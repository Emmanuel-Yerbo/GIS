-- ============================================================================
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
