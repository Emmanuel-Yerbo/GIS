
## Technical Documentation: Urban POI Extraction and Geospatial Visualization

**Date:** October 2023
**Subject:** Geospatial Data Science (Urban Analytics)

---

### 1. Executive Summary
This project demonstrates a robust pipeline for acquiring, processing, and visualizing OpenStreetMap (OSM) data. Using Accra, Ghana as a case study, the workflow transitions from raw tag-based queries to high-fidelity cartographic outputs. The project focuses on Point of Interest (POI) analysis and land-use extraction (Leisure and Green Spaces).

### 2. Environment and Dependencies
The project utilizes the modern Python geospatial stack:
*   **OSMNX:** For retrieving and modeling spatial geometries from OSM.
*   **GeoPandas:** For vector data manipulation and Coordinate Reference System (CRS) management.
*   **Contextily:** For fetching web-map tiles (basemaps).
*   **Folium:** For generating interactive Leaflet.js-based web maps.
*   **Matplotlib:** For static cartographic production.

### 3. Data Acquisition Strategy
#### 3.1 Study Area Definition
The study area is dynamically defined as `"Accra, Ghana"`. The pipeline uses `ox.geocode_to_gdf` to retrieve the official administrative boundary as a `Polygon` geometry.

#### 3.2 OSM Tagging Schema
Data extraction is driven by key-value pairs representing urban infrastructure:
- **Amenities:** Hospitals, schools, marketplaces, banks, etc.
- **Leisure:** Parks, playgrounds, and stadiums.

### 4. Data Processing and Cleaning
*   **Geometry Unification:** OSM data often contains mixed types (Points, Polygons, Relations). To ensure consistency for POI mapping, all features are converted to their **centroids**.
*   **Spatial Filtering:** A topological check (`within`) is performed to ensure all extracted points reside strictly within the Accra administrative boundary.
*   **Data Serialization:** The processed layers are saved to the OGC Standard **GeoPackage (GPKG)** format, ensuring interoperability and preserving spatial indices.
*   **Error Handling:** The code includes logic to strip incompatible metadata (e.g., column names with colons like `currency:ghs`) that violate GPKG driver specifications.

### 5. Visualization Architectures
#### 5.1 Static Cartography (Thematic Map)
- **Basemap:** Utilizes CartoDB Dark Matter for high contrast.
- **Projection:** Data is reprojected to Web Mercator (`EPSG:3857`) for accurate alignment with web tiles.
- **Symbology:** Categorical coloring is applied using a custom hex-code palette.
- **Legend:** A multi-column legend dynamically calculates and displays the frequency of each urban feature.

<img width="1389" height="966" alt="STUDY" src="https://github.com/user-attachments/assets/2fe004ad-5b27-48c8-8da3-afd7441d3887" />


#### 5.2 Interactive GIS (Web Map)
- **Engine:** Folium/Leaflet.
- **Features:** Implementation of CircleMarkers with customized popups (displaying names and categories) and tooltips for enhanced UX.
- **Boundary Overlay:** The administrative border is rendered as a GeoJSON layer with custom styling.

<img width="841" height="353" alt="INTERACTIVE" src="https://github.com/user-attachments/assets/05eec393-f853-41d8-8999-d19324abf54a" />


### 6. Critical Analysis (Professor's Note)
*   **Strength:** Excellent modularity in folder management and CRS handling.
*   **Optimization:** When dealing with thousands of POIs, the interactive map limits its display to a sample (e.g., head 500) to maintain browser performance.
*   **Improvement:** Future iterations could include a density analysis (Heatmap) or accessibility routing based on the street network also available via OSMNX.
