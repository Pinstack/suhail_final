import requests
import logging
import sys
from sqlalchemy import create_engine, text
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Database connection string (read from environment or default)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/meshic')

def fetch_provinces():
    url = 'https://api2.suhail.ai/regions'
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()['data']
    provinces = []
    for region in data:
        tile_server_url = region.get('mapStyleUrl', '')
        bbox = region.get('restrictBoundaryBox', {})
        bbox_sw = bbox.get('southwest', {})
        bbox_ne = bbox.get('northeast', {})
        for prov in region.get('provinces', []):
            centroid = prov.get('centroid', {})
            provinces.append({
                'province_id': prov['id'],
                'province_name': prov.get('name_en') or prov.get('name') or '',
                'province_name_ar': prov.get('name') or '',
                'centroid_lon': centroid.get('x'),
                'centroid_lat': centroid.get('y'),
                'tile_server_url': tile_server_url,
                'bbox_sw_lon': bbox_sw.get('x'),
                'bbox_sw_lat': bbox_sw.get('y'),
                'bbox_ne_lon': bbox_ne.get('x'),
                'bbox_ne_lat': bbox_ne.get('y'),
            })
    return provinces

def upsert_provinces(engine, provinces):
    with engine.begin() as conn:
        # Add columns if missing
        column_defs = [
            ('province_name_ar', 'VARCHAR'),
            ('centroid_lon', 'DOUBLE PRECISION'),
            ('centroid_lat', 'DOUBLE PRECISION'),
            ('tile_server_url', 'VARCHAR'),
            ('bbox_sw_lon', 'DOUBLE PRECISION'),
            ('bbox_sw_lat', 'DOUBLE PRECISION'),
            ('bbox_ne_lon', 'DOUBLE PRECISION'),
            ('bbox_ne_lat', 'DOUBLE PRECISION'),
        ]
        for col, coltype in column_defs:
            conn.execute(text(f'''
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='provinces' AND column_name='{col}'
                    ) THEN
                        ALTER TABLE provinces ADD COLUMN {col} {coltype};
                    END IF;
                END$$;
            '''))
        for prov in provinces:
            conn.execute(text('''
                INSERT INTO provinces (
                    province_id, province_name, province_name_ar, centroid_lon, centroid_lat, tile_server_url,
                    bbox_sw_lon, bbox_sw_lat, bbox_ne_lon, bbox_ne_lat
                )
                VALUES (
                    :province_id, :province_name, :province_name_ar, :centroid_lon, :centroid_lat, :tile_server_url,
                    :bbox_sw_lon, :bbox_sw_lat, :bbox_ne_lon, :bbox_ne_lat
                )
                ON CONFLICT (province_id) DO UPDATE SET
                    province_name = EXCLUDED.province_name,
                    province_name_ar = EXCLUDED.province_name_ar,
                    centroid_lon = EXCLUDED.centroid_lon,
                    centroid_lat = EXCLUDED.centroid_lat,
                    tile_server_url = EXCLUDED.tile_server_url,
                    bbox_sw_lon = EXCLUDED.bbox_sw_lon,
                    bbox_sw_lat = EXCLUDED.bbox_sw_lat,
                    bbox_ne_lon = EXCLUDED.bbox_ne_lon,
                    bbox_ne_lat = EXCLUDED.bbox_ne_lat;
            '''), prov)
        logging.info(f"Upserted {len(provinces)} provinces.")

def main():
    try:
        provinces = fetch_provinces()
        if not provinces:
            logging.error("No provinces found in API response.")
            sys.exit(1)
        engine = create_engine(DATABASE_URL)
        upsert_provinces(engine, provinces)
        logging.info("Province sync complete.")
    except Exception as e:
        logging.error(f"Province sync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 