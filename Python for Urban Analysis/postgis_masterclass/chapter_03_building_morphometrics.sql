-- ============================================================================
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
