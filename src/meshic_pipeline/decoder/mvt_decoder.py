from __future__ import annotations

import logging
from typing import Any, Dict, List, Sequence
import re
import json
import os
from google.protobuf.message import DecodeError

import mapbox_vector_tile
import mercantile
import geopandas as gpd
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from pyproj import Transformer
from shapely.ops import transform
from ..config import ARABIC_COLUMN_MAP

logger = logging.getLogger(__name__)


class MVTDecoder:
    """A highly optimized decoder for Mapbox Vector Tiles with data type validation."""

    # Define expected integer ID fields for type casting
    INTEGER_ID_FIELDS = {
        'parcel_id', 'zoning_id', 'subdivision_id', 'neighborhood_id', 
        'province_id', 'region_id'
    }
    
    # Define expected string ID fields (parcel_objectid comes as string but gets converted downstream)
    STRING_ID_FIELDS = {
        'parcel_objectid', 'rule_id', 'station_code', 'grid_id', 'strip_id'
    }

    def __init__(self, target_crs="EPSG:4326"):
        """
        Initializes the decoder and creates a reusable transformer.
        
        Args:
            target_crs (str): The target CRS for the output geometries.
        """
        self.target_crs = target_crs
        # Create a single, reusable transformer for all operations.
        # This is much more efficient than creating one per tile.
        self.transformer = Transformer.from_crs(
            "EPSG:3857", self.target_crs, always_xy=True
        ).transform
        self.quarantined_features = []

    def _cast_property_types(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        cast_properties = {}
        for key, value in properties.items():
            try:
                if key in self.INTEGER_ID_FIELDS:
                    # Accept int, float (if .is_integer()), or string (parseable as int/float and .is_integer())
                    if isinstance(value, int):
                        cast_properties[key] = value
                    elif isinstance(value, float):
                        if value.is_integer():
                            cast_properties[key] = int(value)
                        else:
                            logger.warning(
                                "Non-integer float for %s: %s in feature: %s",
                                key,
                                value,
                                properties,
                            )
                            cast_properties[key] = None
                    elif isinstance(value, str):
                        try:
                            fval = float(value)
                            if fval.is_integer():
                                cast_properties[key] = int(fval)
                            else:
                                logger.warning(
                                    "Non-integer string for %s: '%s' in feature: %s",
                                    key,
                                    value,
                                    properties,
                                )
                                cast_properties[key] = None
                        except Exception:
                            logger.warning(
                                "Unparseable string for %s: '%s' in feature: %s",
                                key,
                                value,
                                properties,
                            )
                            cast_properties[key] = None
                    else:
                        logger.warning(
                            "Unexpected type for %s: %s value: %s in feature: %s",
                            key,
                            type(value),
                            value,
                            properties,
                        )
                        cast_properties[key] = None
                elif key in self.STRING_ID_FIELDS:
                    # Ensure string ID fields are strings
                    cast_properties[key] = str(value)
                else:
                    # Keep other fields as-is
                    cast_properties[key] = value
            except Exception as e:
                logger.error(
                    "Exception casting %s: %s in feature: %s -- %s",
                    key,
                    value,
                    properties,
                    e,
                )
                cast_properties[key] = None
        return cast_properties

    def _create_transform_function(
        self, z: int, x: int, y: int, extent: int
    ) -> callable:
        """
        Creates a single function that scales tile-local coordinates
        directly to the target CRS (e.g., EPSG:4326).
        This avoids intermediate transformations and is highly efficient.
        """
        mx_min, my_min, mx_max, my_max = mercantile.xy_bounds(x, y, z)
        scale_x = (mx_max - mx_min) / extent
        scale_y = (my_max - my_min) / extent

        def transform_coords(lon, lat, z=None):
            # Scale from tile-local coords to Web Mercator (EPSG:3857)
            mercator_x = mx_min + lon * scale_x
            mercator_y = my_min + lat * scale_y
            # Project from Web Mercator to the target CRS
            return self.transformer(mercator_x, mercator_y)

        return transform_coords

    def decode_bytes(
        self, tile_data: bytes, z: int, x: int, y: int, layers: List[str] | None = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Decodes a single MVT tile into a dictionary of features with geometries
        projected to the target CRS and properties with validated types.
        """
        if not tile_data:
            return {}
        # Quick content check for HTML or empty
        if tile_data[:1] == b"<" or tile_data[:15].lower().startswith(b"<!doctype html"):
            logger.error(f"Tile {z}/{x}/{y} appears to be HTML or empty, skipping decode.")
            return {}
        try:
            decoded = mapbox_vector_tile.decode(tile_data)
            print(f"Decoded tile {z}/{x}/{y}: {decoded}")
            # --- PATCH: Normalize province_id 101004 to 101000 (Riyadh) ---
            for layer, features in decoded.items():
                for feat in features:
                    props = feat.get('properties', {})
                    if 'province_id' in props and props['province_id'] == 101004:
                        props['province_id'] = 101000
            return decoded
        except DecodeError as e:
            logger.error(f"DecodeError for tile {z}/{x}/{y}: {e}")
            self._quarantine_tile(tile_data, z, x, y, error=str(e))
            return {}
        except Exception as e:
            logger.error(f"Unexpected decode error for tile {z}/{x}/{y}: {e}")
            self._quarantine_tile(tile_data, z, x, y, error=str(e))
            return {}

    def decode_to_gdf(
        self, tile_data: bytes, z: int, x: int, y: int, layers: List[str] | None = None
    ) -> Dict[str, gpd.GeoDataFrame]:
        """Decodes tile bytes directly into a dictionary of GeoDataFrames."""
        decoded_layers = self.decode_bytes(tile_data, z, x, y, layers)
        gdfs = {}
        for layer_name, features in decoded_layers.items():
            if features:
                gdfs[layer_name] = gpd.GeoDataFrame(
                    features, geometry="geometry", crs=self.target_crs
                )
        return gdfs

    @staticmethod
    def apply_arabic_column_mapping(gdf):
        """Rename all columns in ``gdf`` according to :data:`ARABIC_COLUMN_MAP`."""
        for src, dst in ARABIC_COLUMN_MAP.items():
            if src in gdf.columns:
                gdf = gdf.rename(columns={src: dst})
        return gdf

    def _quarantine_tile(self, tile_data: bytes, z: int, x: int, y: int, error: str = ""):
        """
        Save the raw tile data and error message to tile_decode_failures for inspection.
        """
        quarantine_dir = "tile_decode_failures"
        os.makedirs(quarantine_dir, exist_ok=True)
        tile_path = os.path.join(quarantine_dir, f"tile_{z}_{x}_{y}.bin")
        with open(tile_path, "wb") as f:
            f.write(tile_data)
        if error:
            error_path = os.path.join(quarantine_dir, f"tile_{z}_{x}_{y}.error.txt")
            with open(error_path, "w") as ef:
                ef.write(error)

 
