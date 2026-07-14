
# Geospatial Analysis of Accra, Ghana using OSMnx

This notebook demonstrates a complete workflow for fetching, processing, and visualizing urban spatial data for Accra, Ghana. Using OpenStreetMap (OSM) data, we establish a study boundary, perform geometric calculations, and generate both static and interactive maps.

<img width="1189" height="834" alt="STUDY" src="https://github.com/user-attachments/assets/ef900e56-e1d9-4286-9de4-8d6ee0e5fc84" />


## Project Highlights
- **Automated Data Fetching:** Uses `OSMnx` to geocode administrative boundaries directly from OpenStreetMap.
- **Spatial Geometry:** Precise area calculations using local UTM projections.
- **Advanced Visualization:** High-fidelity static maps with `contextily` and interactive web-based maps with `folium`.
- **Data Persistence:** Exports spatial data to OGC GeoPackage format to maintain CRS integrity.

## Prerequisites
To run this notebook, the following Python libraries are required:
- `osmnx`: For OpenStreetMap data acquisition.
- `geopandas`: For vector data manipulation and spatial analysis.
- `contextily`: For adding basemaps to static plots.
- `folium`: For generating interactive leafet-based maps.
- `matplotlib`: For core data visualization.
- `shapely` & `networkx`: For geometry operations and graph analysis.

## Project Structure
The notebook automatically initializes the following directory structure to keep the workspace organized:
- `data/`: Stores raw and processed spatial data (e.g., `.gpkg` files).
- `outputs/`: Stores final artifacts, including the interactive HTML map.
- `outputs/figures/`: Stores exported static visualizations (e.g., `.png` files).

## Coordinate Reference Systems (CRS)
This project explicitly manages three different CRS types to ensure accuracy:
- **EPSG:4326 (WGS84):** The default global coordinate system (Latitude/Longitude) used for data fetching.
- **EPSG:3857 (Web Mercator):** Used for aligning data with web-based basemaps (Google Maps, CartoDB).
- **EPSG:32630 (UTM Zone 30N):** A projected coordinate system specifically chosen for **Accra, Ghana**.

## Visualization & Outputs
Below is an example of the interactive mapping capabilities developed in this workflow:

<img width="809" height="339" alt="INTERACTIVE" src="https://github.com/user-attachments/assets/9cf6d935-94a7-49fb-979e-190d6bc06cb2" />


## How to Use
1. **Environment Setup:** Run the first cell to install and verify all dependencies.
2. **Run All:** Execute the cells sequentially. The notebook will create necessary folders and fetch the boundary for Accra.
3. **Interactive View:** The final cell generates a Folium map. You can also find the standalone `chi_study_interactive.html` in the `outputs/` folder.
4. **Exports:** Check `outputs/figures/` for high-resolution map exports designed with a dark-themed aesthetic.
