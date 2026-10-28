-- ============================================================================
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
