-- ============================================================================
-- CHAPTER 10: IN-DATABASE SPATIAL STATISTICS & GETIS-ORD GI* HOTSPOTS
-- ============================================================================
-- Focus: Statistically Verifying Economic Hotspot Corridors in Pure SQL
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS accra_commercial_hotspots_gi CASCADE;
CREATE TABLE accra_commercial_hotspots_gi AS
WITH grid_data AS (
    SELECT 
        hex_id,
        building_coverage_ratio_pct::DOUBLE PRECISION AS x_i,
        ST_Centroid(geom) AS geom_pt,
        geom
    FROM accra_hex_density_profile
),
global_parameters AS (
    SELECT 
        COUNT(*)::DOUBLE PRECISION AS n,
        AVG(x_i) AS x_bar,
        STDDEV(x_i) AS s_val
    FROM grid_data
),
spatial_weights_w AS (
    SELECT 
        i.hex_id AS i_id,
        j.hex_id AS j_id,
        1.0::DOUBLE PRECISION AS w_ij,
        j.x_i AS x_j
    FROM grid_data i
    JOIN grid_data j ON ST_DWithin(i.geom_pt, j.geom_pt, 1000.0)
),
local_aggregations AS (
    SELECT 
        sw.i_id,
        SUM(sw.w_ij) AS sum_w,
        SUM(sw.w_ij * sw.x_j) AS sum_wx,
        SUM(POWER(sw.w_ij, 2)) AS sum_w_sq
    FROM spatial_weights_w sw
    GROUP BY sw.i_id
)
SELECT 
    g.hex_id,
    g.geom,
    g.x_i AS building_coverage_pct,
    ROUND(
        (
            (la.sum_wx - (gp.x_bar * la.sum_w)) / 
            NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0)
        )::NUMERIC,
        3
    ) AS gi_z_score,
    CASE 
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) >= 2.58 THEN 'Hotspot (99% Confidence)'
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) >= 1.96 THEN 'Hotspot (95% Confidence)'
        WHEN (la.sum_wx - (gp.x_bar * la.sum_w)) / NULLIF((gp.s_val * SQRT( ( (gp.n * la.sum_w_sq) - POWER(la.sum_w, 2) ) / (gp.n - 1.0) )), 0) <= -1.96 THEN 'Coldspot (95% Confidence)'
        ELSE 'Not Statistically Significant'
    END AS hotspot_category
FROM grid_data g
JOIN local_aggregations la ON g.hex_id = la.i_id
CROSS JOIN global_parameters gp;

CREATE INDEX idx_gi_geom ON accra_commercial_hotspots_gi USING GIST(geom);

SELECT hotspot_category, COUNT(*) AS cell_count
FROM accra_commercial_hotspots_gi
GROUP BY hotspot_category
ORDER BY cell_count DESC;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT hex_id, hotspot_category, gi_z_score, geom FROM accra_commercial_hotspots_gi;
