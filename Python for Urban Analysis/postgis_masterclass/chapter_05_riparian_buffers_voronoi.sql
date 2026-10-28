-- ============================================================================
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
