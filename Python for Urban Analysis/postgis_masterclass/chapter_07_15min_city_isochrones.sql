-- ============================================================================
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
