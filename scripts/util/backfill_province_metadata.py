#!/usr/bin/env python3
"""
Backfill missing province metadata (tile_server_url, bounding boxes, geometry) using existing tile_urls and parcels.

Usage:
    uv run python scripts/util/backfill_province_metadata.py [--province-id 21012] [--dry-run]

By default it repairs every province with missing tile_server_url or bbox columns.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import mercantile
from sqlalchemy import text

from suhail_pipeline.persistence.db import get_db_engine
from suhail_pipeline.config import settings


SLUG_REGEX = re.compile(r"https?://[^/]+/maps/([^/]+)/")


@dataclass
class TileSlugBounds:
    slug: str
    zoom_level: int
    min_x: int
    max_x: int
    min_y: int
    max_y: int

    @property
    def lonlat_bounds(self) -> Tuple[float, float, float, float]:
        """Return (min_lon, min_lat, max_lon, max_lat) based on z15 tiles."""
        z = self.zoom_level
        corners = [
            mercantile.bounds(self.min_x, self.min_y, z),
            mercantile.bounds(self.min_x, self.max_y, z),
            mercantile.bounds(self.max_x, self.min_y, z),
            mercantile.bounds(self.max_x, self.max_y, z),
        ]
        min_lon = min(b.west for b in corners)
        min_lat = min(b.south for b in corners)
        max_lon = max(b.east for b in corners)
        max_lat = max(b.north for b in corners)
        return min_lon, min_lat, max_lon, max_lat


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill missing province metadata using existing tile_urls/parcels."
    )
    parser.add_argument(
        "--province-id",
        type=int,
        required=True,
        help="Repair this province_id (required).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without writing to DB.",
    )
    return parser.parse_args()


def fetch_slug_bounds(conn) -> Dict[str, TileSlugBounds]:
    rows = conn.execute(
        text(
            """
            WITH tiles AS (
                SELECT
                    REGEXP_REPLACE(url, '^https?://[^/]+/maps/([^/]+)/.*$', '\\1') AS slug,
                    zoom_level,
                    x,
                    y
                FROM tile_urls
                WHERE zoom_level = 15
            )
            SELECT slug,
                   zoom_level,
                   MIN(x) AS min_x,
                   MAX(x) AS max_x,
                   MIN(y) AS min_y,
                   MAX(y) AS max_y
            FROM tiles
            GROUP BY slug, zoom_level
            """
        )
    )
    slug_map: Dict[str, TileSlugBounds] = {}
    for row in rows:
        slug_map[row.slug] = TileSlugBounds(
            slug=row.slug,
            zoom_level=row.zoom_level,
            min_x=row.min_x,
            max_x=row.max_x,
            min_y=row.min_y,
            max_y=row.max_y,
        )
    return slug_map


def fetch_province_parcel_bounds(conn) -> Dict[int, Tuple[float, float, float, float]]:
    rows = conn.execute(
        text(
            """
            SELECT province_id,
                   ST_XMin(extent)::float AS min_lon,
                   ST_YMin(extent)::float AS min_lat,
                   ST_XMax(extent)::float AS max_lon,
                   ST_YMax(extent)::float AS max_lat
            FROM (
                SELECT province_id, ST_Extent(geometry) AS extent
                FROM parcels
                GROUP BY province_id
            ) q
            """
        )
    )
    bounds = {}
    for row in rows:
        if None in (row.min_lon, row.min_lat, row.max_lon, row.max_lat):
            continue
        bounds[row.province_id] = (row.min_lon, row.min_lat, row.max_lon, row.max_lat)
    return bounds


def choose_slug_for_province(
    province_bbox: Optional[Tuple[float, float, float, float]],
    slug_bounds: Dict[str, TileSlugBounds],
) -> Optional[TileSlugBounds]:
    if not slug_bounds:
        return None
    if province_bbox is None:
        # Fall back to slug with largest coverage (arbitrary but deterministic)
        return max(slug_bounds.values(), key=lambda sb: (sb.max_x - sb.min_x) * (sb.max_y - sb.min_y))

    p_min_lon, p_min_lat, p_max_lon, p_max_lat = province_bbox
    best_slug = None
    best_area = 0.0
    for slug, sb in slug_bounds.items():
        s_min_lon, s_min_lat, s_max_lon, s_max_lat = sb.lonlat_bounds
        inter_min_lon = max(p_min_lon, s_min_lon)
        inter_min_lat = max(p_min_lat, s_min_lat)
        inter_max_lon = min(p_max_lon, s_max_lon)
        inter_max_lat = min(p_max_lat, s_max_lat)
        if inter_min_lon >= inter_max_lon or inter_min_lat >= inter_max_lat:
            continue
        inter_area = (inter_max_lon - inter_min_lon) * (inter_max_lat - inter_min_lat)
        if inter_area > best_area:
            best_area = inter_area
            best_slug = sb
    return best_slug


def main() -> None:
    args = parse_args()
    engine = get_db_engine(str(settings.database_url))
    with engine.begin() as conn:
        # Provinces needing updates
        province_rows = conn.execute(
            text(
                """
                SELECT province_id, province_name, province_name_ar, tile_server_url,
                       bbox_sw_lon, bbox_sw_lat, bbox_ne_lon, bbox_ne_lat
                FROM provinces
                WHERE province_id = :pid
                """
            ),
            {"pid": args.province_id},
        ).fetchall()

        if not province_rows:
            print(f"Province {args.province_id} not found.")
            return

        # Filter to only rows that actually need repair
        province_rows = [
            row for row in province_rows
            if any(
                col is None
                for col in (row.tile_server_url, row.bbox_sw_lon, row.bbox_sw_lat, row.bbox_ne_lon, row.bbox_ne_lat)
            )
        ]

        if not province_rows:
            print(f"Province {args.province_id} already has tile_server_url/bbox populated. Nothing to do.")
            return

        slug_bounds = fetch_slug_bounds(conn)
        parcel_bounds = fetch_province_parcel_bounds(conn)

        updates = []
        for row in province_rows:
            pid = row.province_id
            pname = row.province_name
            pname_ar = row.province_name_ar

            province_bbox = parcel_bounds.get(pid)
            slug = None
            # Prefer existing slug from tile_server_url
            if row.tile_server_url:
                match = SLUG_REGEX.search(row.tile_server_url)
                if match:
                    slug_key = match.group(1)
                    slug = slug_bounds.get(slug_key)
                    if not slug and slug_key:
                        # Add entry from slug_key if present in tile_urls
                        slug = slug_bounds.get(slug_key)
            if not slug:
                slug = choose_slug_for_province(province_bbox, slug_bounds)
            if not slug:
                print(f"[WARN] Province {pid} ({pname}) - unable to infer tile slug; skipping.")
                continue

            slug_bbox = slug.lonlat_bounds
            if province_bbox is None:
                province_bbox = slug_bbox

            min_lon, min_lat, max_lon, max_lat = province_bbox
            centroid_lon = (min_lon + max_lon) / 2.0
            centroid_lat = (min_lat + max_lat) / 2.0

            tile_url_template = f"https://tiles.suhail.ai/maps/{slug.slug}/{{z}}/{{x}}/{{y}}.vector.pbf"

            updates.append(
                {
                    "province_id": pid,
                    "tile_url": tile_url_template,
                    "min_lon": min_lon,
                    "min_lat": min_lat,
                    "max_lon": max_lon,
                    "max_lat": max_lat,
                    "centroid_lon": centroid_lon,
                    "centroid_lat": centroid_lat,
                }
            )
            print(
                f"[INFO] Province {pid} ({pname}) -> slug '{slug.slug}' "
                f"bbox=({min_lon:.6f}, {min_lat:.6f}, {max_lon:.6f}, {max_lat:.6f})"
            )

        if not updates:
            print("No updates were generated.")
            return

        if args.dry_run:
            print("Dry run enabled; no changes written.")
            return

        for upd in updates:
            conn.execute(
                text(
                    """
                    UPDATE provinces
                    SET tile_server_url = :tile_url,
                        bbox_sw_lon = :min_lon,
                        bbox_sw_lat = :min_lat,
                        bbox_ne_lon = :max_lon,
                        bbox_ne_lat = :max_lat,
                        centroid_lon = :centroid_lon,
                        centroid_lat = :centroid_lat,
                        geometry = ST_SetSRID(ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat), 4326)
                    WHERE province_id = :province_id
                    """
                ),
                upd,
            )

        print(f"Updated {len(updates)} province rows.")


if __name__ == "__main__":
    main()
