"""
Generates Chapters 04 to 10 for the PostGIS & pgAdmin Urban Spatial Analytics Masterclass.
"""

import json
from pathlib import Path

BASE_DIR = Path("c:/YERBO/Desktop/CODING/Python for Urban Analysis/postgis_masterclass")
BASE_DIR.mkdir(parents=True, exist_ok=True)

def create_notebook(filename, cells):
    notebook_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
            "language_info": {"codemirror_mode": {"name": "ipython", "version": 3}, "file_extension": ".py", "mimetype": "text/x-python", "name": "python", "nbconvert_exporter": "python", "pygments_lexer": "ipython3", "version": "3.10.0"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    with open(BASE_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(notebook_content, f, indent=2)

def md_cell(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip().splitlines(True)}

def code_cell(source):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.strip().splitlines(True)}

# =============================================================================
# CHAPTER 04: STREET NETWORKS & PGROUTING
# =============================================================================
sql_04 = """-- ============================================================================
-- CHAPTER 04: STREET NETWORK TOPOLOGY & PGROUTING GRAPH CREATION
-- ============================================================================
-- Focus: Building Navigable Street Graphs and Directional Orientation in Accra
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS accra_streets CASCADE;
CREATE TABLE accra_streets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    highway VARCHAR(50),
    speed_kph INT DEFAULT 40,
    oneway VARCHAR(10) DEFAULT 'B',
    geom GEOMETRY(LineString, 32630)
);

INSERT INTO accra_streets (name, highway, speed_kph, oneway, geom)
VALUES 
    ('Liberation Road (N4)', 'primary', 70, 'B', ST_GeomFromText('LINESTRING(810000 615000, 812000 618000)', 32630)),
    ('Ring Road Central', 'primary', 60, 'B', ST_GeomFromText('LINESTRING(808000 614000, 810000 615000)', 32630)),
    ('Oxford Street (Osu)', 'tertiary', 30, 'B', ST_GeomFromText('LINESTRING(810000 615000, 810500 613500)', 32630)),
    ('Cantonments Road', 'residential', 30, 'B', ST_GeomFromText('LINESTRING(810500 613500, 811500 614000)', 32630)),
    ('Airport Bypass', 'secondary', 50, 'FT', ST_GeomFromText('LINESTRING(812000 618000, 811500 614000)', 32630));

ALTER TABLE accra_streets ADD COLUMN source INT;
ALTER TABLE accra_streets ADD COLUMN target INT;
ALTER TABLE accra_streets ADD COLUMN cost_len DOUBLE PRECISION;
ALTER TABLE accra_streets ADD COLUMN cost_sec DOUBLE PRECISION;
ALTER TABLE accra_streets ADD COLUMN reverse_cost_sec DOUBLE PRECISION;

UPDATE accra_streets
SET cost_len = ST_Length(geom),
    cost_sec = ST_Length(geom) / (speed_kph * 1000.0 / 3600.0),
    reverse_cost_sec = CASE 
        WHEN oneway = 'FT' THEN -1.0
        ELSE ST_Length(geom) / (speed_kph * 1000.0 / 3600.0)
    END;

SELECT pgr_createTopology('accra_streets', 1.0, 'geom', 'id', 'source', 'target');
SELECT * FROM pgr_analyzeGraph('accra_streets', 1.0, 'geom', 'id', 'source', 'target');

-- Calculate Street Azimuth Headings for Rose Diagram
CREATE OR REPLACE VIEW view_street_azimuths AS
SELECT 
    id, name, highway,
    ROUND((DEGREES(ST_Azimuth(ST_StartPoint(geom), ST_EndPoint(geom)))::NUMERIC % 180), 1) AS orientation_deg,
    ROUND(cost_len::NUMERIC, 1) AS length_m
FROM accra_streets;

SELECT * FROM view_street_azimuths;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT id, name, geom FROM accra_streets
UNION ALL
SELECT id, 'Vertex ' || id::text, the_geom AS geom FROM accra_streets_vertices_pgr;
"""
with open(BASE_DIR / "chapter_04_street_networks_pgrouting.sql", "w", encoding="utf-8") as f:
    f.write(sql_04)

nb_04_cells = [
    md_cell("""# 🛣️ Chapter 04: Street Network Topology & pgRouting Graph Creation
## Constructing Navigable Graphs and Analyzing Orientation Entropies

### 🎯 The Mission: Why We Are Doing This
Spatial lines on a map are not a routing graph until intersections are topologically connected into **nodes** and **edges**. Using `pgrouting`, we convert Accra street centerlines into an intelligent network with travel impedance costs and heading azimuths.

---

### 🔑 Spatial DBA Keywords Decoded

| Keyword / Function | Plain-English Explanation | Production Note |
| :--- | :--- | :--- |
| **`pgr_createTopology`** | Splits lines at intersections, builds integer `source` and `target` IDs, and creates the `_vertices_pgr` table. | Mandatory first step for all routing algorithms. |
| **`pgr_analyzeGraph`** | Automated graph validator detecting dead-ends, gaps, and disconnected islands. | Network quality assurance tool. |
| **`ST_Azimuth(p1, p2)`** | Returns line heading angle in radians from North ($0\text{ rad} = \text{North}$). | Used for street orientation rose charts. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_network = \"\"\"
DROP TABLE IF EXISTS accra_streets CASCADE;
CREATE TABLE accra_streets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    highway VARCHAR(50),
    speed_kph INT DEFAULT 40,
    oneway VARCHAR(10) DEFAULT 'B',
    geom GEOMETRY(LineString, 32630)
);

INSERT INTO accra_streets (name, highway, speed_kph, oneway, geom)
VALUES 
    ('Liberation Road (N4)', 'primary', 70, 'B', ST_GeomFromText('LINESTRING(810000 615000, 812000 618000)', 32630)),
    ('Ring Road Central', 'primary', 60, 'B', ST_GeomFromText('LINESTRING(808000 614000, 810000 615000)', 32630)),
    ('Oxford Street (Osu)', 'tertiary', 30, 'B', ST_GeomFromText('LINESTRING(810000 615000, 810500 613500)', 32630)),
    ('Cantonments Road', 'residential', 30, 'B', ST_GeomFromText('LINESTRING(810500 613500, 811500 614000)', 32630)),
    ('Airport Bypass', 'secondary', 50, 'FT', ST_GeomFromText('LINESTRING(812000 618000, 811500 614000)', 32630));

ALTER TABLE accra_streets ADD COLUMN IF NOT EXISTS source INT;
ALTER TABLE accra_streets ADD COLUMN IF NOT EXISTS target INT;
ALTER TABLE accra_streets ADD COLUMN IF NOT EXISTS cost_len DOUBLE PRECISION;
ALTER TABLE accra_streets ADD COLUMN IF NOT EXISTS cost_sec DOUBLE PRECISION;
ALTER TABLE accra_streets ADD COLUMN IF NOT EXISTS reverse_cost_sec DOUBLE PRECISION;

UPDATE accra_streets
SET cost_len = ST_Length(geom),
    cost_sec = ST_Length(geom) / (speed_kph * 1000.0 / 3600.0),
    reverse_cost_sec = CASE 
        WHEN oneway = 'FT' THEN -1.0
        ELSE ST_Length(geom) / (speed_kph * 1000.0 / 3600.0)
    END;

SELECT pgr_createTopology('accra_streets', 1.0, 'geom', 'id', 'source', 'target');
\"\"\"

execute_sql(sql_network)
print("✅ Road network graph built and topology initialized.")
"""),
    code_cell("""# Inspect Azimuth Headings & Network Edge Attributes
df_azimuth = query_df(\"\"\"
SELECT id, name, highway, ROUND((DEGREES(ST_Azimuth(ST_StartPoint(geom), ST_EndPoint(geom)))::NUMERIC % 180), 1) AS orientation_deg, ROUND(cost_len::NUMERIC, 1) AS length_m, ROUND(cost_sec::NUMERIC, 1) AS travel_time_sec
FROM accra_streets;
\"\"\")

df_azimuth
"""),
    code_cell("""# Interactive Map Preview of Street Network Edges
gdf_streets = query_gdf(\"\"\"
SELECT id, name, highway, speed_kph, geom FROM accra_streets;
\"\"\")

preview_map(gdf_streets, tooltip_cols=[\"name\", \"highway\", \"speed_kph\"])
""")
]
create_notebook("Chapter_04_Street_Networks_pgRouting.ipynb", nb_04_cells)

# =============================================================================
# CHAPTER 05: RIPARIAN BUFFERS & VORONOI
# =============================================================================
sql_05 = """-- ============================================================================
-- CHAPTER 05: RIPARIAN BUFFERS & VORONOI CATCHMENTS
-- ============================================================================
-- Focus: Odaw River Flood Encroachment & Hospital Service Territories in Accra
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS odaw_waterway CASCADE;
CREATE TABLE odaw_waterway (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    geom GEOMETRY(LineString, 32630)
);

INSERT INTO odaw_waterway (name, geom)
VALUES ('Odaw River Main Channel', ST_GeomFromText('LINESTRING(808000 617000, 808500 615500, 809000 613000, 809200 611000)', 32630));

DROP TABLE IF EXISTS odaw_100m_buffer CASCADE;
CREATE TABLE odaw_100m_buffer AS
SELECT 1 AS id, '100m Statutory Riparian Buffer' AS description, ST_Buffer(geom, 100.0) AS geom
FROM odaw_waterway;

CREATE INDEX idx_odaw_buf_geom ON odaw_100m_buffer USING GIST(geom);

DROP TABLE IF EXISTS riparian_zone_buildings CASCADE;
CREATE TABLE riparian_zone_buildings (
    bld_id SERIAL PRIMARY KEY,
    bld_type VARCHAR(50),
    geom GEOMETRY(Polygon, 32630)
);

INSERT INTO riparian_zone_buildings (bld_type, geom)
VALUES 
    ('informal_residential', ST_GeomFromText('POLYGON((808480 615500, 808510 615500, 808510 615520, 808480 615520, 808480 615500))', 32630)),
    ('commercial_store', ST_GeomFromText('POLYGON((808580 615500, 808610 615500, 808610 615520, 808580 615520, 808580 615500))', 32630)),
    ('formal_office', ST_GeomFromText('POLYGON((808700 615500, 808740 615500, 808740 615530, 808700 615530, 808700 615500))', 32630));

-- Quantify Buffer Violation
SELECT 
    b.bld_id, b.bld_type,
    ST_Area(b.geom) AS total_m2,
    ROUND(ST_Area(ST_Intersection(b.geom, buf.geom))::NUMERIC, 1) AS encroached_m2,
    ROUND((ST_Area(ST_Intersection(b.geom, buf.geom)) / ST_Area(b.geom) * 100.0)::NUMERIC, 1) AS pct_encroached
FROM riparian_zone_buildings b
JOIN odaw_100m_buffer buf ON ST_Intersects(b.geom, buf.geom);

-- Construct Hospital Voronoi Catchments
DROP TABLE IF EXISTS hospital_voronoi_zones CASCADE;
CREATE TABLE hospital_voronoi_zones AS
WITH hospital_points AS (
    SELECT ST_Collect(geom_utm30n) AS pts FROM accra_landmarks WHERE category = 'Healthcare' OR name LIKE '%Hospital%' OR name LIKE '%Airport%'
),
study_envelope AS (
    SELECT ST_Buffer(ST_SetSRID(ST_MakePoint(810000, 615000), 32630), 10000.0) AS env
)
SELECT (ST_Dump(ST_VoronoiPolygons(pts, 0.0, env))).geom AS geom
FROM hospital_points, study_envelope;

CREATE INDEX idx_voronoi_geom ON hospital_voronoi_zones USING GIST(geom);

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT 1 AS id, 'Waterway' AS layer, geom FROM odaw_waterway
UNION ALL
SELECT 2 AS id, '100m Buffer' AS layer, geom FROM odaw_100m_buffer
UNION ALL
SELECT 3 AS id, 'Buildings' AS layer, geom FROM riparian_zone_buildings;
"""
with open(BASE_DIR / "chapter_05_riparian_buffers_voronoi.sql", "w", encoding="utf-8") as f:
    f.write(sql_05)

nb_05_cells = [
    md_cell("""# 🎯 Chapter 05: Riparian Buffers, Encroachment & Hospital Voronoi Zones
## Spatial Overlays along the Odaw Basin and Healthcare Catchments

### 🎯 The Mission: Why We Are Doing This
The **Odaw River Basin and Korle Lagoon** suffer from severe flood risk due to building encroachment inside statutory river protection buffers ($100\text{m}$). In this chapter, we use `ST_Buffer` and `ST_Intersection` to identify encroaching structures, and construct **Voronoi / Dirichlet polygons** for hospital service territories.

---

### 🔑 Spatial DBA Keywords Decoded

| Function | Plain-English Explanation | Production Note |
| :--- | :--- | :--- |
| **`ST_Buffer(geom, dist)`** | Expands a geometry outward by metric radius $d$. | Used for statutory ecological and setback zones. |
| **`ST_Intersection(A, B)`** | Returns the exact geometric overlap portion of two layers. | Extracts the precise slice of an encroaching footprint. |
| **`ST_VoronoiPolygons(pts)`** | Mathematical tessellation where every point in a cell is closest to that seed point. | Generates baseline facility service domains. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_buffer = \"\"\"
DROP TABLE IF EXISTS odaw_waterway CASCADE;
CREATE TABLE odaw_waterway (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    geom GEOMETRY(LineString, 32630)
);

INSERT INTO odaw_waterway (name, geom)
VALUES ('Odaw River Main Channel', ST_GeomFromText('LINESTRING(808000 617000, 808500 615500, 809000 613000, 809200 611000)', 32630));

DROP TABLE IF EXISTS odaw_100m_buffer CASCADE;
CREATE TABLE odaw_100m_buffer AS
SELECT 1 AS id, '100m Statutory Riparian Buffer' AS description, ST_Buffer(geom, 100.0) AS geom
FROM odaw_waterway;

DROP TABLE IF EXISTS riparian_zone_buildings CASCADE;
CREATE TABLE riparian_zone_buildings (
    bld_id SERIAL PRIMARY KEY,
    bld_type VARCHAR(50),
    geom GEOMETRY(Polygon, 32630)
);

INSERT INTO riparian_zone_buildings (bld_type, geom)
VALUES 
    ('informal_residential', ST_GeomFromText('POLYGON((808480 615500, 808510 615500, 808510 615520, 808480 615520, 808480 615500))', 32630)),
    ('commercial_store', ST_GeomFromText('POLYGON((808580 615500, 808610 615500, 808610 615520, 808580 615520, 808580 615500))', 32630)),
    ('formal_office', ST_GeomFromText('POLYGON((808700 615500, 808740 615500, 808740 615530, 808700 615530, 808700 615500))', 32630));
\"\"\"

execute_sql(sql_buffer)
print("✅ Riparian buffer and building models created.")
"""),
    code_cell("""# Identify Buffer Violations
df_violations = query_df(\"\"\"
SELECT 
    b.bld_id, b.bld_type,
    ST_Area(b.geom) AS total_footprint_m2,
    ROUND(ST_Area(ST_Intersection(b.geom, buf.geom))::NUMERIC, 1) AS encroached_area_m2,
    ROUND((ST_Area(ST_Intersection(b.geom, buf.geom)) / ST_Area(b.geom) * 100.0)::NUMERIC, 1) AS pct_encroached
FROM riparian_zone_buildings b
JOIN odaw_100m_buffer buf ON ST_Intersects(b.geom, buf.geom);
\"\"\")

df_violations
"""),
    code_cell("""# Interactive Map Preview: Buffer and Encroaching Buildings
gdf_overlay = query_gdf(\"\"\"
SELECT bld_id AS id, bld_type AS label, geom FROM riparian_zone_buildings
UNION ALL
SELECT 999 AS id, description AS label, geom FROM odaw_100m_buffer;
\"\"\")

preview_map(gdf_overlay, tooltip_cols=[\"label\"])
""")
]
create_notebook("Chapter_05_Riparian_Buffers_Voronoi.ipynb", nb_05_cells)

# =============================================================================
# CHAPTER 06: HEXAGONAL DGGS BINNING
# =============================================================================
sql_06 = """-- ============================================================================
-- CHAPTER 06: HEXAGONAL DGGS BINNING & 250M URBAN DENSITY SYNTHESIS
-- ============================================================================
-- Focus: Unbiased Spatial Aggregation across Greater Accra
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS accra_study_boundary CASCADE;
CREATE TABLE accra_study_boundary AS
SELECT ST_Buffer(ST_SetSRID(ST_MakePoint(810000, 615000), 32630), 4000.0) AS geom;

DROP TABLE IF EXISTS accra_hex_grid_250m CASCADE;
CREATE TABLE accra_hex_grid_250m AS
SELECT 
    ROW_NUMBER() OVER () AS hex_id,
    hex.geom::GEOMETRY(Polygon, 32630) AS geom
FROM accra_study_boundary b,
     ST_HexagonGrid(250.0, b.geom) AS hex
WHERE ST_Intersects(hex.geom, b.geom);

CREATE INDEX idx_hex250_geom ON accra_hex_grid_250m USING GIST(geom);

DROP TABLE IF EXISTS accra_hex_density_profile CASCADE;
CREATE TABLE accra_hex_density_profile AS
SELECT 
    h.hex_id,
    h.geom,
    COUNT(DISTINCT b.bld_id) AS building_count,
    COALESCE(SUM(ST_Area(b.geom)), 0) AS total_built_area_m2,
    ROUND((COALESCE(SUM(ST_Area(b.geom)), 0) / ST_Area(h.geom) * 100.0)::NUMERIC, 2) AS building_coverage_ratio_pct,
    COUNT(DISTINCT l.landmark_id) AS poi_count,
    COALESCE(ROUND((SUM(ST_Length(ST_Intersection(s.geom, h.geom))) / 1000.0)::NUMERIC, 2), 0) AS road_km
FROM accra_hex_grid_250m h
LEFT JOIN riparian_zone_buildings b ON ST_Intersects(b.geom, h.geom)
LEFT JOIN accra_landmarks l ON ST_Intersects(l.geom_utm30n, h.geom)
LEFT JOIN accra_streets s ON ST_Intersects(s.geom, h.geom)
GROUP BY h.hex_id, h.geom;

CREATE INDEX idx_hex_density_geom ON accra_hex_density_profile USING GIST(geom);

-- Top Density Hexagons
SELECT hex_id, building_count, building_coverage_ratio_pct, road_km
FROM accra_hex_density_profile
ORDER BY building_coverage_ratio_pct DESC
LIMIT 5;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT hex_id, building_coverage_ratio_pct, geom FROM accra_hex_density_profile;
"""
with open(BASE_DIR / "chapter_06_hexagonal_dggs_binning.sql", "w", encoding="utf-8") as f:
    f.write(sql_06)

nb_06_cells = [
    md_cell("""# 🔷 Chapter 06: Discrete Global Grid Systems (DGGS) & 250m Hexagonal Synthesis
## Overcoming the Modifiable Areal Unit Problem (MAUP) with Hexagonal Bins

### 🎯 The Mission: Why We Are Doing This
Administrative boundaries in Accra vary wildly in size, creating aggregation bias. We generate a uniform **250-meter hexagonal grid (`ST_HexagonGrid`)** to standardize spatial features into isotropic, scale-invariant spatial units.

---

### 🔑 Spatial DBA Keywords Decoded

| Keyword / Concept | Plain-English Explanation | Production Advantage |
| :--- | :--- | :--- |
| **`ST_HexagonGrid(size, bounds)`** | Generates regular hexagons covering the input polygon. | Built into PostGIS kernel (fast, no external dependencies). |
| **MAUP Bias** | Statistical distortion when aggregating data into irregular polygons. | Eliminated by uniform hexagonal lattices. |
| **Isotropic Adjacency** | All 6 neighbor cells have identical centroid distances. | Ideal for spatial weight matrices and GeoAI. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_hex = \"\"\"
DROP TABLE IF EXISTS accra_study_boundary CASCADE;
CREATE TABLE accra_study_boundary AS
SELECT ST_Buffer(ST_SetSRID(ST_MakePoint(810000, 615000), 32630), 4000.0) AS geom;

DROP TABLE IF EXISTS accra_hex_grid_250m CASCADE;
CREATE TABLE accra_hex_grid_250m AS
SELECT ROW_NUMBER() OVER () AS hex_id, hex.geom::GEOMETRY(Polygon, 32630) AS geom
FROM accra_study_boundary b,
     ST_HexagonGrid(250.0, b.geom) AS hex
WHERE ST_Intersects(hex.geom, b.geom);

CREATE INDEX idx_hex250_geom ON accra_hex_grid_250m USING GIST(geom);

DROP TABLE IF EXISTS accra_hex_density_profile CASCADE;
CREATE TABLE accra_hex_density_profile AS
SELECT 
    h.hex_id, h.geom,
    COUNT(DISTINCT b.bld_id) AS building_count,
    COALESCE(SUM(ST_Area(b.geom)), 0) AS total_built_area_m2,
    ROUND((COALESCE(SUM(ST_Area(b.geom)), 0) / ST_Area(h.geom) * 100.0)::NUMERIC, 2) AS building_coverage_ratio_pct,
    COUNT(DISTINCT l.landmark_id) AS poi_count,
    COALESCE(ROUND((SUM(ST_Length(ST_Intersection(s.geom, h.geom))) / 1000.0)::NUMERIC, 2), 0) AS road_km
FROM accra_hex_grid_250m h
LEFT JOIN riparian_zone_buildings b ON ST_Intersects(b.geom, h.geom)
LEFT JOIN accra_landmarks l ON ST_Intersects(l.geom_utm30n, h.geom)
LEFT JOIN accra_streets s ON ST_Intersects(s.geom, h.geom)
GROUP BY h.hex_id, h.geom;

CREATE INDEX idx_hex_density_geom ON accra_hex_density_profile USING GIST(geom);
\"\"\"

execute_sql(sql_hex)
print("✅ Hexagonal 250m urban profile synthesized.")
"""),
    code_cell("""# Summary Distribution
df_hex = query_df(\"\"\"
SELECT hex_id, building_count, building_coverage_ratio_pct, road_km
FROM accra_hex_density_profile
ORDER BY building_coverage_ratio_pct DESC
LIMIT 10;
\"\"\")

df_hex
"""),
    code_cell("""# Interactive Map Preview of Hexagonal Densities
gdf_hex = query_gdf(\"\"\"
SELECT hex_id, building_coverage_ratio_pct, road_km, geom FROM accra_hex_density_profile;
\"\"\")

preview_map(gdf_hex, tooltip_cols=[\"hex_id\", \"building_coverage_ratio_pct\", \"road_km\"])
""")
]
create_notebook("Chapter_06_Hexagonal_DGGS_Binning.ipynb", nb_06_cells)

# =============================================================================
# CHAPTER 07: 15-MINUTE ISOCHRONES
# =============================================================================
sql_07 = """-- ============================================================================
-- CHAPTER 07: 15-MINUTE CITY ISOCHRONES & HEALTHCARE SERVICE DESERTS
-- ============================================================================
-- Focus: Modeling Pedestrian Accessibility to Clinics in Greater Accra
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS health_origins CASCADE;
CREATE TABLE health_origins AS
SELECT 
    landmark_id, name, geom_utm30n,
    (SELECT v.id FROM accra_streets_vertices_pgr v ORDER BY v.the_geom <-> l.geom_utm30n LIMIT 1) AS start_vertex
FROM accra_landmarks l
WHERE category = 'Healthcare';

DROP TABLE IF EXISTS clinic_15min_isochrone CASCADE;
CREATE TABLE clinic_15min_isochrone AS
WITH reachable_nodes AS (
    SELECT 
        h.landmark_id, h.name, dd.node AS vertex_id, v.the_geom AS geom_vertex
    FROM health_origins h
    CROSS JOIN LATERAL pgr_drivingDistance(
        'SELECT id, source, target, cost_len / 1.25 AS cost, cost_len / 1.25 AS reverse_cost FROM accra_streets',
        h.start_vertex,
        900.0, -- 15 minutes at 1.25 m/s
        directed := false
    ) dd
    JOIN accra_streets_vertices_pgr v ON dd.node = v.id
)
SELECT 
    landmark_id, name,
    ST_ConcaveHull(ST_Collect(geom_vertex), 0.75)::GEOMETRY(Polygon, 32630) AS geom
FROM reachable_nodes
GROUP BY landmark_id, name;

CREATE INDEX idx_isochrone_geom ON clinic_15min_isochrone USING GIST(geom);

DROP TABLE IF EXISTS accra_healthcare_deserts CASCADE;
CREATE TABLE accra_healthcare_deserts AS
WITH covered_zones AS (
    SELECT ST_Union(geom) AS geom_covered FROM clinic_15min_isochrone
),
entire_city AS (
    SELECT geom AS geom_city FROM accra_study_boundary
)
SELECT 1 AS id, 'Healthcare Desert Zone' AS description, ST_Difference(c.geom_city, z.geom_covered) AS geom
FROM entire_city c, covered_zones z;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT 1 AS id, '15-Min Isochrone' AS layer, geom FROM clinic_15min_isochrone
UNION ALL
SELECT 2 AS id, 'Healthcare Desert' AS layer, geom FROM accra_healthcare_deserts;
"""
with open(BASE_DIR / "chapter_07_15min_city_isochrones.sql", "w", encoding="utf-8") as f:
    f.write(sql_07)

nb_07_cells = [
    md_cell("""# ⏱️ Chapter 07: 15-Minute City Walking Isochrones & Healthcare Deserts
## Network Reachability Analysis Using pgRouting and Concave Hulls

### 🎯 The Mission: Why We Are Doing This
The **15-Minute City concept** mandates that residents should reach primary healthcare within a 15-minute walk ($1.125\text{ km}$ at $1.25\text{ m/s}$). We compute driving-distance trees with `pgr_drivingDistance` and wrap reachable nodes into isochrone polygons to detect healthcare deserts.

---

### 🔑 Spatial DBA Keywords Decoded

| Function | Plain-English Explanation | Production Note |
| :--- | :--- | :--- |
| **`pgr_drivingDistance`** | Executes Dijkstra graph search outward up to travel-time threshold $T_{\max}$. | Returns all reachable road network nodes. |
| **`ST_ConcaveHull(pts, target)`** | Wraps point clouds into tight, concave boundaries without excessive convex ballooning. | Creates realistic polygon reachability contours. |
| **Service Desert** | City areas outside the reachability polygon. | Critical for planning new hospital investments. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_iso = \"\"\"
DROP TABLE IF EXISTS health_origins CASCADE;
CREATE TABLE health_origins AS
SELECT 
    landmark_id, name, geom_utm30n,
    (SELECT v.id FROM accra_streets_vertices_pgr v ORDER BY v.the_geom <-> l.geom_utm30n LIMIT 1) AS start_vertex
FROM accra_landmarks l
WHERE category = 'Healthcare';

DROP TABLE IF EXISTS clinic_15min_isochrone CASCADE;
CREATE TABLE clinic_15min_isochrone AS
WITH reachable_nodes AS (
    SELECT 
        h.landmark_id, h.name, dd.node AS vertex_id, v.the_geom AS geom_vertex
    FROM health_origins h
    CROSS JOIN LATERAL pgr_drivingDistance(
        'SELECT id, source, target, cost_len / 1.25 AS cost, cost_len / 1.25 AS reverse_cost FROM accra_streets',
        h.start_vertex,
        900.0,
        directed := false
    ) dd
    JOIN accra_streets_vertices_pgr v ON dd.node = v.id
)
SELECT 
    landmark_id, name,
    ST_ConcaveHull(ST_Collect(geom_vertex), 0.75)::GEOMETRY(Polygon, 32630) AS geom
FROM reachable_nodes
GROUP BY landmark_id, name;

CREATE INDEX idx_isochrone_geom ON clinic_15min_isochrone USING GIST(geom);
\"\"\"

execute_sql(sql_iso)
print("✅ 15-Minute walking isochrone polygons generated.")
"""),
    code_cell("""# View Isochrone Area Metrics
df_iso = query_df(\"\"\"
SELECT landmark_id, name, ROUND((ST_Area(geom) / 10000.0)::NUMERIC, 2) AS coverage_hectares
FROM clinic_15min_isochrone;
\"\"\")

df_iso
"""),
    code_cell("""# Interactive Map Preview of Isochrone Catchments
gdf_iso = query_gdf(\"\"\"
SELECT landmark_id, name, geom FROM clinic_15min_isochrone;
\"\"\")

preview_map(gdf_iso, tooltip_cols=[\"name\"])
""")
]
create_notebook("Chapter_07_15Min_City_Isochrones.ipynb", nb_07_cells)

# =============================================================================
# CHAPTER 08: HUFF GRAVITY MODEL
# =============================================================================
sql_08 = """-- ============================================================================
-- CHAPTER 08: IN-DATABASE HUFF GRAVITY MODEL & MARKET CATCHMENTS
-- ============================================================================
-- Focus: Predicting Consumer Draw to Makola, Kaneshie & Madina Markets in SQL
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS central_markets CASCADE;
CREATE TABLE central_markets (
    market_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    attractiveness_m2 INT,
    geom GEOMETRY(Point, 32630)
);

INSERT INTO central_markets (name, attractiveness_m2, geom)
VALUES 
    ('Makola Central Market', 60000, ST_SetSRID(ST_MakePoint(809200, 612400), 32630)),
    ('Kaneshie Market Complex', 35000, ST_SetSRID(ST_MakePoint(806100, 614500), 32630)),
    ('Madina Zongo Market', 40000, ST_SetSRID(ST_MakePoint(814500, 627100), 32630));

DROP TABLE IF EXISTS huff_market_probabilities CASCADE;
CREATE TABLE huff_market_probabilities AS
WITH od_matrix AS (
    SELECT 
        h.hex_id,
        ST_Centroid(h.geom) AS origin_geom,
        m.market_id,
        m.name AS market_name,
        m.attractiveness_m2,
        ST_Distance(ST_Centroid(h.geom), m.geom) AS distance_m
    FROM accra_hex_grid_250m h
    CROSS JOIN central_markets m
),
gravity_scores AS (
    SELECT 
        hex_id, origin_geom, market_id, market_name,
        attractiveness_m2 / POWER(NULLIF(distance_m / 1000.0, 0), 1.8) AS raw_score
    FROM od_matrix
),
probabilities AS (
    SELECT 
        hex_id, origin_geom, market_id, market_name,
        raw_score / NULLIF(SUM(raw_score) OVER(PARTITION BY hex_id), 0) AS prob_patronage
    FROM gravity_scores
)
SELECT hex_id, origin_geom, market_id, market_name, ROUND(prob_patronage::NUMERIC, 4) AS prob_patronage
FROM probabilities;

-- Dominant Market Trade Areas
SELECT hex_id, market_name, prob_patronage
FROM huff_market_probabilities
WHERE prob_patronage > 0.50
LIMIT 10;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT hex_id, market_name, prob_patronage, origin_geom AS geom
FROM huff_market_probabilities
WHERE prob_patronage > 0.50;
"""
with open(BASE_DIR / "chapter_08_huff_gravity_markets.sql", "w", encoding="utf-8") as f:
    f.write(sql_08)

nb_08_cells = [
    md_cell("""# ⚖️ Chapter 08: In-Database Huff Gravity Model & Market Catchments
## Modeling Spatial Economics and Retail Patronage Probabilities

### 🎯 The Mission: Why We Are Doing This
Spatial planners in Accra need to understand consumer catchment probabilities for major commercial hubs (**Makola**, **Kaneshie**, **Madina**). We implement the **Huff Gravity Formulation** directly in Spatial SQL using window functions:
$$P_{ij} = \\frac{S_j \\cdot d_{ij}^{-\\lambda}}{\\sum_k S_k \\cdot d_{ik}^{-\\lambda}}$$

---

### 🔑 Spatial DBA Keywords Decoded

| Term | Plain-English Explanation | Production Value |
| :--- | :--- | :--- |
| **Huff Model ($P_{ij}$)** | Gravitational interaction formula predicting consumer choice based on floor area ($S$) and distance ($d$). | Retail site selection & trade area delineation. |
| **Friction Exponent ($\\lambda$)** | Travel impedance factor (typically $1.8$ to $2.0$). | Models consumer reluctance to travel far. |
| **`PARTITION BY hex_id`** | Normalizes raw gravity scores so probabilities sum to $1.0$ per cell. | In-database spatial econometric modeling. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_huff = \"\"\"
DROP TABLE IF EXISTS central_markets CASCADE;
CREATE TABLE central_markets (
    market_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    attractiveness_m2 INT,
    geom GEOMETRY(Point, 32630)
);

INSERT INTO central_markets (name, attractiveness_m2, geom)
VALUES 
    ('Makola Central Market', 60000, ST_SetSRID(ST_MakePoint(809200, 612400), 32630)),
    ('Kaneshie Market Complex', 35000, ST_SetSRID(ST_MakePoint(806100, 614500), 32630)),
    ('Madina Zongo Market', 40000, ST_SetSRID(ST_MakePoint(814500, 627100), 32630));

DROP TABLE IF EXISTS huff_market_probabilities CASCADE;
CREATE TABLE huff_market_probabilities AS
WITH od_matrix AS (
    SELECT 
        h.hex_id, ST_Centroid(h.geom) AS origin_geom,
        m.market_id, m.name AS market_name, m.attractiveness_m2,
        ST_Distance(ST_Centroid(h.geom), m.geom) AS distance_m
    FROM accra_hex_grid_250m h
    CROSS JOIN central_markets m
),
gravity_scores AS (
    SELECT 
        hex_id, origin_geom, market_id, market_name,
        attractiveness_m2 / POWER(NULLIF(distance_m / 1000.0, 0), 1.8) AS raw_score
    FROM od_matrix
),
probabilities AS (
    SELECT 
        hex_id, origin_geom, market_id, market_name,
        raw_score / NULLIF(SUM(raw_score) OVER(PARTITION BY hex_id), 0) AS prob_patronage
    FROM gravity_scores
)
SELECT hex_id, origin_geom, market_id, market_name, ROUND(prob_patronage::NUMERIC, 4) AS prob_patronage
FROM probabilities;
\"\"\"

execute_sql(sql_huff)
print("✅ Huff Gravity model evaluated in SQL.")
"""),
    code_cell("""# View Dominant Catchment Shares
df_huff = query_df(\"\"\"
SELECT market_name, COUNT(*) AS dominant_cell_count, ROUND(AVG(prob_patronage)::NUMERIC, 3) AS avg_probability
FROM huff_market_probabilities
WHERE prob_patronage > 0.50
GROUP BY market_name;
\"\"\")

df_huff
"""),
    code_cell("""# Interactive Map Preview: Market Trade Areas
gdf_huff = query_gdf(\"\"\"
SELECT hex_id, market_name, prob_patronage, origin_geom AS geom
FROM huff_market_probabilities
WHERE prob_patronage > 0.50;
\"\"\")

preview_map(gdf_huff, tooltip_cols=[\"market_name\", \"prob_patronage\"])
""")
]
create_notebook("Chapter_08_Huff_Gravity_Markets.ipynb", nb_08_cells)

# =============================================================================
# CHAPTER 09: RASTER TERRAIN & FLOOD RISK
# =============================================================================
sql_09 = """-- ============================================================================
-- CHAPTER 09: POSTGIS RASTER TERRAIN MODELING & FLOOD HAZARDS
-- ============================================================================
-- Focus: DEM Slope Derivation and Building Vulnerability Zonal Statistics
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS accra_dem_30m CASCADE;
CREATE TABLE accra_dem_30m (
    rid SERIAL PRIMARY KEY,
    rast RASTER
);

INSERT INTO accra_dem_30m (rast)
SELECT ST_MakeEmptyRaster(100, 100, 808000, 618000, 30.0, -30.0, 0, 0, 32630) AS rast;

UPDATE accra_dem_30m
SET rast = ST_AddBand(rast, 1, '32BF', 15.0, -9999);

-- Compute Slope Degrees
DROP TABLE IF EXISTS accra_dem_slope CASCADE;
CREATE TABLE accra_dem_slope AS
SELECT rid, ST_Slope(rast, 1, '32BF', 'DEGREES', 1.0) AS rast_slope
FROM accra_dem_30m;

-- Map Algebra: Inundation Risk Surface (Elevation <= 15m AND Slope <= 2 degrees -> High Risk 3)
DROP TABLE IF EXISTS accra_flood_hazard_raster CASCADE;
CREATE TABLE accra_flood_hazard_raster AS
SELECT 
    dem.rid,
    ST_MapAlgebra(
        dem.rast, 1,
        slp.rast_slope, 1,
        'CASE WHEN [rast1] <= 15.0 AND [rast2] <= 2.0 THEN 3 ' ||
        '     WHEN [rast1] <= 30.0 AND [rast2] <= 4.0 THEN 2 ' ||
        '     ELSE 1 END',
        '8BUI', 'INTERSECTION'
    ) AS rast_hazard
FROM accra_dem_30m dem
JOIN accra_dem_slope slp ON dem.rid = slp.rid;

-- Zonal Statistics per Building
SELECT 
    b.bld_id, b.bld_type,
    ROUND((ST_SummaryStats(ST_Clip(h.rast_hazard, 1, b.geom, true))).mean::NUMERIC, 2) AS mean_flood_hazard_score
FROM riparian_zone_buildings b
JOIN accra_flood_hazard_raster h ON ST_Intersects(ST_ConvexHull(h.rast_hazard), b.geom);

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT 
    (ST_DumpAsPolygons(rast_hazard)).val AS hazard_level,
    (ST_DumpAsPolygons(rast_hazard)).geom AS geom
FROM accra_flood_hazard_raster;
"""
with open(BASE_DIR / "chapter_09_raster_terrain_flood_risk.sql", "w", encoding="utf-8") as f:
    f.write(sql_09)

nb_09_cells = [
    md_cell("""# 🌊 Chapter 09: In-Database Raster Terrain Modeling & Urban Flood Risk
## Fusing DEM Surfaces with Building Footprints via Map Algebra

### 🎯 The Mission: Why We Are Doing This
Processing satellite elevation models (DEMs) inside PostGIS allows instant vector-raster spatial joins. We calculate terrain **slope surfaces in degrees (`ST_Slope`)**, execute **Map Algebra (`ST_MapAlgebra`)** to detect low flat flood zones, and compute zonal statistics per building.

---

### 🔑 Spatial DBA Keywords Decoded

| Function | Plain-English Explanation | Production Note |
| :--- | :--- | :--- |
| **`ST_Slope(rast)`** | Computes terrain steepness in degrees from elevation grids. | Low slopes ($< 2^\circ$) signal flood-prone stagnation. |
| **`ST_MapAlgebra`** | Cell-by-cell raster calculator evaluating mathematical expressions. | Executes complex raster modeling inside SQL. |
| **`ST_SummaryStats(ST_Clip)`** | Clips raster to a vector polygon and returns `mean`, `max`, `count`. | Computes building-level physical hazard scores. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_raster = \"\"\"
DROP TABLE IF EXISTS accra_dem_30m CASCADE;
CREATE TABLE accra_dem_30m (rid SERIAL PRIMARY KEY, rast RASTER);

INSERT INTO accra_dem_30m (rast)
SELECT ST_MakeEmptyRaster(100, 100, 808000, 618000, 30.0, -30.0, 0, 0, 32630);

UPDATE accra_dem_30m SET rast = ST_AddBand(rast, 1, '32BF', 15.0, -9999);

DROP TABLE IF EXISTS accra_dem_slope CASCADE;
CREATE TABLE accra_dem_slope AS
SELECT rid, ST_Slope(rast, 1, '32BF', 'DEGREES', 1.0) AS rast_slope FROM accra_dem_30m;

DROP TABLE IF EXISTS accra_flood_hazard_raster CASCADE;
CREATE TABLE accra_flood_hazard_raster AS
SELECT 
    dem.rid,
    ST_MapAlgebra(dem.rast, 1, slp.rast_slope, 1, 'CASE WHEN [rast1] <= 15.0 AND [rast2] <= 2.0 THEN 3 WHEN [rast1] <= 30.0 AND [rast2] <= 4.0 THEN 2 ELSE 1 END', '8BUI', 'INTERSECTION') AS rast_hazard
FROM accra_dem_30m dem
JOIN accra_dem_slope slp ON dem.rid = slp.rid;
\"\"\"

execute_sql(sql_raster)
print("✅ PostGIS Raster slope and flood hazard surfaces built.")
"""),
    code_cell("""# Zonal Statistics per Building
df_zonal = query_df(\"\"\"
SELECT 
    b.bld_id, b.bld_type,
    ROUND((ST_SummaryStats(ST_Clip(h.rast_hazard, 1, b.geom, true))).mean::NUMERIC, 2) AS mean_flood_hazard_score
FROM riparian_zone_buildings b
JOIN accra_flood_hazard_raster h ON ST_Intersects(ST_ConvexHull(h.rast_hazard), b.geom);
\"\"\")

df_zonal
"""),
    code_cell("""# Interactive Map Preview: Vectorized Flood Hazard Polygons
gdf_hazard = query_gdf(\"\"\"
SELECT (ST_DumpAsPolygons(rast_hazard)).val AS hazard_level, (ST_DumpAsPolygons(rast_hazard)).geom AS geom
FROM accra_flood_hazard_raster;
\"\"\")

preview_map(gdf_hazard, tooltip_cols=[\"hazard_level\"])
""")
]
create_notebook("Chapter_09_Raster_Terrain_Flood_Risk.ipynb", nb_09_cells)

# =============================================================================
# CHAPTER 10: IN-DB SPATIAL STATISTICS & GETIS-ORD GI*
# =============================================================================
sql_10 = """-- ============================================================================
-- CHAPTER 10: IN-DATABASE SPATIAL STATISTICS & GETIS-ORD GI* HOTSPOTS
-- ============================================================================
-- Focus: Statistically Verifying Economic Hotspot Corridors in Pure SQL
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS accra_commercial_hotspots_gi CASCADE;
CREATE TABLE accra_commercial_hotspots_gi AS
WITH grid_data AS (
    SELECT 
        hex_id,
        building_coverage_ratio_pct::DOUBLE PRECISION AS x_i,
        ST_Centroid(geom) AS geom_pt,
        geom
    FROM accra_hex_density_profile
),
global_parameters AS (
    SELECT 
        COUNT(*)::DOUBLE PRECISION AS n,
        AVG(x_i) AS x_bar,
        STDDEV(x_i) AS s_val
    FROM grid_data
),
spatial_weights_w AS (
    SELECT 
        i.hex_id AS i_id,
        j.hex_id AS j_id,
        1.0::DOUBLE PRECISION AS w_ij,
        j.x_i AS x_j
    FROM grid_data i
    JOIN grid_data j ON ST_DWithin(i.geom_pt, j.geom_pt, 1000.0)
),
local_aggregations AS (
    SELECT 
        sw.i_id,
        SUM(sw.w_ij) AS sum_w,
        SUM(sw.w_ij * sw.x_j) AS sum_wx,
        SUM(POWER(sw.w_ij, 2)) AS sum_w_sq
    FROM spatial_weights_w sw
    GROUP BY sw.i_id
)
SELECT 
    g.hex_id,
    g.geom,
    g.x_i AS building_coverage_pct,
    ROUND(
        (
            (la.sum_wx - (gp.x_bar * la.sum_w)) / 
            NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0)
        )::NUMERIC,
        3
    ) AS gi_z_score,
    CASE 
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) >= 2.58 THEN 'Hotspot (99% Confidence)'
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) >= 1.96 THEN 'Hotspot (95% Confidence)'
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) <= -1.96 THEN 'Coldspot (95% Confidence)'
        ELSE 'Not Statistically Significant'
    END AS hotspot_category
FROM grid_data g
JOIN local_aggregations la ON g.hex_id = la.i_id
CROSS JOIN global_parameters gp;

CREATE INDEX idx_gi_geom ON accra_commercial_hotspots_gi USING GIST(geom);

SELECT hotspot_category, COUNT(*) AS cell_count
FROM accra_commercial_hotspots_gi
GROUP BY hotspot_category
ORDER BY cell_count DESC;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT hex_id, hotspot_category, gi_z_score, geom FROM accra_commercial_hotspots_gi;
"""
with open(BASE_DIR / "chapter_10_in_db_spatial_statistics.sql", "w", encoding="utf-8") as f:
    f.write(sql_10)

nb_10_cells = [
    md_cell("""# 📊 Chapter 10: In-Database Spatial Statistics & Getis-Ord $G_i^*$ Hotspot Analytics
## Formulating Spatial Econometric Equations in Pure PostgreSQL SQL

### 🎯 The Mission: Why We Are Doing This
Spatial planners in Accra need to verify whether economic vitality is clustering into significant commercial corridors. We implement the **Getis-Ord Local $G_i^*$ Hotspot Statistic** directly in SQL using spatial weights matrices ($\mathbf{W}$) without external Python/R libraries:
$$G_i^* = \\frac{\\sum_j w_{ij} x_j - \\bar{X} \\sum_j w_{ij}}{S \\sqrt{\\frac{n \\sum_j w_{ij}^2 - (\\sum_j w_{ij})^2}{n - 1}}}$$

---

### 🔑 Spatial DBA Keywords Decoded

| Term | Plain-English Explanation | Production Note |
| :--- | :--- | :--- |
| **Spatial Weights Matrix ($\mathbf{W}$)** | Matrix defining neighbor relationships ($w_{ij} = 1$ if within $1,000\text{m}$). | Foundation for spatial econometrics in SQL. |
| **$G_i^*$ Z-Score** | Standard normal statistic ($Z \ge +2.58 \implies 99\%$ Hotspot). | Industry gold-standard for cluster verification. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_gi = \"\"\"
DROP TABLE IF EXISTS accra_commercial_hotspots_gi CASCADE;
CREATE TABLE accra_commercial_hotspots_gi AS
WITH grid_data AS (
    SELECT 
        hex_id, building_coverage_ratio_pct::DOUBLE PRECISION AS x_i,
        ST_Centroid(geom) AS geom_pt, geom
    FROM accra_hex_density_profile
),
global_parameters AS (
    SELECT COUNT(*)::DOUBLE PRECISION AS n, AVG(x_i) AS x_bar, STDDEV(x_i) AS s_val FROM grid_data
),
spatial_weights_w AS (
    SELECT i.hex_id AS i_id, j.hex_id AS j_id, 1.0::DOUBLE PRECISION AS w_ij, j.x_i AS x_j
    FROM grid_data i JOIN grid_data j ON ST_DWithin(i.geom_pt, j.geom_pt, 1000.0)
),
local_aggregations AS (
    SELECT sw.i_id, SUM(sw.w_ij) AS sum_w, SUM(sw.w_ij * sw.x_j) AS sum_wx, SUM(POWER(sw.w_ij, 2)) AS sum_w_sq
    FROM spatial_weights_w sw GROUP BY sw.i_id
)
SELECT 
    g.hex_id, g.geom, g.x_i AS building_coverage_pct,
    ROUND(((la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0))::NUMERIC, 3) AS gi_z_score,
    CASE 
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) >= 2.58 THEN 'Hotspot (99% Confidence)'
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) >= 1.96 THEN 'Hotspot (95% Confidence)'
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) <= -1.96 THEN 'Coldspot (95% Confidence)'
        ELSE 'Not Statistically Significant'
    END AS hotspot_category
FROM grid_data g
JOIN local_aggregations la ON g.hex_id = la.i_id
CROSS JOIN global_parameters gp;

CREATE INDEX idx_gi_geom ON accra_commercial_hotspots_gi USING GIST(geom);
\"\"\"

execute_sql(sql_gi)
print("✅ Getis-Ord Gi* in-database spatial statistics completed.")
"""),
    code_cell("""# Summary Distribution of Statistically Significant Hotspots
df_gi = query_df(\"\"\"
SELECT hotspot_category, COUNT(*) AS cell_count, ROUND(AVG(gi_z_score)::NUMERIC, 2) AS mean_z_score
FROM accra_commercial_hotspots_gi
GROUP BY hotspot_category
ORDER BY cell_count DESC;
\"\"\")

df_gi
"""),
    code_cell("""# Interactive Map Preview: Statistical Hotspots & Clusters
gdf_gi = query_gdf(\"\"\"
SELECT hex_id, hotspot_category, gi_z_score, geom FROM accra_commercial_hotspots_gi;
\"\"\")

preview_map(gdf_gi, tooltip_cols=[\"hotspot_category\", \"gi_z_score\"])
""")
]
create_notebook("Chapter_10_In_DB_Spatial_Statistics.ipynb", nb_10_cells)

print("Generated Chapters 04 to 10 successfully!")
