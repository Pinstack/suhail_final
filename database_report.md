# 1. Database Structure Overview
Found 1 schemas: public

## Schema: `public`

### Table: `public.alembic_version`
|    | column_name   | data_type         | nullability   | pk                  | check   |
|---:|:--------------|:------------------|:--------------|:--------------------|:--------|
|  0 | version_num   | character varying | NOT NULL      | alembic_version_pkc |         |

### Table: `public.building_rules`
|    | column_name               | data_type         | nullability   | pk              | check   |
|---:|:--------------------------|:------------------|:--------------|:----------------|:--------|
|  0 | parcel_objectid           | bigint            | NOT NULL      | _parcel_rule_uc |         |
|  1 | building_rule_id          | character varying | NOT NULL      | _parcel_rule_uc |         |
|  2 | zoning_id                 | integer           | NULL          |                 |         |
|  3 | zoning_color              | character varying | NULL          |                 |         |
|  4 | zoning_group              | character varying | NULL          |                 |         |
|  5 | landuse                   | character varying | NULL          |                 |         |
|  6 | description               | character varying | NULL          |                 |         |
|  7 | name                      | character varying | NULL          |                 |         |
|  8 | coloring                  | character varying | NULL          |                 |         |
|  9 | coloring_description      | character varying | NULL          |                 |         |
| 10 | max_building_coefficient  | character varying | NULL          |                 |         |
| 11 | max_building_height       | character varying | NULL          |                 |         |
| 12 | max_parcel_coverage       | character varying | NULL          |                 |         |
| 13 | max_rule_depth            | character varying | NULL          |                 |         |
| 14 | main_streets_setback      | character varying | NULL          |                 |         |
| 15 | secondary_streets_setback | character varying | NULL          |                 |         |
| 16 | side_rear_setback         | character varying | NULL          |                 |         |
| 17 | raw_data                  | json              | NULL          |                 |         |

### Table: `public.bus_lines`
|    | column_name   | data_type    | nullability   | pk   | check   |
|---:|:--------------|:-------------|:--------------|:-----|:--------|
|  0 | busroute      | text         | NULL          |      |         |
|  1 | geometry      | USER-DEFINED | NULL          |      |         |

### Table: `public.dimensions`
|    | column_name     | data_type    | nullability   | pk   | check   |
|---:|:----------------|:-------------|:--------------|:-----|:--------|
|  0 | parcel_objectid | bigint       | NULL          |      |         |
|  1 | geometry        | USER-DEFINED | NULL          |      |         |

### Table: `public.geography_columns`
|    | column_name        | data_type   | nullability   | pk   | check   |
|---:|:-------------------|:------------|:--------------|:-----|:--------|
|  0 | f_table_catalog    | name        | NULL          |      |         |
|  1 | f_table_schema     | name        | NULL          |      |         |
|  2 | f_table_name       | name        | NULL          |      |         |
|  3 | f_geography_column | name        | NULL          |      |         |
|  4 | coord_dimension    | integer     | NULL          |      |         |
|  5 | srid               | integer     | NULL          |      |         |
|  6 | type               | text        | NULL          |      |         |

### Table: `public.geometry_columns`
|    | column_name       | data_type         | nullability   | pk   | check   |
|---:|:------------------|:------------------|:--------------|:-----|:--------|
|  0 | f_table_catalog   | character varying | NULL          |      |         |
|  1 | f_table_schema    | name              | NULL          |      |         |
|  2 | f_table_name      | name              | NULL          |      |         |
|  3 | f_geometry_column | name              | NULL          |      |         |
|  4 | coord_dimension   | integer           | NULL          |      |         |
|  5 | srid              | integer           | NULL          |      |         |
|  6 | type              | character varying | NULL          |      |         |

### Table: `public.land_use_groups`
|    | column_name   | data_type         | nullability   | pk                   | check   |
|---:|:--------------|:------------------|:--------------|:---------------------|:--------|
|  0 | landuse_group | character varying | NOT NULL      | land_use_groups_pkey |         |
|  1 | description   | character varying | NULL          |                      |         |

### Table: `public.metro_stations`
|    | column_name   | data_type    | nullability   | pk   | check   |
|---:|:--------------|:-------------|:--------------|:-----|:--------|
|  0 | station_code  | text         | NULL          |      |         |
|  1 | geometry      | USER-DEFINED | NULL          |      |         |

### Table: `public.municipalities`
|    | column_name       | data_type         | nullability   | pk                  | check   |
|---:|:------------------|:------------------|:--------------|:--------------------|:--------|
|  0 | municipality_id   | bigint            | NOT NULL      | municipalities_pkey |         |
|  1 | municipality_name | character varying | NULL          |                     |         |
|  2 | province_id       | bigint            | NULL          |                     |         |
|  3 | geometry          | USER-DEFINED      | NULL          |                     |         |

### Table: `public.neighborhoods`
|    | column_name       | data_type         | nullability   | pk                 | check   |
|---:|:------------------|:------------------|:--------------|:-------------------|:--------|
|  0 | neighborhood_id   | bigint            | NOT NULL      | neighborhoods_pkey |         |
|  1 | geometry          | USER-DEFINED      | NULL          |                    |         |
|  2 | neighborhood_name | character varying | NULL          |                    |         |
|  3 | region_id         | bigint            | NULL          |                    |         |
|  4 | province_id       | bigint            | NULL          |                    |         |
|  5 | price_of_meter    | double precision  | NULL          |                    |         |
|  6 | shape_area        | double precision  | NULL          |                    |         |
|  7 | transaction_price | double precision  | NULL          |                    |         |
|  8 | zoning_id         | bigint            | NULL          |                    |         |
|  9 | zoning_color      | character varying | NULL          |                    |         |
| 10 | geometry_hash     | character varying | NULL          |                    |         |

### Table: `public.parcel_price_metrics`
|    | column_name            | data_type         | nullability   | pk                        | check   |
|---:|:-----------------------|:------------------|:--------------|:--------------------------|:--------|
|  0 | metric_id              | integer           | NOT NULL      | parcel_price_metrics_pkey |         |
|  1 | parcel_objectid        | bigint            | NULL          |                           |         |
|  2 | month                  | integer           | NOT NULL      |                           |         |
|  3 | year                   | integer           | NOT NULL      |                           |         |
|  4 | metrics_type           | character varying | NOT NULL      |                           |         |
|  5 | average_price_of_meter | double precision  | NULL          |                           |         |
|  6 | neighborhood_id        | bigint            | NULL          |                           |         |

### Table: `public.parcels`
|    | column_name        | data_type                   | nullability   | pk           | check   |
|---:|:-------------------|:----------------------------|:--------------|:-------------|:--------|
|  0 | parcel_objectid    | bigint                      | NOT NULL      | parcels_pkey |         |
|  1 | geometry           | USER-DEFINED                | NOT NULL      |              |         |
|  2 | landuseagroup      | character varying           | NULL          |              |         |
|  3 | landuseadetailed   | character varying           | NULL          |              |         |
|  4 | subdivision_no     | character varying           | NULL          |              |         |
|  5 | transaction_price  | double precision            | NULL          |              |         |
|  6 | zoning_id          | bigint                      | NULL          |              |         |
|  7 | neighborhood_id    | bigint                      | NULL          |              |         |
|  8 | block_no           | character varying           | NULL          |              |         |
|  9 | neighborhaname     | character varying           | NULL          |              |         |
| 10 | subdivision_id     | bigint                      | NULL          |              |         |
| 11 | price_of_meter     | double precision            | NULL          |              |         |
| 12 | shape_area         | double precision            | NULL          |              |         |
| 13 | zoning_color       | character varying           | NULL          |              |         |
| 14 | ruleid             | character varying           | NULL          |              |         |
| 15 | province_id        | bigint                      | NULL          |              |         |
| 16 | municipality_aname | character varying           | NULL          |              |         |
| 17 | parcel_id          | bigint                      | NULL          |              |         |
| 18 | parcel_no          | character varying           | NULL          |              |         |
| 19 | created_at         | timestamp without time zone | NOT NULL      |              |         |
| 20 | updated_at         | timestamp without time zone | NOT NULL      |              |         |
| 21 | is_active          | boolean                     | NOT NULL      |              |         |
| 22 | geometry_hash      | character varying           | NULL          |              |         |
| 23 | enriched_at        | timestamp with time zone    | NULL          |              |         |

### Table: `public.parcels_base`
|    | column_name   | data_type         | nullability   | pk                | check   |
|---:|:--------------|:------------------|:--------------|:------------------|:--------|
|  0 | parcel_id     | character varying | NOT NULL      | parcels_base_pkey |         |
|  1 | geometry      | USER-DEFINED      | NULL          |                   |         |

### Table: `public.parcels_centroids`
|    | column_name        | data_type    | nullability   | pk   | check   |
|---:|:-------------------|:-------------|:--------------|:-----|:--------|
|  0 | parcel_id          | bigint       | NULL          |      |         |
|  1 | geometry           | USER-DEFINED | NULL          |      |         |
|  2 | parcel_no          | text         | NULL          |      |         |
|  3 | neighborhood_id    | bigint       | NULL          |      |         |
|  4 | province_id        | bigint       | NULL          |      |         |
|  5 | transactions_count | text         | NULL          |      |         |
|  6 | transaction_date   | text         | NULL          |      |         |
|  7 | transaction_price  | text         | NULL          |      |         |
|  8 | price_of_meter     | text         | NULL          |      |         |

### Table: `public.provinces`
|    | column_name   | data_type         | nullability   | pk             | check   |
|---:|:--------------|:------------------|:--------------|:---------------|:--------|
|  0 | province_id   | bigint            | NOT NULL      | provinces_pkey |         |
|  1 | province_name | character varying | NULL          |                |         |
|  2 | geometry      | USER-DEFINED      | NULL          |                |         |

### Table: `public.qi_population_metrics`
|    | column_name   | data_type    | nullability   | pk   | check   |
|---:|:--------------|:-------------|:--------------|:-----|:--------|
|  0 | grid_id       | text         | NULL          |      |         |
|  1 | geometry      | USER-DEFINED | NULL          |      |         |

### Table: `public.qi_stripes`
|    | column_name   | data_type    | nullability   | pk   | check   |
|---:|:--------------|:-------------|:--------------|:-----|:--------|
|  0 | strip_id      | text         | NULL          |      |         |
|  1 | geometry      | USER-DEFINED | NULL          |      |         |

### Table: `public.riyadh_bus_stations`
|    | column_name   | data_type    | nullability   | pk   | check   |
|---:|:--------------|:-------------|:--------------|:-----|:--------|
|  0 | station_code  | text         | NULL          |      |         |
|  1 | geometry      | USER-DEFINED | NULL          |      |         |

### Table: `public.spatial_ref_sys`
|    | column_name   | data_type         | nullability   | pk                   | check                               |
|---:|:--------------|:------------------|:--------------|:---------------------|:------------------------------------|
|  0 | srid          | integer           | NOT NULL      | spatial_ref_sys_pkey | (((srid > 0) AND (srid <= 998999))) |
|  1 | auth_name     | character varying | NULL          |                      |                                     |
|  2 | auth_srid     | integer           | NULL          |                      |                                     |
|  3 | srtext        | character varying | NULL          |                      |                                     |
|  4 | proj4text     | character varying | NULL          |                      |                                     |

### Table: `public.streets`
|    | column_name   | data_type    | nullability   | pk           | check   |
|---:|:--------------|:-------------|:--------------|:-------------|:--------|
|  0 | street_id     | bigint       | NOT NULL      | streets_pkey |         |
|  1 | geometry      | USER-DEFINED | NULL          |              |         |

### Table: `public.subdivisions`
|    | column_name       | data_type         | nullability   | pk                | check   |
|---:|:------------------|:------------------|:--------------|:------------------|:--------|
|  0 | subdivision_id    | bigint            | NOT NULL      | subdivisions_pkey |         |
|  1 | geometry          | USER-DEFINED      | NULL          |                   |         |
|  2 | subdivision_no    | character varying | NULL          |                   |         |
|  3 | shape_area        | double precision  | NULL          |                   |         |
|  4 | transaction_price | double precision  | NULL          |                   |         |
|  5 | price_of_meter    | double precision  | NULL          |                   |         |
|  6 | zoning_id         | bigint            | NULL          |                   |         |
|  7 | zoning_color      | character varying | NULL          |                   |         |
|  8 | province_id       | bigint            | NULL          |                   |         |

### Table: `public.transactions`
|    | column_name       | data_type                   | nullability   | pk                | check   |
|---:|:------------------|:----------------------------|:--------------|:------------------|:--------|
|  0 | transaction_id    | bigint                      | NOT NULL      | transactions_pkey |         |
|  1 | parcel_objectid   | bigint                      | NULL          |                   |         |
|  2 | transaction_price | double precision            | NULL          |                   |         |
|  3 | price_of_meter    | double precision            | NULL          |                   |         |
|  4 | transaction_date  | timestamp without time zone | NULL          |                   |         |
|  5 | area              | double precision            | NULL          |                   |         |
|  6 | raw_data          | json                        | NULL          |                   |         |

### Table: `public.zoning_rules`
|    | column_name   | data_type         | nullability   | pk                | check   |
|---:|:--------------|:------------------|:--------------|:------------------|:--------|
|  0 | ruleid        | character varying | NOT NULL      | zoning_rules_pkey |         |
|  1 | description   | character varying | NULL          |                   |         |

# 2. Spatial Feature Summary

## Spatial Columns
|    | f_table_schema   | f_table_name          | f_geometry_column   |   srid | type            |
|---:|:-----------------|:----------------------|:--------------------|-------:|:----------------|
|  0 | public           | provinces             | geometry            |   4326 | MULTIPOLYGON    |
|  1 | public           | parcels_base          | geometry            |   4326 | GEOMETRY        |
|  2 | public           | streets               | geometry            |   4326 | MULTILINESTRING |
|  3 | public           | neighborhoods         | geometry            |   4326 | GEOMETRY        |
|  4 | public           | municipalities        | geometry            |   4326 | MULTIPOLYGON    |
|  5 | public           | subdivisions          | geometry            |   4326 | GEOMETRY        |
|  6 | public           | parcels               | geometry            |   4326 | MULTIPOLYGON    |
|  7 | public           | parcels_centroids     | geometry            |   4326 | GEOMETRY        |
|  8 | public           | dimensions            | geometry            |   4326 | GEOMETRY        |
|  9 | public           | bus_lines             | geometry            |   4326 | MULTIPOLYGON    |
| 10 | public           | metro_stations        | geometry            |   4326 | POLYGON         |
| 11 | public           | riyadh_bus_stations   | geometry            |   4326 | GEOMETRY        |
| 12 | public           | qi_population_metrics | geometry            |   4326 | POLYGON         |
| 13 | public           | qi_stripes            | geometry            |   4326 | POLYGON         |

## Spatial Indexes
|    | schemaname   | tablename             | indexname                          | columnname   |
|---:|:-------------|:----------------------|:-----------------------------------|:-------------|
|  0 | public       | bus_lines             | idx_bus_lines_geometry             | geometry     |
|  1 | public       | dimensions            | idx_dimensions_geometry            | geometry     |
|  2 | public       | metro_stations        | idx_metro_stations_geometry        | geometry     |
|  3 | public       | municipalities        | idx_municipalities_geometry        | geometry     |
|  4 | public       | neighborhoods         | idx_neighborhoods_geometry         | geometry     |
|  5 | public       | parcels               | idx_parcels_geometry               | geometry     |
|  6 | public       | parcels_base          | idx_parcels_base_geometry          | geometry     |
|  7 | public       | parcels_centroids     | idx_parcels_centroids_geometry     | geometry     |
|  8 | public       | provinces             | idx_provinces_geometry             | geometry     |
|  9 | public       | qi_population_metrics | idx_qi_population_metrics_geometry | geometry     |
| 10 | public       | qi_stripes            | idx_qi_stripes_geometry            | geometry     |
| 11 | public       | riyadh_bus_stations   | idx_riyadh_bus_stations_geometry   | geometry     |
| 12 | public       | streets               | idx_streets_geometry               | geometry     |
| 13 | public       | subdivisions          | idx_subdivisions_geometry          | geometry     |

## Table Relationships (Foreign Keys)
|    | table_schema   | table_name           | column_name     | foreign_table_schema   | foreign_table_name   | foreign_column_name   |
|---:|:---------------|:---------------------|:----------------|:-----------------------|:---------------------|:----------------------|
|  0 | public         | neighborhoods        | province_id     | public                 | provinces            | province_id           |
|  1 | public         | municipalities       | province_id     | public                 | provinces            | province_id           |
|  2 | public         | subdivisions         | province_id     | public                 | provinces            | province_id           |
|  3 | public         | transactions         | parcel_objectid | public                 | parcels              | parcel_objectid       |
|  4 | public         | parcel_price_metrics | parcel_objectid | public                 | parcels              | parcel_objectid       |
|  5 | public         | parcel_price_metrics | neighborhood_id | public                 | neighborhoods        | neighborhood_id       |
|  6 | public         | building_rules       | parcel_objectid | public                 | parcels              | parcel_objectid       |
|  7 | public         | parcels              | neighborhood_id | public                 | neighborhoods        | neighborhood_id       |
|  8 | public         | parcels              | province_id     | public                 | provinces            | province_id           |
|  9 | public         | parcels              | ruleid          | public                 | zoning_rules         | ruleid                |
| 10 | public         | parcels              | landuseagroup   | public                 | land_use_groups      | landuse_group         |

# JSON Column Analysis

## Analyzing JSON in `public.building_rules`

### Column: `raw_data`
Found common keys that could potentially be expanded:
```
- maxRuleDepth
- maxBuildingCoefficient
- landuse
- description
- coloringDescription
- mainStreetsSetback
- id
- zoningGroup
- zoningColor
- coloring
- zoningId
- maxBuildingHeight
- secondaryStreetsSetback
- sideRearSetback
- maxParcelCoverage
- name
```

## Analyzing JSON in `public.transactions`

### Column: `raw_data`
Found common keys that could potentially be expanded:
```
- propertyNumber
- centroidY
- parcelObjectId
- totalArea
- projectName
- neighborhoodId
- transactionNumber
- parcelId
- isLowValueTransaction
- parcelNo
- centroidX
- propertyType
- noOfProperties
- landUseaDetailed
- priceOfMeter
- zoningId
- geometry
- transactionDate
- landUsageGroup
- subdivisionNo
```

# 3. Analytical & Visualization Potential

- **Proximity Analysis:** Calculate distances between spatial features (e.g., properties to parks, schools, transit stops).
- **Clustering:** Identify hotspots of real estate activity or areas with similar characteristics using algorithms like DBSCAN or K-means.
- **Overlay Analysis:** Combine layers to find intersections (e.g., properties within a specific zoning district or flood plain).
- **Network Analysis:** Analyze street networks to determine optimal routes, travel times, and accessibility.
- **Heatmaps:** Visualize the density of points, such as property sales, crime incidents, or business locations.
- **Choropleth Maps:** Map aggregated data by geographic area (e.g., average property price by neighborhood, population density by census tract).
- **Interactive Web Maps:** Create dynamic maps with tools like Leaflet, Mapbox, or Kepler.gl to allow users to explore the data, filter results, and view details on demand.
        

# 4. Real Estate Use Cases

- **Site Selection:** Identify optimal locations for new developments (residential, commercial) based on demographics, accessibility, zoning, and market trends.
- **Market Analysis:** Understand pricing trends, absorption rates, and competitive landscapes by analyzing historical sales, listings, and neighborhood characteristics.
- **Risk Assessment:** Evaluate property exposure to environmental hazards (flooding, pollution), proximity to undesirable features (e.g., industrial zones), or infrastructure deficits.
- **Infrastructure Access:** Assess the value added by proximity to key amenities like public transit, major highways, schools, parks, and retail centers.
- **Beneficiaries:**
    - **Real Estate Brokers/Agents:** To advise clients on property values, market conditions, and investment opportunities.
    - **Developers:** To find and evaluate development sites and understand market demand.
    - **City Planners & Urbanists:** To analyze urban growth patterns, manage infrastructure, and develop zoning policies.
    - **Investors:** To identify undervalued assets and growth markets.
        

# 5. Recommendations

- **Standardize SRIDs:** Ensure all spatial layers use a consistent and appropriate Spatial Reference Identifier (SRID) for accurate spatial analysis. If multiple SRIDs are present, reproject data to a single standard (e.g., WGS 84 - SRID 4326 for global data, or a local projected system for regional analysis).
- **Improve Naming Conventions:** Adopt a clear and consistent naming convention for schemas, tables, and columns to improve readability and maintainability.
- **Add Missing Indexes:** Beyond spatial indexes, add B-tree indexes to foreign key columns and other frequently queried columns to improve join performance and query speed.
- **Create Materialized Views:** For complex queries or aggregations that are frequently accessed, create materialized views to pre-compute and store the results, leading to faster dashboards and analytics. Example: A view that joins property data with neighborhood names, average prices, and proximity scores to amenities.
- **Data Dictionary:** Create and maintain a data dictionary that describes each table, column, and its meaning, source, and update frequency.
        