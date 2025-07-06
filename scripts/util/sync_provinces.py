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
        for prov in region.get('provinces', []):
            provinces.append({
                'province_id': prov['id'],
                'province_name': prov.get('name_en') or prov.get('name') or '',
                'province_name_ar': prov.get('name') or '',
            })
    return provinces

def upsert_provinces(engine, provinces):
    with engine.begin() as conn:
        # Add province_name_ar column if missing
        conn.execute(text('''
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='provinces' AND column_name='province_name_ar'
                ) THEN
                    ALTER TABLE provinces ADD COLUMN province_name_ar VARCHAR;
                END IF;
            END$$;
        '''))
        for prov in provinces:
            conn.execute(text('''
                INSERT INTO provinces (province_id, province_name, province_name_ar)
                VALUES (:province_id, :province_name, :province_name_ar)
                ON CONFLICT (province_id) DO UPDATE SET
                    province_name = EXCLUDED.province_name,
                    province_name_ar = EXCLUDED.province_name_ar;
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