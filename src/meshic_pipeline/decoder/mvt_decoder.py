from __future__ import annotations

import logging
from typing import Any, Dict, List, Sequence
import re
import json
import os

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
                            print(f"[WARN] Non-integer float for {key}: {value} in feature: {properties}")
                            logging.warning(f"Non-integer float for {key}: {value} in feature: {properties}")
                            cast_properties[key] = None
                    elif isinstance(value, str):
                        try:
                            fval = float(value)
                            if fval.is_integer():
                                cast_properties[key] = int(fval)
                            else:
                                print(f"[WARN] Non-integer string for {key}: '{value}' in feature: {properties}")
                                logging.warning(f"Non-integer string for {key}: '{value}' in feature: {properties}")
                                cast_properties[key] = None
                        except Exception:
                            print(f"[WARN] Unparseable string for {key}: '{value}' in feature: {properties}")
                            logging.warning(f"Unparseable string for {key}: '{value}' in feature: {properties}")
                            cast_properties[key] = None
                    else:
                        print(f"[WARN] Unexpected type for {key}: {type(value)} value: {value} in feature: {properties}")
                        logging.warning(f"Unexpected type for {key}: {type(value)} value: {value} in feature: {properties}")
                        cast_properties[key] = None
                elif key in self.STRING_ID_FIELDS:
                    # Ensure string ID fields are strings
                    cast_properties[key] = str(value)
                else:
                    # Keep other fields as-is
                    cast_properties[key] = value
            except Exception as e:
                print(f"[ERROR] Exception casting {key}: {value} in feature: {properties} -- {e}")
                logging.error(f"Exception casting {key}: {value} in feature: {properties} -- {e}")
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
            
        decoded_tile = mapbox_vector_tile.decode(tile_data)
        output_layers: Dict[str, List[Dict[str, Any]]] = {}

        # Get the extent from the first available layer (it's typically consistent)
        first_layer = next(iter(decoded_tile.values()), None)
        if not first_layer:
            return {}
        
        extent = first_layer.get("extent", 4096)
        coord_transformer = self._create_transform_function(z, x, y, extent)

        for layer_name, layer_content in decoded_tile.items():
            if layers and layer_name not in layers:
                continue
            
            features_out = []
            for feature in layer_content.get("features", []):
                try:
                    # Create the initial Shapely geometry from raw tile coords
                    geom: BaseGeometry = shape(feature["geometry"])
                    
                    if geom.is_empty:
                        continue

                    # Apply the combined scale + project transformation in one step.
                    # This is significantly faster than multiple transforms.
                    projected_geom = transform(coord_transformer, geom)

                    if not projected_geom.is_empty:
                        # Cast properties to expected types for consistency
                        properties = self._cast_property_types(feature["properties"])
                        # Convert camelCase property keys to snake_case to match DB schema
                        properties = {
                            re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower(): value
                            for key, value in properties.items()
                        }
                        features_out.append({"geometry": projected_geom, **properties})

                except Exception as e:
                    # Skip features with invalid geometries or properties
                    logger.warning(f"Skipping feature in layer {layer_name}: {e}")
                    continue
            
            if features_out:
                output_layers[layer_name] = features_out
        
        # At the end, if any quarantined features, write to file
        if self.quarantined_features:
            quarantine_path = os.path.join(os.getcwd(), 'quarantined_features.jsonl')
            with open(quarantine_path, 'a', encoding='utf-8') as f:
                for q in self.quarantined_features:
                    f.write(json.dumps(q, ensure_ascii=False) + '\n')
            print(f"Quarantined {len(self.quarantined_features)} problematic features to {quarantine_path}")
            logging.warning(f"Quarantined {len(self.quarantined_features)} problematic features to {quarantine_path}")
            self.quarantined_features.clear()
        
        return output_layers

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

 
