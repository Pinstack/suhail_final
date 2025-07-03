import gzip
import mapbox_vector_tile

with gzip.open("test_tile.pbf", "rb") as f:
    tile_data = f.read()

decoded_tile = mapbox_vector_tile.decode(tile_data)

print("Decoded Tile Structure:")
for layer_name, layer_content in decoded_tile.items():
    print(f"  Layer: {layer_name}")
    print(f"    Extent: {layer_content.get('extent')}")
    print(f"    Number of features: {len(layer_content.get('features'))}")
    if layer_name == "dimensions":
        for i, feature in enumerate(layer_content.get('features')):
            print(f"      Feature {i}: {feature.get('properties')}")
