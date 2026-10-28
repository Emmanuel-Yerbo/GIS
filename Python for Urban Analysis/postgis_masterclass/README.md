# 🏛️ POSTGIS & pgADMIN FOR URBAN SPATIAL ANALYTICS (GHANA EDITION)
## An Enterprise Masterclass & Spatial DBA Laboratory Series

Welcome to the **PostGIS & pgAdmin Urban Spatial Analytics Masterclass (Ghana Edition)**. This repository provides a complete, dual-format curriculum designed for urban scientists, spatial data engineers, and aspiring **Spatial Database Administrators (Spatial DBAs)**.

---

## 🧭 CURRICULUM ARCHITECTURE (DUAL-FORMAT)

Every chapter is delivered in two mirrored formats:
1. **Interactive Jupyter Notebook (`.ipynb`)**: Features rich Markdown explanations, plain-English *Keyword Decoders*, *Professor's Warnings*, inline SQL execution, and live interactive Leaflet/Folium map widgets.
2. **Production SQL Script (`.sql`)**: Self-contained, production-grade Spatial SQL with realistic Greater Accra coordinates, table constraints, and `GIST` indexes for direct execution in **pgAdmin 4's Query Tool**.

```
postgis_masterclass/
│
├── config_db.py                                   <-- Central database connection helper
│
├── 00_init_environment.sql                       <-- Ch 00: Environment & memory tuning
├── Chapter_00_Environment_Setup.ipynb
│
├── chapter_01_geodesy_and_projections.sql        <-- Ch 01: WGS84, UTM 30N & Ghana Grid
├── Chapter_01_Geodesy_and_Projections.ipynb
│
├── chapter_02_spatial_etl_and_cleaning.sql       <-- Ch 02: ST_MakeValid & topology repairs
├── Chapter_02_Spatial_ETL_and_Cleaning.ipynb
│
├── chapter_03_building_morphometrics.sql         <-- Ch 03: Compactness & DBSCAN clustering
├── Chapter_03_Building_Morphometrics.ipynb
│
├── chapter_04_street_networks_pgrouting.sql      <-- Ch 04: pgRouting graph & azimuth roses
├── Chapter_04_Street_Networks_pgRouting.ipynb
│
├── chapter_05_riparian_buffers_voronoi.sql       <-- Ch 05: Odaw buffer & hospital catchments
├── Chapter_05_Riparian_Buffers_Voronoi.ipynb
│
├── chapter_06_hexagonal_dggs_binning.sql         <-- Ch 06: ST_HexagonGrid 250m synthesis
├── Chapter_06_Hexagonal_DGGS_Binning.ipynb
│
├── chapter_07_15min_city_isochrones.sql          <-- Ch 07: 15-Minute walking access deserts
├── Chapter_07_15Min_City_Isochrones.ipynb
│
├── chapter_08_huff_gravity_markets.sql           <-- Ch 08: In-DB Huff Gravity retail model
├── Chapter_08_Huff_Gravity_Markets.ipynb
│
├── chapter_09_raster_terrain_flood_risk.sql      <-- Ch 09: PostGIS Raster & slope flood risk
├── Chapter_09_Raster_Terrain_Flood_Risk.ipynb
│
├── chapter_10_in_db_spatial_statistics.sql       <-- Ch 10: Getis-Ord Gi* in pure SQL
└── Chapter_10_In_DB_Spatial_Statistics.ipynb
```

---

## 🚀 QUICK-START GUIDE

### Option A: Running in pgAdmin 4 (Pure SQL Mode)
1. Open **pgAdmin 4** and connect to your PostgreSQL database.
2. Create or select a database (e.g. `urban_analytics_ghana`).
3. Open `Tools` $\rightarrow$ `Query Tool` (or press `Alt + Shift + Q`).
4. Open any chapter script (e.g. `chapter_05_riparian_buffers_voronoi.sql`).
5. Press **`F5` (Execute)**.
6. In the Data Output grid, click the **Eye Icon (View Geometry)** next to `geom` to view the interactive map directly inside pgAdmin!

### Option B: Running in Jupyter Notebooks (Interactive Python/SQL Mode)
1. Ensure your Python environment has `geopandas`, `sqlalchemy`, `psycopg2` (or `psycopg`), `folium`, and `matplotlib`.
2. Configure your connection in `config_db.py` or set environment variables:
   ```bash
   export POSTGIS_USER="postgres"
   export POSTGIS_PASSWORD="your_password"
   export POSTGIS_HOST="localhost"
   export POSTGIS_PORT="5432"
   export POSTGIS_DB="urban_analytics_ghana"
   ```
3. Start Jupyter Notebook:
   ```bash
   jupyter notebook
   ```
4. Open `Chapter_01_Geodesy_and_Projections.ipynb` and run all cells!

---

## 🏆 COMPLETE CHAPTER OUTLINE

| Ch. | Title | Core Spatial Concepts | Ghana Urban Case Study |
| :---: | :--- | :--- | :--- |
| **00** | **Environment & Memory Tuning** | Extensions, `shared_buffers`, `work_mem` | Setting up the `urban_ghana` analytical schema |
| **01** | **Geodesy & Datum Shifts** | `ST_SetSRID`, `ST_Transform`, `GIST` | Resolving WGS84, UTM 30N, and Ghana National Grid |
| **02** | **Spatial ETL & Cleaning** | `ST_IsValid`, `ST_MakeValid`, `ST_SnapToGrid` | Auto-repairing figure-8 building footprints |
| **03** | **Building Morphometrics** | Isoperimetric $CI$, `ST_ClusterDBSCAN` | Classifying Nima vs Cantonments fabrics |
| **04** | **Street Graphs & pgRouting** | `pgr_createTopology`, `ST_Azimuth` | Building road graphs and azimuth orientation roses |
| **05** | **Riparian Buffers & Voronoi** | `ST_Buffer`, `ST_Intersection`, `ST_Voronoi` | Odaw river 100m flood buffer encroachment |
| **06** | **Hexagonal DGGS Binning** | `ST_HexagonGrid 250m`, Spatial Aggregations | Resolving MAUP bias across Greater Accra |
| **07** | **15-Min Walk Isochrones** | `pgr_drivingDistance`, `ST_ConcaveHull` | Mapping healthcare service deserts in GAMA |
| **08** | **In-DB Huff Gravity Model** | Gravity interaction, Partitioned windowing | Predicting Makola vs Madina market trade shares |
| **09** | **PostGIS Raster Flood Risk** | `postgis_raster`, `ST_Slope`, `ST_MapAlgebra` | Terrain slope and building flood exposure scores |
| **10** | **In-DB Spatial Statistics** | Getis-Ord $G_i^*$ Z-Scores, Weights Matrix $\mathbf{W}$ | Statistically verifying economic hotspot corridors |
