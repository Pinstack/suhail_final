#!/usr/bin/env python3
"""
Extended tile data validation script.
Scans all .pbf tiles in a directory, decodes features, and checks for:
- Non-integer or invalid ID fields
- Missing required fields
- Out-of-range values (e.g., negative IDs, negative areas)
- Writes problematic features to quarantined_features.jsonl
"""
import os
import sys
import glob
import argparse
import json
from meshic_pipeline.decoder.mvt_decoder import MVTDecoder
from shapely.geometry import mapping

ID_FIELDS = {
    'parcel_id', 'zoning_id', 'subdivision_id', 'neighborhood_id', 
    'province_id', 'municipality_id', 'region_id', 'parcel_objectid'
}
REQUIRED_FIELDS = ID_FIELDS | {'geometry'}

QUARANTINE_FILE = 'quarantined_features.jsonl'

def is_valid_int(val):
    try:
        if isinstance(val, int):
            return True
        if isinstance(val, float):
            return val.is_integer()
        if isinstance(val, str):
            f = float(val)
            return f.is_integer()
    except Exception:
        return False
    return False

def is_out_of_range(field, val):
    if field in ID_FIELDS and val is not None:
        try:
            ival = int(val)
            if ival < 0:
                return True
        except Exception:
            return True
    if field == 'shape_area' and val is not None:
        try:
            fval = float(val)
            if fval < 0:
                return True
        except Exception:
            return True
    return False

def feature_to_serializable(feat):
    feat_copy = dict(feat)
    if 'geometry' in feat_copy and feat_copy['geometry'] is not None:
        try:
            feat_copy['geometry'] = mapping(feat_copy['geometry'])
        except Exception:
            feat_copy['geometry'] = str(feat_copy['geometry'])
    return feat_copy

def main(tile_dir):
    decoder = MVTDecoder()
    quarantine_path = os.path.join(os.getcwd(), QUARANTINE_FILE)
    issues_found = 0
    quarantined = []
    tiles = glob.glob(os.path.join(tile_dir, '*.pbf'))
    print(f"Scanning {len(tiles)} tiles in {tile_dir}...")
    for tile in tiles:
        basename = os.path.basename(tile)
        try:
            zxy = basename.replace('.pbf', '').split('_')
            if len(zxy) == 3:
                z, x, y = map(int, zxy)
            else:
                z, x, y = None, None, None
        except Exception:
            z, x, y = None, None, None
        with open(tile, 'rb') as f:
            data = f.read()
        decoded = decoder.decode_bytes(data, z or 0, x or 0, y or 0)
        for layer, features in decoded.items():
            for feat in features:
                feature_issues = []
                # Check for missing required fields
                for req in REQUIRED_FIELDS:
                    if req not in feat or feat[req] is None:
                        feature_issues.append(f"Missing required field: {req}")
                # Check ID fields for non-integer
                for idf in ID_FIELDS:
                    if idf in feat and feat[idf] is not None and not is_valid_int(feat[idf]):
                        feature_issues.append(f"Non-integer value for {idf}: {feat[idf]} ({type(feat[idf]).__name__})")
                # Check for out-of-range values
                for field, val in feat.items():
                    if is_out_of_range(field, val):
                        feature_issues.append(f"Out-of-range value for {field}: {val}")
                if feature_issues:
                    issues_found += 1
                    issue_record = {
                        'tile': {'z': z, 'x': x, 'y': y},
                        'layer': layer,
                        'feature': feature_to_serializable(feat),
                        'issues': feature_issues
                    }
                    quarantined.append(issue_record)
                    print(f"[ISSUE] Tile {z},{x},{y} Layer {layer}: {feature_issues}\n  Feature: {json.dumps(feature_to_serializable(feat), ensure_ascii=False)}")
    if quarantined:
        print(f"Quarantined {len(quarantined)} problematic features (not written to file)")
    print(f"Validation complete. Issues found: {issues_found}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate tile data for ID, required, and range issues.")
    parser.add_argument('--tile-dir', type=str, default='temp_tiles/', help='Directory containing .pbf tiles')
    args = parser.parse_args()
    main(args.tile_dir) 