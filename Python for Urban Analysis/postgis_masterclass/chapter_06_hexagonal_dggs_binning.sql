-- ============================================================================
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
