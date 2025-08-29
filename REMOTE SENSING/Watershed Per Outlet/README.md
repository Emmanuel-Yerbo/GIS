# Watershed Per Outlet Analysis: Sawla-Tuna-Kalba District, Ghana

## Overview

This project focuses on delineating watershed areas for various outlets within the Sawla-Tuna-Kalba District in Ghana. A **watershed** is an area of land that drains all rainfall and streams to a common outlet, such as a reservoir outflow, river mouth, or any point along a stream channel. An **outlet** is the specific point where water exits the watershed.

Understanding watershed boundaries and their catchment areas is crucial for effective water resource management, flood risk assessment, and sustainable environmental planning.

---

## Project Aim

To estimate the total drainage area (watershed) contributing to each outlet within the Sawla-Tuna-Kalba District.

---

## Data and Methods

### Data Source
- **SRTM Digital Elevation Model (DEM):** Shuttle Radar Topography Mission data used to model terrain elevation.

### Methodology Steps
1. **DEM Fill:** Fill sinks in the DEM to remove spurious depressions that can disrupt flow modeling.
2. **Flow Direction:** Calculate the direction of water flow from each cell based on the DEM.
3. **Flow Accumulation:** Compute the number of upstream cells draining into each cell to identify stream networks.
4. **Reclassify to Extract Rivers:** Using a threshold on flow accumulation, extract river channels from the DEM.
5. **Outlet Creation:** Generate outlet points randomly placed along the stream network to define points of interest for watershed delineation.
6. **Watershed Per Outlet:** Delineate individual watersheds draining into each outlet using flow direction data.

---

## Results
### Table for Result
| Catchment | Watershed Area (km²) |
|-----------|----------------------|
| A         | 1,405                |
| B         | 186                  |
| C         | 1,432                |
| D         | 146                  |

### Graph as Result
![Picture1](https://github.com/user-attachments/assets/45ef081f-b2fd-45cd-ae7c-8776a2b2e8d3)

## Map as Result
#![Outlet](https://github.com/user-attachments/assets/d37779ea-bdda-444c-9c16-044e1f00b655)

---

## Applications

- **Water Resource Allocation:** Accurately defining watershed boundaries helps allocate water resources efficiently among communities and sectors.
- **Flood Risk Management:** Understanding catchment sizes and flow paths aids in predicting flood-prone areas and planning mitigation strategies.
- **Sustainable Water Management:** Watershed delineation supports integrated water resources management, ensuring long-term sustainability of water availability.

---

## Importance of This Study

This analysis underscores the critical role of watershed delineation in optimizing resource allocation, managing flood risks, and supporting sustainable water management practices in the Sawla-Tuna-Kalba District. By leveraging DEM-based hydrological modeling, local authorities and stakeholders can better understand the spatial distribution of water flow and make informed decisions toward environmental stewardship and community resilience.
