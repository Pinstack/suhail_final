-- migrations/003_populate_municipalities.sql

-- Ensure unique constraint on municipalities.name for FK enforcement
ALTER TABLE municipalities
ADD CONSTRAINT municipalities_name_key UNIQUE (name);

-- Populate municipalities from parcels data with surrogate IDs
WITH distinct_muni AS (
    SELECT DISTINCT municipality_aname AS name, province_id
    FROM parcels
    WHERE municipality_aname IS NOT NULL AND municipality_aname <> ''
)
INSERT INTO municipalities (municipality_id, name, province_id)
SELECT
    ROW_NUMBER() OVER (ORDER BY name) AS municipality_id,
    name,
    province_id
FROM distinct_muni
ON CONFLICT (name) DO NOTHING;

-- Add foreign key constraint from parcels to municipalities by name
ALTER TABLE parcels
ADD CONSTRAINT parcels_municipality_aname_fkey
    FOREIGN KEY (municipality_aname)
    REFERENCES municipalities(name); 