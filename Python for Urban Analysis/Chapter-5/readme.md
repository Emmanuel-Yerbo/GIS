# Urban Analytics & Transportation: Accra Urban Profile Analysis

## 1. Executive Summary
This study provides a multi-dimensional spatial quantification of **Accra, Ghana**, utilizing high-resolution OpenStreetMap (OSM) data. By integrating building footprints, road network topology, and Point-of-Interest (POI) distributions, we identify a city defined by a dense monocentric core and rapidly expanding, less-integrated residential peripheries. This documentation serves as a structural baseline for calculating the city's future Livability Index.

## 2. Technical Methodology & Assumptions
- **Data Acquisition**: We utilized the `OSMnx` library to fetch geometry features. Building footprints were filtered for validity, and POIs were extracted based on a custom `AMENITY_TAGS` schema (covering health, education, and commerce).
- **Graph Projection & Geometry**: All spatial metrics, specifically building footprint areas ($m^2$), were calculated using **EPSG:32630 (UTM Zone 30N)** to ensure metric accuracy. For mapping and basemap integration, data was re-projected to **EPSG:3857**.
- **Outlier Management**: To visualize urban density effectively, we applied a **99th percentile filter** ($Q_{99} \approx 787.4 m^2$) to building footprints. This allows the visualization to focus on the dominant urban fabric rather than large industrial or institutional outliers.
- **Cartographic Composition**: The 'Hero Map' utilizes a layered alpha-blending technique: Leisure/Green space (Z=1) -> Buildings (Z=2) -> Roads (Z=3) -> Amenities (Z=5).

## 3. Empirical Findings

### 3.1 Network & Fabric Statistics
| Metric | Observed Value | Insight |
| :--- | :--- | :--- |
| **Total Building Footprints** | 228,528 | Indicates high-density informal and formal housing mixtures. |
| **Road Segments (Drivable)** | 46,661 | Highlights an extensive but often congested primary network. |
| **Points of Interest (POIs)** | 3,104 | Clustered primarily along major transit corridors. |
| **Green Space Features** | 72 | Reveals a critical scarcity of formal leisure zones. |

### 3.2 Morphology Observations
- **Building Density**: The analysis of footprint areas shows a high concentration of small-scale structures. The 'Buildings by Area' panel confirms that smaller footprints dominate the central business district (CBD) and surrounding residential zones.
- **Road Hierarchy**: The network shows high connectivity in central Accra, but connectivity drops significantly as we move toward the peri-urban boundary, where 'drivable' paths are restricted to few main arteries.
- **Amenity Distribution**: POIs (Hospitals, Markets, Schools) show a heavy 'linear' clustering pattern along the GAMA (Greater Accra Metropolitan Area) transport spines, leaving significant residential interior zones as 'service deserts.'

## 4. Visual Evidence: Digital Cartography
Our analysis produced two primary visual artifacts to support these findings:
- **The 2x2 Dashboard (`ch5_urban_profile.png`)**: Deconstructs the city into four specific layers, allowing for a comparative view of how infrastructure density (Roads) aligns with socio-economic activity (POIs).
- <img width="1990" height="1776" alt="download (3)" src="https://github.com/user-attachments/assets/33f23d2a-b850-4b87-96e6-b2d007e363cd" />

- **The Hero Map (`ch5_hero_map.png`)**: A composite 'single-canvas' visualization. It effectively highlights the **Green Space Gap** and the dominance of the **Primary Road Artery** in structuring the city's movement.
- <img width="1790" height="1237" alt="download (4)" src="https://github.com/user-attachments/assets/3b200daa-8da6-4d22-ba43-2fe39a138c67" />


## 5. Planning Implications
1. **Arterial Pressure**: The concentration of amenities and primary roads creates extreme pressure points. Planning should focus on 'secondary connectivity' to distribute traffic flow away from the central hubs.
2. **The 'Green Gap'**: With only 72 identified leisure/green space features for over 200,000 buildings, Accra faces a significant deficit in public urban lungs. Zoning for 'Green Belts' is a priority.
3. **Spatial Inequality**: The disparity between the dense core infrastructure and the sparse peripheral amenities suggests that future growth must be managed via 'Sub-Centric' development to bring services closer to the residents.
