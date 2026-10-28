-- ============================================================================
-- CHAPTER 08: IN-DATABASE HUFF GRAVITY MODEL & MARKET CATCHMENTS
-- ============================================================================
-- Focus: Predicting Consumer Draw to Makola, Kaneshie & Madina Markets in SQL
-- ============================================================================
SET search_path TO urban_ghana, public;

DROP TABLE IF EXISTS central_markets CASCADE;
CREATE TABLE central_markets (
    market_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    attractiveness_m2 INT,
    geom GEOMETRY(Point, 32630)
);

INSERT INTO central_markets (name, attractiveness_m2, geom)
VALUES 
    ('Makola Central Market', 60000, ST_SetSRID(ST_MakePoint(809200, 612400), 32630)),
    ('Kaneshie Market Complex', 35000, ST_SetSRID(ST_MakePoint(806100, 614500), 32630)),
    ('Madina Zongo Market', 40000, ST_SetSRID(ST_MakePoint(814500, 627100), 32630));

DROP TABLE IF EXISTS huff_market_probabilities CASCADE;
CREATE TABLE huff_market_probabilities AS
WITH od_matrix AS (
    SELECT 
        h.hex_id,
        ST_Centroid(h.geom) AS origin_geom,
        m.market_id,
        m.name AS market_name,
        m.attractiveness_m2,
        ST_Distance(ST_Centroid(h.geom), m.geom) AS distance_m
    FROM accra_hex_grid_250m h
    CROSS JOIN central_markets m
),
gravity_scores AS (
    SELECT 
        hex_id, origin_geom, market_id, market_name,
        attractiveness_m2 / POWER(NULLIF(distance_m / 1000.0, 0), 1.8) AS raw_score
    FROM od_matrix
),
probabilities AS (
    SELECT 
        hex_id, origin_geom, market_id, market_name,
        raw_score / NULLIF(SUM(raw_score) OVER(PARTITION BY hex_id), 0) AS prob_patronage
    FROM gravity_scores
)
SELECT hex_id, origin_geom, market_id, market_name, ROUND(prob_patronage::NUMERIC, 4) AS prob_patronage
FROM probabilities;

-- Dominant Market Trade Areas
SELECT hex_id, market_name, prob_patronage
FROM huff_market_probabilities
WHERE prob_patronage > 0.50
LIMIT 10;

-- VISUAL RENDERING QUERY FOR pgAdmin 4
SELECT hex_id, market_name, prob_patronage, origin_geom AS geom
FROM huff_market_probabilities
WHERE prob_patronage > 0.50;
