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
    geometry public.geometry(Geometry,4326),
    color text,
    type text,
    busroute text,
    origin text,
    originar text
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
-- Name: municipalities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.municipalities (
    municipality_id bigint NOT NULL,
    municipality_name character varying,
    province_id bigint,
    geometry public.geometry(MultiPolygon,4326)
);


--
-- Name: municipalities_municipality_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.municipalities_municipality_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: municipalities_municipality_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.municipalities_municipality_id_seq OWNED BY public.municipalities.municipality_id;


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
-- Name: provinces; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provinces (
    province_id bigint NOT NULL,
    province_name character varying,
    geometry public.geometry(MultiPolygon,4326),
    province_name_ar character varying
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
-- Name: riyadh_bus_stations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.riyadh_bus_stations (
    station_code character varying NOT NULL,
    geometry public.geometry(Point,4326),
    station_name character varying,
    route character varying
);


--
-- Name: streets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.streets (
    street_id bigint NOT NULL,
    geometry public.geometry(MultiLineString,4326)
);


--
-- Name: streets_street_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.streets_street_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: streets_street_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.streets_street_id_seq OWNED BY public.streets.street_id;


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
-- Name: municipalities municipality_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.municipalities ALTER COLUMN municipality_id SET DEFAULT nextval('public.municipalities_municipality_id_seq'::regclass);


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
-- Name: provinces province_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provinces ALTER COLUMN province_id SET DEFAULT nextval('public.provinces_province_id_seq'::regclass);


--
-- Name: streets street_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streets ALTER COLUMN street_id SET DEFAULT nextval('public.streets_street_id_seq'::regclass);


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
-- Name: municipalities municipalities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.municipalities
    ADD CONSTRAINT municipalities_pkey PRIMARY KEY (municipality_id);


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
-- Name: riyadh_bus_stations riyadh_bus_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.riyadh_bus_stations
    ADD CONSTRAINT riyadh_bus_stations_pkey PRIMARY KEY (station_code);


--
-- Name: streets streets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.streets
    ADD CONSTRAINT streets_pkey PRIMARY KEY (street_id);


--
-- Name: subdivisions subdivisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subdivisions
    ADD CONSTRAINT subdivisions_pkey PRIMARY KEY (subdivision_id);


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
-- Name: idx_municipalities_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_municipalities_geometry ON public.municipalities USING gist (geometry);


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
-- Name: idx_streets_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_streets_geometry ON public.streets USING gist (geometry);


--
-- Name: idx_subdivisions_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_subdivisions_geometry ON public.subdivisions USING gist (geometry);


--
-- Name: uq_metro_stations_station_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_metro_stations_station_code ON public.metro_stations USING btree (station_code) WHERE (station_code IS NOT NULL);


--
-- Name: uq_parcels_centroids_parcel_no; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_parcels_centroids_parcel_no ON public.parcels_centroids USING btree (parcel_no) WHERE (parcel_no IS NOT NULL);


--
-- Name: uq_qi_population_metrics_grid_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_qi_population_metrics_grid_id ON public.qi_population_metrics USING btree (grid_id) WHERE (grid_id IS NOT NULL);


--
-- Name: uq_qi_stripes_strip_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_qi_stripes_strip_id ON public.qi_stripes USING btree (strip_id) WHERE (strip_id IS NOT NULL);


--
-- Name: uq_riyadh_bus_stations_station_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_riyadh_bus_stations_station_code ON public.riyadh_bus_stations USING btree (station_code) WHERE (station_code IS NOT NULL);


--
-- Name: building_rules building_rules_parcel_objectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.building_rules
    ADD CONSTRAINT building_rules_parcel_objectid_fkey FOREIGN KEY (parcel_objectid) REFERENCES public.parcels(parcel_objectid);


--
-- Name: municipalities municipalities_province_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.municipalities
    ADD CONSTRAINT municipalities_province_id_fkey FOREIGN KEY (province_id) REFERENCES public.provinces(province_id);


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

