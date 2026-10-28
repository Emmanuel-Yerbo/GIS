-- ============================================================================
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
