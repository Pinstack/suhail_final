-- migrations/001_create_meshic_schema.sql

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Reference tables for regions
CREATE TABLE provinces (
    province_id BIGINT PRIMARY KEY,
    name TEXT
);

CREATE TABLE municipalities (
    municipality_id BIGINT PRIMARY KEY,
    name TEXT,
    province_id BIGINT REFERENCES provinces(province_id)
);

-- Neighborhoods with geometry and centroid
CREATE TABLE neighborhoods (
    neighborhood_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    geometry Geometry(MULTIPOLYGON,4326),
    province_id BIGINT REFERENCES provinces(province_id),
    municipality_id BIGINT REFERENCES municipalities(municipality_id)
);

-- Centroids for neighborhoods
CREATE TABLE neighborhoods_centroids (
    neighborhood_id BIGINT PRIMARY KEY REFERENCES neighborhoods(neighborhood_id),
    geometry Geometry(MULTIPOINT,4326)
);

-- Land use groups lookup
CREATE TABLE land_use_groups (
    landuse_agroup TEXT PRIMARY KEY,
    description TEXT
);

-- Zoning rules lookup with metadata
CREATE TABLE zoning_rules (
    rule_id TEXT PRIMARY KEY,
    zoning_group TEXT,
    zoning_color TEXT,
    description TEXT,
    max_building_coefficient TEXT,
    max_building_height TEXT,
    max_parcel_coverage TEXT,
    main_streets_setback TEXT,
    secondary_streets_setback TEXT,
    side_rear_setback TEXT,
    province_id BIGINT REFERENCES provinces(province_id)
);

-- Subdivisions lookup
CREATE TABLE subdivisions (
    subdivision_id BIGINT PRIMARY KEY,
    subdivision_no TEXT UNIQUE,
    name TEXT,
    province_id BIGINT REFERENCES provinces(province_id)
);

-- Staging table for raw CDC loads
CREATE TABLE parcels_staging (
    parcel_objectid BIGINT,
    parcel_id BIGINT,
    parcel_no TEXT,
    price_of_meter DOUBLE PRECISION,
    transaction_price DOUBLE PRECISION,
    shape_area DOUBLE PRECISION,
    landuse_agroup TEXT,
    landuse_adetailed TEXT,
    subdivision_no TEXT,
    subdivision_id BIGINT,
    province_id BIGINT,
    municipality_aname TEXT,
    neighborhood_id BIGINT,
    rule_id TEXT,
    zoning_id BIGINT,
    zoning_color TEXT,
    ingested_at TIMESTAMPTZ DEFAULT now(),
    geometry Geometry(MULTIPOLYGON,4326)
);

-- Canonical parcels table
CREATE TABLE parcels (
    parcel_objectid BIGINT PRIMARY KEY,
    parcel_id BIGINT,
    parcel_no TEXT,
    price_of_meter DOUBLE PRECISION,
    transaction_price DOUBLE PRECISION,
    shape_area DOUBLE PRECISION,
    landuse_agroup TEXT REFERENCES land_use_groups(landuse_agroup),
    landuse_adetailed TEXT,
    subdivision_no TEXT,
    subdivision_id BIGINT REFERENCES subdivisions(subdivision_id),
    province_id BIGINT REFERENCES provinces(province_id),
    municipality_aname TEXT,
    neighborhood_id BIGINT REFERENCES neighborhoods(neighborhood_id),
    rule_id TEXT REFERENCES zoning_rules(rule_id),
    zoning_id BIGINT,
    zoning_color TEXT,
    raw_json JSONB,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    enriched_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    geometry_hash TEXT NOT NULL,
    geometry Geometry(MULTIPOLYGON,4326)
);

-- Centroids table for fast point lookups
CREATE TABLE parcels_centroids (
    parcel_objectid BIGINT PRIMARY KEY REFERENCES parcels(parcel_objectid),
    geometry Geometry(POINT,4326),
    transactions_count INTEGER
);

-- Transactions with audit blob
CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY,
    parcel_objectid BIGINT NOT NULL REFERENCES parcels(parcel_objectid),
    transaction_price DOUBLE PRECISION,
    price_of_meter DOUBLE PRECISION,
    transaction_date TIMESTAMPTZ,
    area DOUBLE PRECISION,
    raw_data JSONB NOT NULL
);

-- Price history per parcel
CREATE TABLE parcel_price_history (
    metric_id BIGSERIAL PRIMARY KEY,
    parcel_objectid BIGINT NOT NULL REFERENCES parcels(parcel_objectid),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    average_price_of_meter DOUBLE PRECISION,
    UNIQUE(parcel_objectid, year, month)
);

-- Price history per neighborhood
CREATE TABLE neighborhood_price_history (
    metric_id BIGSERIAL PRIMARY KEY,
    neighborhood_id BIGINT NOT NULL REFERENCES neighborhoods(neighborhood_id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    average_price_of_meter DOUBLE PRECISION,
    UNIQUE(neighborhood_id, year, month)
);

-- Indexes for performance
CREATE INDEX idx_parcels_geom ON parcels USING GIST(geometry);
CREATE INDEX idx_parcels_centroids_geom ON parcels_centroids USING GIST(geometry);
CREATE INDEX idx_neighborhoods_geom ON neighborhoods USING GIST(geometry);
CREATE INDEX idx_neighborhoods_centroids_geom ON neighborhoods_centroids USING GIST(geometry);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_parcel ON transactions(parcel_objectid);
CREATE INDEX idx_pph_date ON parcel_price_history(year, month);
CREATE INDEX idx_nph_date ON neighborhood_price_history(year, month);
CREATE INDEX idx_parcels_neighborhood ON parcels(neighborhood_id);
CREATE INDEX idx_parcels_province ON parcels(province_id); 