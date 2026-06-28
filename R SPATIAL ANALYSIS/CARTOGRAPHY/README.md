# VIIRS Nighttime Lights Mapping & Spatial Analysis of Ghana

An advanced geospatial cartography project analyzing urban infrastructure density, socioeconomic distribution, and transportation corridors in Ghana using NASA’s VIIRS (Visible Infrared Imaging Radiometer Suite) Black Marble nighttime lights data.

<p align="center">
  <img src="https://github.com/user-attachments/assets/5891939c-bfdc-450b-95b2-990bac476246" width="600" alt="Ghana Nighttime Lights Map" />
</p>



---

## 1. Project Overview
Nighttime light (NTL) remote sensing serves as a direct proxy for human activity, economic development, and electrical grid infrastructure. This project establishes a robust spatial pipeline in R to process, transform, and visualize NASA's Black Marble annual composite data for Ghana. It produces two distinct cartographic outputs:
1. **A publication-grade static visualization** utilizing high-contrast, dark-mode cartography to map urban core networks.
2. **An interactive web GIS overlay** (via OpenStreetMap and CartoDB) designed for zoomable spatial exploration.

---

## 2. Data Sources

### NASA Black Marble VIIRS DNB (VNP46A4 / NOAA VCMSLCFG)
*   **Sensor:** Visible Infrared Imaging Radiometer Suite (VIIRS) Day/Night Band (DNB) aboard the Suomi National Polar-orbiting Partnership (Suomi-NPP) satellite.
*   **Product Type:** Annual VNP46A4 / Monthly NOAA VCMSLCFG composite (2023).
*   **Resolution:** 15 arc-seconds (~463 meters at the equator).
*   **Correction Algorithms:** Preprocessed to correct for atmospheric effects, terrain reflections, lunar bidirectional reflectance distribution function (BRDF), stray light, and cloud contamination, leaving a stable, long-term radiance baseline of human settlement lights.
*   **Administrative Boundaries:** GADM (Database of Global Administrative Areas), retrieved at Level 0 (Country outline).

---

## 3. Preprocessing & Methodological Framework

The processing pipeline is implemented in R using the `sf` and `terra` libraries. It follows a structured workflow to handle the massive dynamic range of satellite nighttime radiance:

### Workflow:
1. **GADM Boundary Retrieval:** Load the administrative boundary of Ghana.
2. **GEE Data Query:** Load the 2023 median composite TIFF file.
3. **Spatial Clip & Mask:** Crop the raster to the exact coastline and borders of Ghana.
4. **Background Noise Clamping:** Set negative values (< 0) to exactly 0 to eliminate sensor noise.
5. **Logarithmic Scaling:** Apply a log-transformation to compress high-radiance spikes in urban cores and highlight rural grid infrastructure:
   ```
   Luminosity Index = ln(Radiance + 1)
   ```
6. **Cartographic Styling:** Map the values using a custom color ramp (deep space violet -> orange -> gold -> white) on a pitch-black background (`#06060c`).

---

## 4. Key Spatial Results & Insights

The processed output provides an intuitive view of Ghana's spatial structure, highlighting several distinct features:

*   **The Coastal Economic Belt:** The Accra-Tema metropolitan area dominates the southern coast with the highest radiance values, extending westward toward Cape Coast and Takoradi. This reflects the intense concentration of industrial activity, urbanization, and port infrastructure.
*   **The Triangle Corridor:** A clear spatial corridor connects Accra, Kumasi (the Ashanti regional capital), and the coastal ports, forming the economic backbone of southern Ghana.
*   **The Northern Hub (Tamale):** Tamale stands out as a highly centralized star-burst of light in the northern savanna region, acting as a crucial regional trading and logistics hub.
*   **Secondary Cities and Roads:** The log-scaled map clearly visualizes the highway networks connecting secondary towns like Sunyani, Techiman, Bolgatanga, and Wa, outlining the physical structure of regional connectivity.
*   **Rural-Urban Contrast:** A stark contrast exists between the highly illuminated southern third of the country and the sparsely lit northern savanna, illustrating differences in population density, urban expansion, and electrical grid extension.

---

## 5. Developmental & Policy Implications

*   **Tracking Electrification:** The visualization serves as a tool to verify the progress of the National Electrification Scheme (NES), helping policy makers identify unlit pockets in rural districts.
*   **Socioeconomic Proxy:** Changes in nighttime light intensity over time are highly correlated with GDP growth, local household wealth, and urbanization rates, providing a fast, non-survey-based economic monitoring method.
*   **Disaster Resilience & Energy Planning:** The baseline map can be used in combination with real-time imagery to monitor power grid stability, detect blackouts during climate events, and assess regional energy consumption.
*   **Conservation & Light Pollution:** The data maps the encroachment of artificial light into ecological reserves and national parks, indicating zones where light pollution may affect nocturnal wildlife.

---

## 6. How to Reproduce

### Prerequisites
Ensure you have the required R packages installed:
```R
install.packages(c("tidyverse", "sf", "terra", "tidyterra", "geodata", "leaflet", "raster"))
```

### Setup and Run
1.  Open RStudio.
2.  Place your Google Earth Engine exported file `ghana_viirs_2023.tif` inside the `data/` folder.
3.  Open and run the master R script:
    `visualize_ghana_nightlights.R`
4.  The script will export a print-ready static map into `output/` and render the zoomable interactive map in your RStudio Viewer pane.
