-- ============================================================================
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
