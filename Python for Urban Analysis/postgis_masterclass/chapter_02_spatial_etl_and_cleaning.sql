-- ============================================================================
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
