"""
Builds the complete PostGIS & pgAdmin Urban Spatial Analytics Masterclass
(Ghana Edition) - generating both .sql production scripts and .ipynb Jupyter notebooks.
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("c:/YERBO/Desktop/CODING/Python for Urban Analysis/postgis_masterclass")
BASE_DIR.mkdir(parents=True, exist_ok=True)

def create_notebook(filename, cells):
    """Writes a valid Jupyter Notebook JSON file."""
    notebook_content = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.10.0"
            }
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

print("Generating Masterclass Chapters...")

# =============================================================================
# CHAPTER 00: ENVIRONMENT SETUP & DATABASE TUNING
# =============================================================================
sql_00 = """-- ============================================================================
-- CHAPTER 00: POSTGIS ENVIRONMENT INITIALIZATION & MEMORY CONFIGURATION
-- ============================================================================
-- Focus: Enterprise Spatial Database Setup for Greater Accra, Ghana
-- ============================================================================

-- 1. Create Dedicated Analytical Project Schema
CREATE SCHEMA IF NOT EXISTS urban_ghana;
SET search_path TO urban_ghana, public;

-- 2. Enable Required Spatial Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS pgrouting;

-- 3. Verify Version Compatibility and Hardware Acceleration
SELECT 
    postgis_lib_version()     AS postgis_version,
    postgis_geos_version()    AS geos_engine_version,
    postgis_proj_version()    AS proj_datum_engine,
    pgr_version()             AS pgrouting_version;

-- 4. Session-Level Memory Tuning for Spatial Relational Joins
-- (For production server-wide effect, add to postgresql.conf)
SET work_mem = '128MB';
SET maintenance_work_mem = '512MB';
SET max_parallel_workers_per_gather = 4;

-- 5. Masterclass Execution Log Table
CREATE TABLE IF NOT EXISTS masterclass_tracker (
    chapter_num INT PRIMARY KEY,
    chapter_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'INITIALIZED',
    last_executed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO masterclass_tracker (chapter_num, chapter_name, status)
VALUES (0, 'Environment & Performance Initialization', 'COMPLETED')
ON CONFLICT (chapter_num) DO UPDATE SET last_executed = CURRENT_TIMESTAMP;

SELECT * FROM masterclass_tracker;
"""

with open(BASE_DIR / "00_init_environment.sql", "w", encoding="utf-8") as f:
    f.write(sql_00)

nb_00_cells = [
    md_cell("""# 🏛️ Chapter 00: Enterprise Spatial Environment & PostgreSQL Configuration
## PostGIS for Urban Spatial Analytics (Ghana Edition)

### 🎯 The Mission: Why We Are Doing This
Spatial geometries and raster pixels require significantly more memory for sorting, hash joins, and $R$-Tree index construction than traditional text/integer tables. Before executing spatial queries across Greater Accra, we must configure PostgreSQL for spatial workloads, enable core extensions (`postgis`, `postgis_raster`, `pgrouting`), and establish an analytical project schema (`urban_ghana`).

---

### 🔑 Spatial DBA Keywords Decoded

| Keyword / Setting | Plain-English Explanation | Production Importance |
| :--- | :--- | :--- |
| **`postgis`** | The core spatial C-library extension adding geometry data types and spatial functions to PostgreSQL. | Foundation for all vector operations. |
| **`postgis_raster`** | The extension enabling in-database storage and Map Algebra for satellite & elevation grids. | Replaces external raster GIS software. |
| **`pgrouting`** | The graph network routing extension providing shortest-path and isochrone algorithms. | Transforms street centerlines into navigable transit graphs. |
| **`work_mem`** | Dedicated memory allocated for *each* spatial sort, hash join, or aggregation operation. | Prevents queries from spilling onto slow disk drives. |
| **`maintenance_work_mem`** | Memory allocated for index construction (`GIST`). | Accelerates spatial index creation by up to $10\\times$. |

---

### ⚠️ The Professor's Pitfall & DBA Warning
> **The Out-of-Memory Trap:** Never set `work_mem` excessively high on multi-user servers (e.g. 4GB). `work_mem` is allocated *per operation per user*. A query with 4 spatial joins across 20 concurrent connections can consume $4 \\times 20 \\times \\text{work_mem}$. Setting `work_mem = '128MB'` is the ideal sweet spot for spatial analysis.
"""),
    code_cell("""# Connect to the Database and Initialize Extensions
from config_db import execute_sql, query_df

sql_init = \"\"\"
CREATE SCHEMA IF NOT EXISTS urban_ghana;
SET search_path TO urban_ghana, public;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS pgrouting;

SET work_mem = '128MB';
SET maintenance_work_mem = '512MB';
\"\"\"

execute_sql(sql_init)
print("✅ Database extensions and memory parameters initialized.")
"""),
    code_cell("""# Verify Extension Versions
df_version = query_df(\"\"\"
SELECT 
    postgis_lib_version()  AS postgis_version,
    postgis_geos_version() AS geos_engine,
    postgis_proj_version() AS proj_datum_engine,
    pgr_version()          AS pgrouting_version;
\"\"\")

df_version
""")
]
create_notebook("Chapter_00_Environment_Setup.ipynb", nb_00_cells)

# =============================================================================
# CHAPTER 01: GEODESY, PROJECTIONS & DATUM TRANSFORMS
# =============================================================================
sql_01 = """-- ============================================================================
-- CHAPTER 01: SPATIAL DBMS GEODESY, PROJECTIONS & DATUM TRANSFORMATIONS
-- ============================================================================
-- Focus: Resolving Ghana's Tripartite Datum Conflict in Greater Accra
-- ============================================================================
SET search_path TO urban_ghana, public;

-- 1. Create Landmark Table with Multi-Datum Coordinate Columns
DROP TABLE IF EXISTS accra_landmarks CASCADE;
CREATE TABLE accra_landmarks (
    landmark_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    geom_wgs84 GEOMETRY(Point, 4326),
    geom_utm30n GEOMETRY(Point, 32630),
    geom_ghana_grid GEOMETRY(Point, 2136)
);

-- 2. Insert Real Greater Accra Landmarks with Native GPS Coordinates (EPSG:4326)
INSERT INTO accra_landmarks (name, category, geom_wgs84)
VALUES 
    ('Kotoka International Airport (Terminal 3)', 'Transport', ST_SetSRID(ST_MakePoint(-0.1667, 5.6052), 4326)),
    ('University of Ghana (Balme Library, Legon)', 'Education', ST_SetSRID(ST_MakePoint(-0.1870, 5.6508), 4326)),
    ('Jamestown Lighthouse', 'Heritage', ST_SetSRID(ST_MakePoint(-0.2132, 5.5345), 4326)),
    ('Tema Port (Meridian Point)', 'Maritime', ST_SetSRID(ST_MakePoint(0.0000, 5.6350), 4326)),
    ('Accra Mall (Tetteh Quarshie)', 'Commercial', ST_SetSRID(ST_MakePoint(-0.1772, 5.6178), 4326)),
    ('Korle Bu Teaching Hospital', 'Healthcare', ST_SetSRID(ST_MakePoint(-0.2285, 5.5372), 4326));

-- 3. Transform Coordinates to Projected UTM 30N (Meters) and Ghana National Grid
UPDATE accra_landmarks
SET geom_utm30n     = ST_Transform(geom_wgs84, 32630),
    geom_ghana_grid = ST_Transform(geom_wgs84, 2136);

-- 4. Build Spatial Indexes (GIST R-Tree)
CREATE INDEX idx_landmarks_wgs84 ON accra_landmarks USING GIST(geom_wgs84);
CREATE INDEX idx_landmarks_utm30n ON accra_landmarks USING GIST(geom_utm30n);

-- 5. Spatial DBA Verification: Compare Planar vs Ellipsoidal Distances
SELECT 
    a.name AS origin,
    b.name AS destination,
    ROUND(ST_Distance(a.geom_utm30n, b.geom_utm30n)::NUMERIC, 2) AS planar_dist_meters,
    ROUND(ST_Distance(a.geom_wgs84::geography, b.geom_wgs84::geography)::NUMERIC, 2) AS ellipsoidal_dist_meters,
    ROUND(ABS(ST_Distance(a.geom_utm30n, b.geom_utm30n) - ST_Distance(a.geom_wgs84::geography, b.geom_wgs84::geography))::NUMERIC, 3) AS distortion_error_meters
FROM accra_landmarks a
CROSS JOIN accra_landmarks b
WHERE a.landmark_id < b.landmark_id
ORDER BY planar_dist_meters DESC;

-- 6. VISUAL RENDERING QUERY FOR pgAdmin 4 (Click the Eye Icon on 'geom')
SELECT 
    landmark_id,
    name,
    category,
    geom_utm30n AS geom
FROM accra_landmarks;
"""

with open(BASE_DIR / "chapter_01_geodesy_and_projections.sql", "w", encoding="utf-8") as f:
    f.write(sql_01)

nb_01_cells = [
    md_cell("""# 📍 Chapter 01: Spatial DBMS Geodesy, Projections & Datum Shifts
## Managing Ghana's Tripartite Datum Conflict in PostGIS

### 🎯 The Mission: Why We Are Doing This
In Ghana, urban datasets arrive in three conflicting geodetic standards:
1. **WGS 84 (`EPSG:4326`)**: Raw GPS coordinates in angular degrees ($^\circ$).
2. **UTM Zone 30N (`EPSG:32630`)**: Ghana's national engineering standard in linear metric meters ($\text{m}$).
3. **Ghana National Grid / War Office (`EPSG:2136`)**: Historical cadastral survey grid used by the Lands Commission.

If you measure distances or areas in `EPSG:4326`, PostGIS calculates in degrees (where $1^\circ \approx 111\text{ km}$ at the equator), producing completely invalid numbers. As a Spatial DBA, you must enforce metric coordinate reprojection using `ST_Transform`.

---

### 🔑 Spatial DBA Keywords Decoded

| Function / Term | Plain-English Explanation | Production Trap / Note |
| :--- | :--- | :--- |
| **`ST_SetSRID(geom, srid)`** | Stamps an SRID tag onto geometry **WITHOUT** changing its $(X, Y)$ coordinate values. | Use ONLY when importing raw untagged coordinates. |
| **`ST_Transform(geom, target_srid)`** | **Reprojects** coordinates from one datum to another by recalculating the math. | Use to convert WGS84 GPS degrees to UTM 30N meters. |
| **`GIST` (Generalized Search Tree)** | Balanced $R$-Tree spatial index that speeds up spatial searches from $O(N)$ to $O(\log N)$. | Never run spatial queries without a GIST index! |
| **Bounding Box (`&&`)** | 2D rectangular overlap operator. Fast primary filter. | Evaluated in milliseconds using the spatial index. |

---

### ⚠️ The Professor's Pitfall & DBA Warning
> **The `ST_SetSRID` Disaster:** Never call `ST_SetSRID(geom_wgs84, 32630)`. This tells PostGIS that $(-0.18, 5.65)$ are UTM meters! Your geometry will be displaced into the Atlantic Ocean near $(0, 0)$. Always call `ST_Transform(geom_wgs84, 32630)`.
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

# 1. Create table and insert Accra landmarks
sql_create = \"\"\"
DROP TABLE IF EXISTS accra_landmarks CASCADE;
CREATE TABLE accra_landmarks (
    landmark_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    geom_wgs84 GEOMETRY(Point, 4326),
    geom_utm30n GEOMETRY(Point, 32630),
    geom_ghana_grid GEOMETRY(Point, 2136)
);

INSERT INTO accra_landmarks (name, category, geom_wgs84)
VALUES 
    ('Kotoka International Airport (Terminal 3)', 'Transport', ST_SetSRID(ST_MakePoint(-0.1667, 5.6052), 4326)),
    ('University of Ghana (Balme Library, Legon)', 'Education', ST_SetSRID(ST_MakePoint(-0.1870, 5.6508), 4326)),
    ('Jamestown Lighthouse', 'Heritage', ST_SetSRID(ST_MakePoint(-0.2132, 5.5345), 4326)),
    ('Tema Port (Meridian Point)', 'Maritime', ST_SetSRID(ST_MakePoint(0.0000, 5.6350), 4326)),
    ('Accra Mall (Tetteh Quarshie)', 'Commercial', ST_SetSRID(ST_MakePoint(-0.1772, 5.6178), 4326)),
    ('Korle Bu Teaching Hospital', 'Healthcare', ST_SetSRID(ST_MakePoint(-0.2285, 5.5372), 4326));

-- Transform to UTM Zone 30N and Ghana Grid
UPDATE accra_landmarks
SET geom_utm30n     = ST_Transform(geom_wgs84, 32630),
    geom_ghana_grid = ST_Transform(geom_wgs84, 2136);

CREATE INDEX idx_landmarks_utm30n ON accra_landmarks USING GIST(geom_utm30n);
\"\"\"

execute_sql(sql_create)
print("✅ Landmarks inserted, transformed, and indexed.")
"""),
    code_cell("""# 2. Compare Planar vs Ellipsoidal Distances
df_distances = query_df(\"\"\"
SELECT 
    a.name AS origin,
    b.name AS destination,
    ROUND(ST_Distance(a.geom_utm30n, b.geom_utm30n)::NUMERIC, 2) AS planar_dist_m,
    ROUND(ST_Distance(a.geom_wgs84::geography, b.geom_wgs84::geography)::NUMERIC, 2) AS ellipsoidal_dist_m,
    ROUND(ABS(ST_Distance(a.geom_utm30n, b.geom_utm30n) - ST_Distance(a.geom_wgs84::geography, b.geom_wgs84::geography))::NUMERIC, 3) AS distortion_m
FROM accra_landmarks a
CROSS JOIN accra_landmarks b
WHERE a.landmark_id < b.landmark_id
ORDER BY planar_dist_m DESC;
\"\"\")

df_distances
"""),
    code_cell("""# 3. Interactive Map Preview
gdf_landmarks = query_gdf(\"\"\"
SELECT landmark_id, name, category, geom_utm30n AS geom FROM accra_landmarks;
\"\"\")

preview_map(gdf_landmarks, tooltip_cols=[\"name\", \"category\"], zoom_start=11)
""")
]
create_notebook("Chapter_01_Geodesy_and_Projections.ipynb", nb_01_cells)

# =============================================================================
# CHAPTER 02: SPATIAL ETL & TOPOLOGY CLEANING
# =============================================================================
sql_02 = """-- ============================================================================
-- CHAPTER 02: SPATIAL ETL & AUTOMATED TOPOLOGY CLEANING
-- ============================================================================
-- Focus: Detecting and Repairing Corrupted Building Footprints in Accra
-- ============================================================================
SET search_path TO urban_ghana, public;

-- 1. Create Quarantine Table
DROP TABLE IF EXISTS spatial_quarantine_log CASCADE;
CREATE TABLE spatial_quarantine_log (
    log_id SERIAL PRIMARY KEY,
    feature_source VARCHAR(100),
    rejection_reason TEXT,
    original_geom GEOMETRY,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create Staging Table with Valid & Corrupted Geometries
DROP TABLE IF EXISTS staging_buildings CASCADE;
CREATE TABLE staging_buildings (
    building_id SERIAL PRIMARY KEY,
    building_tag VARCHAR(50),
    raw_geom GEOMETRY(Geometry, 32630)
);

INSERT INTO staging_buildings (building_tag, raw_geom)
VALUES 
    -- Valid rectangular building (Cantonments)
    ('residential', ST_GeomFromText('POLYGON((809000 614000, 809020 614000, 809020 614030, 809000 614030, 809000 614000))', 32630)),
    -- Invalid Self-Intersecting Figure-8 building (Nima)
    ('commercial', ST_GeomFromText('POLYGON((809100 614100, 809150 614150, 809150 614100, 809100 614150, 809100 614100))', 32630)),
    -- Sliver polygon with repeated vertices
    ('residential', ST_GeomFromText('POLYGON((809200 614200, 809200.0001 614200, 809210 614220, 809200 614220, 809200 614200))', 32630));

-- 3. Production Cleaning & Normalization Pipeline
DROP TABLE IF EXISTS clean_buildings CASCADE;
CREATE TABLE clean_buildings (
    building_id INT PRIMARY KEY,
    building_tag VARCHAR(50),
    geom GEOMETRY(MultiPolygon, 32630),
    was_repaired BOOLEAN
);

INSERT INTO clean_buildings (building_id, building_tag, geom, was_repaired)
SELECT 
    building_id,
    building_tag,
    ST_Multi(
        ST_CollectionExtract(
            ST_MakeValid(
                ST_SnapToGrid(raw_geom, 0.001)
            ), 
            3 -- Extract Polygons only
        )
    )::GEOMETRY(MultiPolygon, 32630) AS geom,
    NOT ST_IsValid(raw_geom) AS was_repaired
FROM staging_buildings;

-- Log rejected/corrupted features into quarantine
INSERT INTO spatial_quarantine_log (feature_source, rejection_reason, original_geom)
SELECT 'staging_buildings', ST_IsValidReason(raw_geom), raw_geom
FROM staging_buildings
WHERE ST_IsValid(raw_geom) = FALSE;

-- Enforce Strict Validity Constraint & Spatial Index
CREATE INDEX idx_clean_bld_geom ON clean_buildings USING GIST(geom);
ALTER TABLE clean_buildings ADD CONSTRAINT chk_geom_valid CHECK (ST_IsValid(geom));

-- Audit Report
SELECT 
    COUNT(*) AS total_processed,
    COUNT(*) FILTER (WHERE was_repaired = TRUE) AS total_repaired,
    ROUND(AVG(ST_NPoints(geom))::NUMERIC, 1) AS avg_vertices
FROM clean_buildings;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT building_id, building_tag, was_repaired, geom FROM clean_buildings;
"""

with open(BASE_DIR / "chapter_02_spatial_etl_and_cleaning.sql", "w", encoding="utf-8") as f:
    f.write(sql_02)

nb_02_cells = [
    md_cell("""# 📥 Chapter 02: Spatial ETL, Ingestion & Automated Topology Cleaning
## Automated Detection and Repair of Corrupted Building Geometries

### 🎯 The Mission: Why We Are Doing This
Spatial datasets from digitizing surveys, OpenStreetMap, or CAD conversions frequently contain topological errors:
1. **Self-intersecting "figure-8" polygons** (borders crossing themselves).
2. **Unclosed boundary rings**.
3. **Micro-sliver coordinate jitter**.

If you insert invalid geometries into PostGIS, subsequent spatial operations (`ST_Intersection`, `ST_Buffer`) will crash with `GEOSTopologyException`. A Spatial DBA must build automated cleaning and quarantine pipelines.

---

### 🔑 Spatial DBA Keywords Decoded

| Keyword / Function | Plain-English Explanation | Production Note |
| :--- | :--- | :--- |
| **`ST_IsValid(geom)`** | Returns `TRUE` if a polygon obeys OGC topological rules; `FALSE` if broken. | Used as a filter and table check constraint. |
| **`ST_IsValidReason(geom)`** | Returns a diagnostic string explaining *why* geometry failed (e.g. `Self-intersection [809125 614125]`). | Logs exact error locations for survey audits. |
| **`ST_MakeValid(geom)`** | Automatically repairs self-intersections and invalid rings using GEOS algorithms. | Fixes figure-8 polygons into valid MultiPolygons. |
| **`ST_SnapToGrid(geom, tol)`** | Snaps coordinates to a grid (e.g. $1\text{mm} = 0.001\text{m}$) to remove micro-jitter. | Prevents precision floating-point errors. |
| **`ST_CollectionExtract(geom, type)`** | Extracts only Polygons (3), Lines (2), or Points (1) from messy `GeometryCollections`. | Enforces strict geometry types. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_etl = \"\"\"
DROP TABLE IF EXISTS staging_buildings CASCADE;
CREATE TABLE staging_buildings (
    building_id SERIAL PRIMARY KEY,
    building_tag VARCHAR(50),
    raw_geom GEOMETRY(Geometry, 32630)
);

INSERT INTO staging_buildings (building_tag, raw_geom)
VALUES 
    ('residential', ST_GeomFromText('POLYGON((809000 614000, 809020 614000, 809020 614030, 809000 614030, 809000 614000))', 32630)),
    ('commercial', ST_GeomFromText('POLYGON((809100 614100, 809150 614150, 809150 614100, 809100 614150, 809100 614100))', 32630)),
    ('residential', ST_GeomFromText('POLYGON((809200 614200, 809200.0001 614200, 809210 614220, 809200 614220, 809200 614200))', 32630));

DROP TABLE IF EXISTS clean_buildings CASCADE;
CREATE TABLE clean_buildings AS
SELECT 
    building_id,
    building_tag,
    ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SnapToGrid(raw_geom, 0.001)), 3))::GEOMETRY(MultiPolygon, 32630) AS geom,
    NOT ST_IsValid(raw_geom) AS was_repaired
FROM staging_buildings;

CREATE INDEX idx_clean_bld_geom ON clean_buildings USING GIST(geom);
\"\"\"

execute_sql(sql_etl)
print("✅ Staging data processed, repaired, and validated.")
"""),
    code_cell("""# Inspect Cleaning Results
df_clean = query_df(\"\"\"
SELECT building_id, building_tag, was_repaired, ST_IsValid(geom) AS is_now_valid, ST_Area(geom) AS area_m2
FROM clean_buildings;
\"\"\")

df_clean
"""),
    code_cell("""# Interactive Map Preview of Repaired Buildings
gdf_clean = query_gdf(\"\"\"
SELECT building_id, building_tag, was_repaired, geom FROM clean_buildings;
\"\"\")

preview_map(gdf_clean, tooltip_cols=[\"building_id\", \"building_tag\", \"was_repaired\"])
""")
]
create_notebook("Chapter_02_Spatial_ETL_and_Cleaning.ipynb", nb_02_cells)

# =============================================================================
# CHAPTER 03: BUILDING MORPHOMETRICS & DENSITY (DBSCAN)
# =============================================================================
sql_03 = """-- ============================================================================
-- CHAPTER 03: BUILDING MORPHOMETRICS & IN-DATABASE DBSCAN CLUSTERING
-- ============================================================================
-- Focus: Classifying Informal (Nima) vs Planned (Cantonments) Urban Fabrics
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS accra_building_inventory CASCADE;
CREATE TABLE accra_building_inventory (
    building_id SERIAL PRIMARY KEY,
    neighborhood VARCHAR(50),
    geom GEOMETRY(Polygon, 32630)
);

INSERT INTO accra_building_inventory (neighborhood, geom)
VALUES 
    -- Cantonments (Planned Estate: Large footprints, regular spacing)
    ('Cantonments', ST_GeomFromText('POLYGON((810000 615000, 810030 615000, 810030 615025, 810000 615025, 810000 615000))', 32630)),
    ('Cantonments', ST_GeomFromText('POLYGON((810060 615000, 810090 615000, 810090 615025, 810060 615025, 810060 615000))', 32630)),
    ('Cantonments', ST_GeomFromText('POLYGON((810000 615060, 810030 615060, 810030 615085, 810000 615085, 810000 615060))', 32630)),
    
    -- Nima (Informal High-Density Fabric: Small footprints, touching structures)
    ('Nima', ST_GeomFromText('POLYGON((808000 616000, 808010 616000, 808010 616008, 808000 616008, 808000 616000))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808012 616000, 808022 616000, 808022 616008, 808012 616008, 808012 616000))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808000 616010, 808010 616010, 808010 616018, 808000 616018, 808000 616010))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808012 616010, 808022 616010, 808022 616018, 808012 616018, 808012 616010))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808024 616000, 808034 616000, 808034 616018, 808024 616018, 808024 616000))', 32630));

-- Morphometric Calculations and In-Database DBSCAN Clustering
DROP TABLE IF EXISTS accra_morphometric_analysis CASCADE;
CREATE TABLE accra_morphometric_analysis AS
WITH computed_metrics AS (
    SELECT 
        building_id,
        neighborhood,
        geom,
        ST_Area(geom) AS footprint_area_m2,
        ST_Perimeter(geom) AS perimeter_m,
        (4 * PI() * ST_Area(geom)) / NULLIF(POWER(ST_Perimeter(geom), 2), 0) AS compactness_ci,
        ST_Area(geom) / NULLIF(ST_Area(ST_OrientedEnvelope(geom)), 0) AS rectangular_fit
    FROM accra_building_inventory
)
SELECT 
    building_id,
    neighborhood,
    geom,
    ROUND(footprint_area_m2::NUMERIC, 1) AS area_m2,
    ROUND(perimeter_m::NUMERIC, 1) AS perimeter_m,
    ROUND(compactness_ci::NUMERIC, 3) AS compactness_ci,
    ROUND(rectangular_fit::NUMERIC, 3) AS rectangular_fit,
    CASE 
        WHEN compactness_ci < 0.60 AND footprint_area_m2 < 100 THEN 'Organic / High Density'
        ELSE 'Formal / Planned'
    END AS morphological_class,
    ST_ClusterDBSCAN(geom, eps := 15, minpoints := 3) OVER () AS cluster_group_id
FROM computed_metrics;

CREATE INDEX idx_morpho_geom ON accra_morphometric_analysis USING GIST(geom);

-- Summary Stats
SELECT 
    neighborhood,
    morphological_class,
    COUNT(*) AS building_count,
    ROUND(AVG(area_m2)::NUMERIC, 1) AS mean_area_m2,
    ROUND(AVG(compactness_ci)::NUMERIC, 3) AS mean_compactness
FROM accra_morphometric_analysis
GROUP BY neighborhood, morphological_class;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT building_id, neighborhood, morphological_class, cluster_group_id, geom FROM accra_morphometric_analysis;
"""

with open(BASE_DIR / "chapter_03_building_morphometrics.sql", "w", encoding="utf-8") as f:
    f.write(sql_03)

nb_03_cells = [
    md_cell("""# 🏢 Chapter 03: Building Morphometrics & In-Database DBSCAN Clustering
## Distinguishing Informal Settlements from Planned Neighborhoods

### 🎯 The Mission: Why We Are Doing This
In Greater Accra, urban morphology reflects socioeconomic settlement patterns:
- **Planned enclaves (Cantonments, Airport Residential):** Large footprint areas ($A > 300\text{ m}^2$), high compactness ($CI > 0.75$), regular spacing.
- **Informal / Organic settlements (Nima, Old Fadama, Jamestown):** Small footprints ($A < 80\text{ m}^2$), lower compactness, high spatial density forming massive contiguous clusters.

Using PostGIS computational geometry functions and in-database **DBSCAN Clustering (`ST_ClusterDBSCAN`)**, we classify building typologies directly inside SQL.

---

### 🔑 Spatial DBA Keywords Decoded

| Keyword / Metric | Plain-English Explanation | Production Purpose |
| :--- | :--- | :--- |
| **Isoperimetric Quotient ($CI$)** | Compactness formula: $CI = \frac{4\pi A}{P^2}$. Circles = $1.0$, rectangles $\approx 0.78$, fractured shapes $< 0.45$. | Mathematical quantifier of structural irregularity. |
| **`ST_OrientedEnvelope(geom)`** | Computes the smallest rotated bounding rectangle enclosing the polygon. | Used to measure true length, width, and rectangular fit. |
| **`ST_ClusterDBSCAN(geom, eps, minpts)`** | Groups spatial objects into clusters if at least `minpts` features lie within metric distance `eps`. | Automatically detects contiguous informal settlement clusters. |
"""),
    code_cell("""from config_db import execute_sql, query_df, query_gdf, preview_map

sql_morpho = \"\"\"
DROP TABLE IF EXISTS accra_building_inventory CASCADE;
CREATE TABLE accra_building_inventory (
    building_id SERIAL PRIMARY KEY,
    neighborhood VARCHAR(50),
    geom GEOMETRY(Polygon, 32630)
);

INSERT INTO accra_building_inventory (neighborhood, geom)
VALUES 
    ('Cantonments', ST_GeomFromText('POLYGON((810000 615000, 810030 615000, 810030 615025, 810000 615025, 810000 615000))', 32630)),
    ('Cantonments', ST_GeomFromText('POLYGON((810060 615000, 810090 615000, 810090 615025, 810060 615025, 810060 615000))', 32630)),
    ('Cantonments', ST_GeomFromText('POLYGON((810000 615060, 810030 615060, 810030 615085, 810000 615085, 810000 615060))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808000 616000, 808010 616000, 808010 616008, 808000 616008, 808000 616000))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808012 616000, 808022 616000, 808022 616008, 808012 616008, 808012 616000))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808000 616010, 808010 616010, 808010 616018, 808000 616018, 808000 616010))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808012 616010, 808022 616010, 808022 616018, 808012 616018, 808012 616010))', 32630)),
    ('Nima', ST_GeomFromText('POLYGON((808024 616000, 808034 616000, 808034 616018, 808024 616018, 808024 616000))', 32630));

DROP TABLE IF EXISTS accra_morphometric_analysis CASCADE;
CREATE TABLE accra_morphometric_analysis AS
WITH computed_metrics AS (
    SELECT 
        building_id, neighborhood, geom,
        ST_Area(geom) AS footprint_area_m2,
        ST_Perimeter(geom) AS perimeter_m,
        (4 * PI() * ST_Area(geom)) / NULLIF(POWER(ST_Perimeter(geom), 2), 0) AS compactness_ci,
        ST_Area(geom) / NULLIF(ST_Area(ST_OrientedEnvelope(geom)), 0) AS rectangular_fit
    FROM accra_building_inventory
)
SELECT 
    building_id, neighborhood, geom,
    ROUND(footprint_area_m2::NUMERIC, 1) AS area_m2,
    ROUND(perimeter_m::NUMERIC, 1) AS perimeter_m,
    ROUND(compactness_ci::NUMERIC, 3) AS compactness_ci,
    ROUND(rectangular_fit::NUMERIC, 3) AS rectangular_fit,
    CASE 
        WHEN compactness_ci < 0.60 AND footprint_area_m2 < 100 THEN 'Organic / High Density'
        ELSE 'Formal / Planned'
    END AS morphological_class,
    ST_ClusterDBSCAN(geom, eps := 15, minpoints := 3) OVER () AS cluster_group_id
FROM computed_metrics;

CREATE INDEX idx_morpho_geom ON accra_morphometric_analysis USING GIST(geom);
\"\"\"

execute_sql(sql_morpho)
print("✅ Morphometrics and DBSCAN clustering completed.")
"""),
    code_cell("""# View Morphometrics Summary
df_morpho = query_df(\"\"\"
SELECT neighborhood, morphological_class, COUNT(*) AS count, ROUND(AVG(area_m2)::NUMERIC, 1) AS avg_area_m2, ROUND(AVG(compactness_ci)::NUMERIC, 3) AS avg_compactness
FROM accra_morphometric_analysis
GROUP BY neighborhood, morphological_class;
\"\"\")

df_morpho
"""),
    code_cell("""# Interactive Map Preview (Color by Cluster ID)
gdf_morpho = query_gdf(\"\"\"
SELECT building_id, neighborhood, morphological_class, cluster_group_id, geom FROM accra_morphometric_analysis;
\"\"\")

preview_map(gdf_morpho, tooltip_cols=[\"building_id\", \"neighborhood\", \"morphological_class\", \"cluster_group_id\"])
""")
]
create_notebook("Chapter_03_Building_Morphometrics.ipynb", nb_03_cells)

print("Generated Chapters 00 to 03...")
