-- migrations/002_populate_reference_data.sql

-- Populate provinces
INSERT INTO provinces (province_id)
SELECT DISTINCT province_id
FROM parcels
WHERE province_id IS NOT NULL
ON CONFLICT (province_id) DO NOTHING;

-- Populate land use groups
INSERT INTO land_use_groups (landuse_agroup)
SELECT DISTINCT landuse_agroup
FROM parcels
WHERE landuse_agroup IS NOT NULL
ON CONFLICT (landuse_agroup) DO NOTHING;

-- Populate zoning rules (minimal)
INSERT INTO zoning_rules (rule_id, zoning_color)
SELECT DISTINCT rule_id, zoning_color
FROM parcels
WHERE rule_id IS NOT NULL
ON CONFLICT (rule_id) DO UPDATE SET zoning_color = EXCLUDED.zoning_color;

-- Populate subdivisions details from parcels
INSERT INTO subdivisions (subdivision_id, subdivision_no, name, province_id)
SELECT DISTINCT subdivision_id, subdivision_no, subdivision_no, province_id
FROM parcels
WHERE subdivision_id IS NOT NULL
ON CONFLICT (subdivision_id) DO UPDATE SET subdivision_no = EXCLUDED.subdivision_no, name = EXCLUDED.name, province_id = EXCLUDED.province_id;

-- Re-enable FK constraints on parcels
ALTER TABLE parcels ADD CONSTRAINT parcels_subdivision_id_fkey FOREIGN KEY (subdivision_id) REFERENCES subdivisions (subdivision_id);
ALTER TABLE parcels ADD CONSTRAINT parcels_province_id_fkey FOREIGN KEY (province_id) REFERENCES provinces (province_id);
ALTER TABLE parcels ADD CONSTRAINT parcels_neighborhood_id_fkey FOREIGN KEY (neighborhood_id) REFERENCES neighborhoods (neighborhood_id);
ALTER TABLE parcels ADD CONSTRAINT parcels_landuse_agroup_fkey FOREIGN KEY (landuse_agroup) REFERENCES land_use_groups (landuse_agroup);
ALTER TABLE parcels ADD CONSTRAINT parcels_rule_id_fkey FOREIGN KEY (rule_id) REFERENCES zoning_rules (rule_id); 