--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Homebrew)
-- Dumped by pg_dump version 14.18 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.transactions DROP CONSTRAINT IF EXISTS transactions_parcel_objectid_fkey;
ALTER TABLE IF EXISTS ONLY public.subdivisions DROP CONSTRAINT IF EXISTS subdivisions_province_id_fkey;
ALTER TABLE IF EXISTS ONLY public.provinces DROP CONSTRAINT IF EXISTS provinces_region_id_fkey;
ALTER TABLE IF EXISTS ONLY public.parcels DROP CONSTRAINT IF EXISTS parcels_ruleid_fkey;
ALTER TABLE IF EXISTS ONLY public.parcels DROP CONSTRAINT IF EXISTS parcels_province_id_fkey;
ALTER TABLE IF EXISTS ONLY public.parcels DROP CONSTRAINT IF EXISTS parcels_neighborhood_id_fkey;
ALTER TABLE IF EXISTS ONLY public.parcel_price_metrics DROP CONSTRAINT IF EXISTS parcel_price_metrics_parcel_objectid_fkey;
ALTER TABLE IF EXISTS ONLY public.parcel_price_metrics DROP CONSTRAINT IF EXISTS parcel_price_metrics_neighborhood_id_fkey;
ALTER TABLE IF EXISTS ONLY public.neighborhoods DROP CONSTRAINT IF EXISTS neighborhoods_province_id_fkey;
ALTER TABLE IF EXISTS ONLY public.building_rules DROP CONSTRAINT IF EXISTS building_rules_parcel_objectid_fkey;
DROP INDEX IF EXISTS public.temp_neighborhoods_geometry_idx;
DROP INDEX IF EXISTS public.idx_temp_subdivisions_geometry;
DROP INDEX IF EXISTS public.idx_temp_riyadh_bus_stations_geometry;
DROP INDEX IF EXISTS public.idx_temp_qi_stripes_geometry;
DROP INDEX IF EXISTS public.idx_temp_qi_population_metrics_geometry;
DROP INDEX IF EXISTS public.idx_temp_parcels_geometry;
DROP INDEX IF EXISTS public.idx_temp_metro_stations_geometry;
DROP INDEX IF EXISTS public.idx_temp_metro_lines_geometry;
DROP INDEX IF EXISTS public.idx_temp_bus_lines_geometry;
DROP INDEX IF EXISTS public.idx_subdivisions_geometry;
DROP INDEX IF EXISTS public.idx_riyadh_bus_stations_geometry;
DROP INDEX IF EXISTS public.idx_qi_stripes_geometry;
DROP INDEX IF EXISTS public.idx_qi_population_metrics_geometry;
DROP INDEX IF EXISTS public.idx_provinces_geometry;
DROP INDEX IF EXISTS public.idx_parcels_geometry;
DROP INDEX IF EXISTS public.idx_parcels_enriched_geometry;
DROP INDEX IF EXISTS public.idx_parcels_centroids_geometry;
DROP INDEX IF EXISTS public.idx_parcels_base_geometry;
DROP INDEX IF EXISTS public.idx_neighborhoods_geometry;
DROP INDEX IF EXISTS public.idx_neighborhoods_centroids_geometry;
DROP INDEX IF EXISTS public.idx_metro_stations_geometry;
DROP INDEX IF EXISTS public.idx_metro_lines_geometry;
DROP INDEX IF EXISTS public.idx_bus_lines_geometry;
ALTER TABLE IF EXISTS ONLY public.zoning_rules DROP CONSTRAINT IF EXISTS zoning_rules_pkey;
ALTER TABLE IF EXISTS ONLY public.transactions DROP CONSTRAINT IF EXISTS transactions_pkey;
ALTER TABLE IF EXISTS ONLY public.temp_neighborhoods DROP CONSTRAINT IF EXISTS temp_neighborhoods_pkey;
ALTER TABLE IF EXISTS ONLY public.subdivisions DROP CONSTRAINT IF EXISTS subdivisions_pkey;
ALTER TABLE IF EXISTS ONLY public.riyadh_bus_stations DROP CONSTRAINT IF EXISTS riyadh_bus_stations_pkey;
ALTER TABLE IF EXISTS ONLY public.regions DROP CONSTRAINT IF EXISTS regions_pkey;
ALTER TABLE IF EXISTS ONLY public.quarantined_features DROP CONSTRAINT IF EXISTS quarantined_features_pkey;
ALTER TABLE IF EXISTS ONLY public.qi_stripes DROP CONSTRAINT IF EXISTS qi_stripes_pkey;
ALTER TABLE IF EXISTS ONLY public.qi_population_metrics DROP CONSTRAINT IF EXISTS qi_population_metrics_pkey;
ALTER TABLE IF EXISTS ONLY public.provinces DROP CONSTRAINT IF EXISTS provinces_pkey;
ALTER TABLE IF EXISTS ONLY public.province_id_mapping DROP CONSTRAINT IF EXISTS province_id_mapping_pkey;
ALTER TABLE IF EXISTS ONLY public.parcels DROP CONSTRAINT IF EXISTS parcels_pkey;
ALTER TABLE IF EXISTS ONLY public.parcels_centroids DROP CONSTRAINT IF EXISTS parcels_centroids_pkey;
ALTER TABLE IF EXISTS ONLY public.parcels_base DROP CONSTRAINT IF EXISTS parcels_base_pkey;
ALTER TABLE IF EXISTS ONLY public.parcel_price_metrics DROP CONSTRAINT IF EXISTS parcel_price_metrics_pkey;
ALTER TABLE IF EXISTS ONLY public.neighborhoods DROP CONSTRAINT IF EXISTS neighborhoods_pkey;
ALTER TABLE IF EXISTS ONLY public.metro_stations DROP CONSTRAINT IF EXISTS metro_stations_pkey;
ALTER TABLE IF EXISTS ONLY public.land_use_groups DROP CONSTRAINT IF EXISTS land_use_groups_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
ALTER TABLE IF EXISTS ONLY public.transactions DROP CONSTRAINT IF EXISTS _transaction_parcel_uc;
ALTER TABLE IF EXISTS ONLY public.building_rules DROP CONSTRAINT IF EXISTS _parcel_rule_uc;
ALTER TABLE IF EXISTS ONLY public.parcel_price_metrics DROP CONSTRAINT IF EXISTS _parcel_metric_uc;
ALTER TABLE IF EXISTS public.transactions ALTER COLUMN transaction_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.subdivisions ALTER COLUMN subdivision_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.regions ALTER COLUMN region_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.quarantined_features ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.provinces ALTER COLUMN province_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.province_id_mapping ALTER COLUMN source_province_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.parcels ALTER COLUMN parcel_objectid DROP DEFAULT;
ALTER TABLE IF EXISTS public.parcel_price_metrics ALTER COLUMN metric_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.neighborhoods ALTER COLUMN neighborhood_id DROP DEFAULT;
DROP TABLE IF EXISTS public.zoning_rules;
DROP SEQUENCE IF EXISTS public.transactions_transaction_id_seq;
DROP TABLE IF EXISTS public.transactions;
DROP TABLE IF EXISTS public.temp_subdivisions;
DROP TABLE IF EXISTS public.temp_riyadh_bus_stations;
DROP TABLE IF EXISTS public.temp_qi_stripes;
DROP TABLE IF EXISTS public.temp_qi_population_metrics;
DROP TABLE IF EXISTS public.temp_parcels;
DROP TABLE IF EXISTS public.temp_neighborhoods;
DROP TABLE IF EXISTS public.temp_metro_stations;
DROP TABLE IF EXISTS public.temp_metro_lines;
DROP TABLE IF EXISTS public.temp_decoded_neighborhoods_538a8f59;
DROP TABLE IF EXISTS public.temp_bus_lines;
DROP SEQUENCE IF EXISTS public.subdivisions_subdivision_id_seq;
DROP TABLE IF EXISTS public.subdivisions;
DROP TABLE IF EXISTS public.riyadh_bus_stations;
DROP SEQUENCE IF EXISTS public.regions_region_id_seq;
DROP TABLE IF EXISTS public.regions;
DROP SEQUENCE IF EXISTS public.quarantined_features_id_seq;
DROP TABLE IF EXISTS public.quarantined_features;
DROP TABLE IF EXISTS public.qi_stripes;
DROP TABLE IF EXISTS public.qi_population_metrics;
DROP SEQUENCE IF EXISTS public.provinces_province_id_seq;
DROP TABLE IF EXISTS public.provinces;
DROP SEQUENCE IF EXISTS public.province_id_mapping_source_province_id_seq;
DROP TABLE IF EXISTS public.province_id_mapping;
DROP SEQUENCE IF EXISTS public.parcels_parcel_objectid_seq;
DROP TABLE IF EXISTS public.parcels_enriched;
DROP TABLE IF EXISTS public.parcels_centroids;
DROP TABLE IF EXISTS public.parcels_base;
DROP TABLE IF EXISTS public.parcels;
DROP SEQUENCE IF EXISTS public.parcel_price_metrics_metric_id_seq;
DROP TABLE IF EXISTS public.parcel_price_metrics;
DROP SEQUENCE IF EXISTS public.neighborhoods_neighborhood_id_seq;
DROP TABLE IF EXISTS public.neighborhoods_centroids;
DROP TABLE IF EXISTS public.neighborhoods;
DROP TABLE IF EXISTS public.metro_stations;
DROP TABLE IF EXISTS public.metro_lines;
DROP TABLE IF EXISTS public.land_use_groups;
DROP TABLE IF EXISTS public.bus_lines;
DROP TABLE IF EXISTS public.building_rules;
DROP TABLE IF EXISTS public.alembic_version;
DROP EXTENSION IF EXISTS postgis;
--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: building_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.building_rules (
    parcel_objectid bigint NOT NULL,
    building_rule_id character varying NOT NULL,
    zoning_id integer,
    zoning_color character varying,
    zoning_group character varying,
    landuse character varying,
    description character varying,
    name character varying,
    coloring character varying,
    coloring_description character varying,
    max_building_coefficient character varying,
    max_building_height character varying,
    max_parcel_coverage character varying,
    max_rule_depth character varying,
    main_streets_setback character varying,
    secondary_streets_setback character varying,
    side_rear_setback character varying,
    raw_data json
);


--
-- Name: bus_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bus_lines (
    geometry public.geometry(Geometry,4326)
);


--
-- Name: land_use_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.land_use_groups (
    landuse_group character varying NOT NULL,
    description character varying
);


--
-- Name: metro_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metro_lines (
    geometry public.geometry(LineString,4326),
    track_name text,
    track_color text,
    track_length double precision
);


--
-- Name: metro_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metro_stations (
    station_code character varying NOT NULL,
    geometry public.geometry(Point,4326),
    station_name character varying,
    line character varying
);


--
-- Name: neighborhoods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.neighborhoods (
    neighborhood_id bigint NOT NULL,
    geometry public.geometry(Geometry,4326),
    neighborhood_name character varying,
    neighborhood_ar character varying,
    region_id bigint,
    province_id bigint,
    price_of_meter double precision,
    shape_area double precision,
    transaction_price double precision,
    zoning_id bigint,
    zoning_color character varying,
    geometry_hash character varying
);


--
-- Name: neighborhoods_centroids; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.neighborhoods_centroids (
    geometry public.geometry(Point,4326),
    neighborh_aname text,
    province_id bigint
);


--
-- Name: neighborhoods_neighborhood_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.neighborhoods_neighborhood_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: neighborhoods_neighborhood_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.neighborhoods_neighborhood_id_seq OWNED BY public.neighborhoods.neighborhood_id;


--
-- Name: parcel_price_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parcel_price_metrics (
    metric_id integer NOT NULL,
    parcel_objectid bigint,
    month integer NOT NULL,
    year integer NOT NULL,
    metrics_type character varying NOT NULL,
    average_price_of_meter double precision,
    neighborhood_id bigint
);


--
-- Name: parcel_price_metrics_metric_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parcel_price_metrics_metric_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parcel_price_metrics_metric_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parcel_price_metrics_metric_id_seq OWNED BY public.parcel_price_metrics.metric_id;


--
-- Name: parcels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parcels (
    parcel_objectid bigint NOT NULL,
    geometry public.geometry(MultiPolygon,4326) NOT NULL,
    landuseagroup character varying,
    landuseadetailed character varying,
    subdivision_no character varying,
    transaction_price double precision,
    zoning_id bigint,
    neighborhood_id bigint,
    block_no character varying,
    neighborhood_ar character varying,
    subdivision_id bigint,
    price_of_meter double precision,
    shape_area double precision,
    zoning_color character varying,
    ruleid character varying,
    province_id bigint,
    municipality_ar character varying,
    parcel_id bigint,
    parcel_no character varying,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    geometry_hash character varying,
    enriched_at timestamp with time zone,
    region_id bigint
);


--
-- Name: parcels_base; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parcels_base (
    parcel_id character varying NOT NULL,
    geometry public.geometry(Geometry,4326)
);


--
-- Name: parcels_centroids; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parcels_centroids (
    parcel_no character varying NOT NULL,
    geometry public.geometry(Point,4326),
    transaction_date timestamp without time zone,
    transaction_price double precision,
    price_of_meter double precision
);


--
-- Name: parcels_enriched; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parcels_enriched (
    geometry public.geometry(Geometry,4326),
    block_no text,
    landuseagroup text,
    parcel_no text,
    subdivision_id double precision,
    zoning_id double precision,
    landuseadetailed text,
    price_of_meter double precision,
    ruleid text,
    province_id bigint,
    parcel_id bigint,
    subdivision_no text,
    transaction_price double precision,
    parcel_objectid bigint,
    neighborhood_id bigint,
    shape_area double precision,
    zoning_color text,
    index_right double precision,
    region_id double precision
);


--
-- Name: parcels_parcel_objectid_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.parcels_parcel_objectid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: parcels_parcel_objectid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.parcels_parcel_objectid_seq OWNED BY public.parcels.parcel_objectid;


--
-- Name: province_id_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.province_id_mapping (
    source_province_id bigint NOT NULL,
    canonical_province_id bigint NOT NULL,
    mapping_reason character varying(128),
    last_seen timestamp with time zone DEFAULT now()
);


--
-- Name: province_id_mapping_source_province_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.province_id_mapping_source_province_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: province_id_mapping_source_province_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.province_id_mapping_source_province_id_seq OWNED BY public.province_id_mapping.source_province_id;


--
-- Name: provinces; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provinces (
    province_id bigint NOT NULL,
    province_name character varying,
    geometry public.geometry(MultiPolygon,4326),
    province_name_ar character varying,
    centroid_lon double precision,
    centroid_lat double precision,
    tile_server_url character varying,
    bbox_sw_lon double precision,
    bbox_sw_lat double precision,
    bbox_ne_lon double precision,
    bbox_ne_lat double precision,
    region_id bigint,
    centroid_x double precision,
    centroid_y double precision
);


--
-- Name: provinces_province_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.provinces_province_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: provinces_province_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.provinces_province_id_seq OWNED BY public.provinces.province_id;


--
-- Name: qi_population_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qi_population_metrics (
    grid_id character varying NOT NULL,
    population integer,
    geometry public.geometry(Polygon,4326)
);


--
-- Name: qi_stripes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.qi_stripes (
    strip_id character varying NOT NULL,
    geometry public.geometry(Polygon,4326),
    value double precision
);


--
-- Name: quarantined_features; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quarantined_features (
    id bigint NOT NULL,
    feature_type character varying(64) NOT NULL,
    feature_id bigint NOT NULL,
    province_id bigint NOT NULL,
    raw_data jsonb NOT NULL,
    reason character varying(128),
    created_at timestamp with time zone DEFAULT now(),
    region_id bigint,
    geometry text,
    properties text,
    quarantined_at timestamp with time zone DEFAULT now()
);


--
-- Name: quarantined_features_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quarantined_features_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quarantined_features_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quarantined_features_id_seq OWNED BY public.quarantined_features.id;


--
-- Name: regions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regions (
    region_id bigint NOT NULL,
    region_key character varying(64),
    region_name character varying(128),
    map_style_url character varying(256),
    map_zoom_level double precision,
    metrics_url character varying(256),
    default_transactions_date_range character varying(32),
    centroid_x double precision,
    centroid_y double precision,
    bbox_sw_x double precision,
    bbox_sw_y double precision,
    bbox_ne_x double precision,
    bbox_ne_y double precision,
    image_url character varying(256)
);


--
-- Name: regions_region_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.regions_region_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: regions_region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.regions_region_id_seq OWNED BY public.regions.region_id;


--
-- Name: riyadh_bus_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.riyadh_bus_stations (
    station_code character varying NOT NULL,
    geometry public.geometry(Point,4326),
    station_name character varying,
    route character varying
);


--
-- Name: subdivisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subdivisions (
    subdivision_id bigint NOT NULL,
    geometry public.geometry(Geometry,4326),
    subdivision_no character varying,
    shape_area double precision,
    transaction_price double precision,
    price_of_meter double precision,
    zoning_id bigint,
    zoning_color character varying,
    province_id bigint
);


--
-- Name: subdivisions_subdivision_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subdivisions_subdivision_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subdivisions_subdivision_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subdivisions_subdivision_id_seq OWNED BY public.subdivisions.subdivision_id;


--
-- Name: temp_bus_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_bus_lines (
    geometry public.geometry(Geometry,4326)
);


--
-- Name: temp_decoded_neighborhoods_538a8f59; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_decoded_neighborhoods_538a8f59 (
    geometry public.geometry(Geometry,4326),
    neighborh_aname text,
    region_id bigint,
    province_id bigint,
    shape_area double precision,
    transaction_price double precision,
    price_of_meter double precision,
    transactions_count text,
    neighborhood_id bigint
);


--
-- Name: temp_metro_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_metro_lines (
    geometry public.geometry(LineString,4326),
    track_name text,
    track_color text,
    track_length double precision
);


--
-- Name: temp_metro_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_metro_stations (
    geometry public.geometry(Point,4326),
    station_code text,
    station_name text
);


--
-- Name: temp_neighborhoods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_neighborhoods (
    neighborhood_id bigint DEFAULT nextval('public.neighborhoods_neighborhood_id_seq'::regclass) NOT NULL,
    geometry public.geometry(Geometry,4326),
    neighborhood_name character varying,
    neighborhood_ar character varying,
    region_id bigint,
    province_id bigint,
    price_of_meter double precision,
    shape_area double precision,
    transaction_price double precision,
    zoning_id bigint,
    zoning_color character varying,
    geometry_hash character varying
);


--
-- Name: temp_parcels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_parcels (
    geometry public.geometry(Geometry,4326),
    block_no text,
    landuseagroup text,
    parcel_no text,
    subdivision_id bigint,
    zoning_id bigint,
    landuseadetailed text,
    price_of_meter double precision,
    ruleid text,
    province_id bigint,
    parcel_id bigint,
    subdivision_no text,
    transaction_price double precision,
    parcel_objectid bigint,
    neighborhood_id bigint,
    shape_area double precision,
    zoning_color text
);


--
-- Name: temp_qi_population_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_qi_population_metrics (
    geometry public.geometry(Polygon,4326),
    grid_id text
);


--
-- Name: temp_qi_stripes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_qi_stripes (
    geometry public.geometry(Polygon,4326),
    strip_id text
);


--
-- Name: temp_riyadh_bus_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_riyadh_bus_stations (
    geometry public.geometry(Point,4326),
    station_name text,
    station_code text
);


--
-- Name: temp_subdivisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temp_subdivisions (
    geometry public.geometry(Geometry,4326),
    price_of_meter double precision,
    zoning_id bigint,
    zoning_color text,
    province_id bigint,
    subdivision_id bigint,
    subdivision_no text,
    shape_area double precision,
    transaction_price double precision
);


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    transaction_id bigint NOT NULL,
    parcel_objectid bigint,
    transaction_price double precision,
    price_of_meter double precision,
    transaction_date timestamp without time zone,
    area double precision,
    raw_data json
);


--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transactions_transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transactions_transaction_id_seq OWNED BY public.transactions.transaction_id;


--
-- Name: zoning_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zoning_rules (
    ruleid character varying NOT NULL,
    description character varying
);


--
-- Name: neighborhoods neighborhood_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.neighborhoods ALTER COLUMN neighborhood_id SET DEFAULT nextval('public.neighborhoods_neighborhood_id_seq'::regclass);


--
-- Name: parcel_price_metrics metric_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_price_metrics ALTER COLUMN metric_id SET DEFAULT nextval('public.parcel_price_metrics_metric_id_seq'::regclass);


--
-- Name: parcels parcel_objectid; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels ALTER COLUMN parcel_objectid SET DEFAULT nextval('public.parcels_parcel_objectid_seq'::regclass);


--
-- Name: province_id_mapping source_province_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.province_id_mapping ALTER COLUMN source_province_id SET DEFAULT nextval('public.province_id_mapping_source_province_id_seq'::regclass);


--
-- Name: provinces province_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provinces ALTER COLUMN province_id SET DEFAULT nextval('public.provinces_province_id_seq'::regclass);


--
-- Name: quarantined_features id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quarantined_features ALTER COLUMN id SET DEFAULT nextval('public.quarantined_features_id_seq'::regclass);


--
-- Name: regions region_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regions ALTER COLUMN region_id SET DEFAULT nextval('public.regions_region_id_seq'::regclass);


--
-- Name: subdivisions subdivision_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subdivisions ALTER COLUMN subdivision_id SET DEFAULT nextval('public.subdivisions_subdivision_id_seq'::regclass);


--
-- Name: transactions transaction_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions ALTER COLUMN transaction_id SET DEFAULT nextval('public.transactions_transaction_id_seq'::regclass);


--
-- Name: parcel_price_metrics _parcel_metric_uc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_price_metrics
    ADD CONSTRAINT _parcel_metric_uc UNIQUE (parcel_objectid, month, year, metrics_type);


--
-- Name: building_rules _parcel_rule_uc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_rules
    ADD CONSTRAINT _parcel_rule_uc PRIMARY KEY (parcel_objectid, building_rule_id);


--
-- Name: transactions _transaction_parcel_uc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT _transaction_parcel_uc UNIQUE (transaction_id, parcel_objectid);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: land_use_groups land_use_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.land_use_groups
    ADD CONSTRAINT land_use_groups_pkey PRIMARY KEY (landuse_group);


--
-- Name: metro_stations metro_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metro_stations
    ADD CONSTRAINT metro_stations_pkey PRIMARY KEY (station_code);


--
-- Name: neighborhoods neighborhoods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.neighborhoods
    ADD CONSTRAINT neighborhoods_pkey PRIMARY KEY (neighborhood_id);


--
-- Name: parcel_price_metrics parcel_price_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_price_metrics
    ADD CONSTRAINT parcel_price_metrics_pkey PRIMARY KEY (metric_id);


--
-- Name: parcels_base parcels_base_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels_base
    ADD CONSTRAINT parcels_base_pkey PRIMARY KEY (parcel_id);


--
-- Name: parcels_centroids parcels_centroids_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels_centroids
    ADD CONSTRAINT parcels_centroids_pkey PRIMARY KEY (parcel_no);


--
-- Name: parcels parcels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_pkey PRIMARY KEY (parcel_objectid);


--
-- Name: province_id_mapping province_id_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.province_id_mapping
    ADD CONSTRAINT province_id_mapping_pkey PRIMARY KEY (source_province_id);


--
-- Name: provinces provinces_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provinces
    ADD CONSTRAINT provinces_pkey PRIMARY KEY (province_id);


--
-- Name: qi_population_metrics qi_population_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qi_population_metrics
    ADD CONSTRAINT qi_population_metrics_pkey PRIMARY KEY (grid_id);


--
-- Name: qi_stripes qi_stripes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.qi_stripes
    ADD CONSTRAINT qi_stripes_pkey PRIMARY KEY (strip_id);


--
-- Name: quarantined_features quarantined_features_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quarantined_features
    ADD CONSTRAINT quarantined_features_pkey PRIMARY KEY (id);


--
-- Name: regions regions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT regions_pkey PRIMARY KEY (region_id);


--
-- Name: riyadh_bus_stations riyadh_bus_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.riyadh_bus_stations
    ADD CONSTRAINT riyadh_bus_stations_pkey PRIMARY KEY (station_code);


--
-- Name: subdivisions subdivisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subdivisions
    ADD CONSTRAINT subdivisions_pkey PRIMARY KEY (subdivision_id);


--
-- Name: temp_neighborhoods temp_neighborhoods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temp_neighborhoods
    ADD CONSTRAINT temp_neighborhoods_pkey PRIMARY KEY (neighborhood_id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: zoning_rules zoning_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zoning_rules
    ADD CONSTRAINT zoning_rules_pkey PRIMARY KEY (ruleid);


--
-- Name: idx_bus_lines_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bus_lines_geometry ON public.bus_lines USING gist (geometry);


--
-- Name: idx_metro_lines_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metro_lines_geometry ON public.metro_lines USING gist (geometry);


--
-- Name: idx_metro_stations_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_metro_stations_geometry ON public.metro_stations USING gist (geometry);


--
-- Name: idx_neighborhoods_centroids_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_neighborhoods_centroids_geometry ON public.neighborhoods_centroids USING gist (geometry);


--
-- Name: idx_neighborhoods_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_neighborhoods_geometry ON public.neighborhoods USING gist (geometry);


--
-- Name: idx_parcels_base_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcels_base_geometry ON public.parcels_base USING gist (geometry);


--
-- Name: idx_parcels_centroids_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcels_centroids_geometry ON public.parcels_centroids USING gist (geometry);


--
-- Name: idx_parcels_enriched_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcels_enriched_geometry ON public.parcels_enriched USING gist (geometry);


--
-- Name: idx_parcels_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcels_geometry ON public.parcels USING gist (geometry);


--
-- Name: idx_provinces_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_provinces_geometry ON public.provinces USING gist (geometry);


--
-- Name: idx_qi_population_metrics_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qi_population_metrics_geometry ON public.qi_population_metrics USING gist (geometry);


--
-- Name: idx_qi_stripes_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_qi_stripes_geometry ON public.qi_stripes USING gist (geometry);


--
-- Name: idx_riyadh_bus_stations_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_riyadh_bus_stations_geometry ON public.riyadh_bus_stations USING gist (geometry);


--
-- Name: idx_subdivisions_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subdivisions_geometry ON public.subdivisions USING gist (geometry);


--
-- Name: idx_temp_bus_lines_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_bus_lines_geometry ON public.temp_bus_lines USING gist (geometry);


--
-- Name: idx_temp_metro_lines_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_metro_lines_geometry ON public.temp_metro_lines USING gist (geometry);


--
-- Name: idx_temp_metro_stations_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_metro_stations_geometry ON public.temp_metro_stations USING gist (geometry);


--
-- Name: idx_temp_parcels_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_parcels_geometry ON public.temp_parcels USING gist (geometry);


--
-- Name: idx_temp_qi_population_metrics_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_qi_population_metrics_geometry ON public.temp_qi_population_metrics USING gist (geometry);


--
-- Name: idx_temp_qi_stripes_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_qi_stripes_geometry ON public.temp_qi_stripes USING gist (geometry);


--
-- Name: idx_temp_riyadh_bus_stations_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_riyadh_bus_stations_geometry ON public.temp_riyadh_bus_stations USING gist (geometry);


--
-- Name: idx_temp_subdivisions_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temp_subdivisions_geometry ON public.temp_subdivisions USING gist (geometry);


--
-- Name: temp_neighborhoods_geometry_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX temp_neighborhoods_geometry_idx ON public.temp_neighborhoods USING gist (geometry);


--
-- Name: building_rules building_rules_parcel_objectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_rules
    ADD CONSTRAINT building_rules_parcel_objectid_fkey FOREIGN KEY (parcel_objectid) REFERENCES public.parcels(parcel_objectid);


--
-- Name: neighborhoods neighborhoods_province_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.neighborhoods
    ADD CONSTRAINT neighborhoods_province_id_fkey FOREIGN KEY (province_id) REFERENCES public.provinces(province_id);


--
-- Name: parcel_price_metrics parcel_price_metrics_neighborhood_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_price_metrics
    ADD CONSTRAINT parcel_price_metrics_neighborhood_id_fkey FOREIGN KEY (neighborhood_id) REFERENCES public.neighborhoods(neighborhood_id);


--
-- Name: parcel_price_metrics parcel_price_metrics_parcel_objectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_price_metrics
    ADD CONSTRAINT parcel_price_metrics_parcel_objectid_fkey FOREIGN KEY (parcel_objectid) REFERENCES public.parcels(parcel_objectid);


--
-- Name: parcels parcels_neighborhood_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_neighborhood_id_fkey FOREIGN KEY (neighborhood_id) REFERENCES public.neighborhoods(neighborhood_id);


--
-- Name: parcels parcels_province_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_province_id_fkey FOREIGN KEY (province_id) REFERENCES public.provinces(province_id);


--
-- Name: parcels parcels_ruleid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_ruleid_fkey FOREIGN KEY (ruleid) REFERENCES public.zoning_rules(ruleid);


--
-- Name: provinces provinces_region_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provinces
    ADD CONSTRAINT provinces_region_id_fkey FOREIGN KEY (region_id) REFERENCES public.regions(region_id);


--
-- Name: subdivisions subdivisions_province_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subdivisions
    ADD CONSTRAINT subdivisions_province_id_fkey FOREIGN KEY (province_id) REFERENCES public.provinces(province_id);


--
-- Name: transactions transactions_parcel_objectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_parcel_objectid_fkey FOREIGN KEY (parcel_objectid) REFERENCES public.parcels(parcel_objectid);


--
-- PostgreSQL database dump complete
--

