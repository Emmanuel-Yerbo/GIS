markdown
# Urban Analytics: Accra Building Footprint Analysis & Morphology

## 1. Executive Summary
This repository contains a reproducible Python-based pipeline for the extraction, processing, and multi-scalar visualization of urban building footprints in **Accra, Ghana**. Using the `OSMNX` framework, we analyze over 228,000 unique geometries to assess urban density and functional classification. This project serves as a template for large-scale urban morphology studies in rapidly urbanizing contexts.

## 2. Technical Environment
The analysis is conducted within a cloud-based Python environment using the modern geospatial stack:
- **OSMNX**: For API interfacing and topology extraction.
- **GeoPandas**: For vector operations and CRS management.
- **Contextily**: For high-resolution basemap integration (CartoDB DarkMatter).
- **Matplotlib/Folium**: For static and interactive cartographic outputs.

## 3. Data Pipeline & Methodology

### 3.1 Data Acquisition
We utilize the `building=True` tag to retrieve all building-related features within the Accra administrative boundary. This includes polygons, multipolygons, and points (which are filtered during pre-processing).

### 3.2 Geospatial Refinement (CRS Management)
A critical component of our workflow is the use of dual-coordinate systems:
- **EPSG:32630 (UTM Zone 30N)**: Used for accurate metric calculations, specifically for calculating building footprint area in $m^2$.
- **EPSG:3857 (Web Mercator)**: Used for cartographic projection to align with web-based tile providers.

### 3.3 Data Schema
Processed data is exported in the OGC-standard **GeoPackage (GPKG)** format with the following core attributes:
| Column | Description | Unit |
| :--- | :--- | :--- |
| `geometry` | Polygon/MultiPolygon vector | - |
| `area_m2` | Projected footprint area | Square Meters |
| `bldg_type` | Functional classification (Residential, Commercial, etc.) | Categorical |
| `levels` | Verticality data (Building Floors) | Count |

## 4. Visual Analysis

### 4.1 Quantitative Choropleth
We employ a sequential `YlOrRd` (Yellow-Orange-Red) colormap using **Quantile classification ($k=7$)** to visualize the distribution of building sizes across the city. This allows for the identification of high-density formal sectors vs. fragmented informal footprints.
<img width="1589" height="1019" alt="buildings_area" src="https://github.com/user-attachments/assets/6ee8bcb5-6f1f-4513-ac7a-27c90d74a948" />


### 4.2 Categorical Urban Fabric
To distinguish land-use patterns, a custom categorical mapping is implemented. This visualization reveals the spatial clustering of institutional, commercial, and residential zones, providing insights into Accra's mixed-use urban structure.
<img width="1589" height="1101" alt="BUILDING TYPES" src="https://github.com/user-attachments/assets/403f2c45-80ec-48df-a6fc-3d733e6cc8ed" />

