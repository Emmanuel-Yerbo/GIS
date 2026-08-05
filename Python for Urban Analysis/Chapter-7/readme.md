

# Pedestrian Accessibility & The '15-Minute City' Framework
## Case Study: Greater Accra Healthcare & Service Infrastructure

### 1. Introduction: The Spatial Logic of Accessibility
In urban studies, **accessibility** is the primary metric of equity. This notebook implements an **Isochrone-based analysis** to evaluate the '15-Minute City' model within Accra, Ghana. An isochrone (a line of equal time) allows us to move beyond simple 'as-the-crow-flies' buffers and instead model the reality of the urban fabric—accounting for street connectivity, barriers, and walking speeds.

### 2. Methodological Pipeline

#### 2.1 Network Modeling (OSMnx & NetworkX)
- **The Process**: We fetch the OpenStreetMap (OSM) pedestrian graph (`G_walk`). 
- **The Essence**: Unlike driving networks, pedestrian networks must account for sidewalks and local paths. We assign a travel cost ('time') to every edge based on a standard walking speed of **4.5 km/h (1.25 m/s)**.

#### 2.2 Per-Facility Convex Hull Isochrones
- **The Process**: For every Point of Interest (POI), we traverse the graph using Dijkstra's algorithm to find all nodes reachable within specific time intervals (5, 10, 15, 20 mins).
- **The Essence**: We use a **Per-Facility Convex Hull** approach. By generating a hull for each hospital individually and then performing a spatial union, we preserve the 'organic' shape of service catchments and avoid the 'global hull' error that overestimates coverage in sparse areas.

### 3. Scenario Analysis: Urban Insights

#### Scenario 1: The Anchor Institution (Korle-Bu Spotlight)
- **Purpose**: Micro-scale analysis of Ghana’s premier teaching hospital.
- <img width="1389" height="1196" alt="image" src="https://github.com/user-attachments/assets/c8e3af2e-41eb-476f-9efa-886a154e0dd9" />

- **Insight**: Highlights the 'Gold Standard' of reach. The multi-ring visualization reveals how the immediate neighborhood is served versus the fringe, using callout annotations to orient the viewer.

#### Scenario 2: Facility Overlap & Clustering
- **Purpose**: Modeling 10 random healthcare POIs.
- <img width="1589" height="1101" alt="image" src="https://github.com/user-attachments/assets/fc7ea0cd-6ee9-4839-8c50-8ee65e069305" />

- **Insight**: This reveals the **co-location effect**. Where isochrones overlap significantly, we see service redundancy; where they are isolated, we see fragile access points.

#### Scenario 3: The 'Healthcare Desert' Identification
- **Purpose**: Citywide 15-minute coverage vs. the Study Area Boundary.
- <img width="1589" height="1098" alt="image" src="https://github.com/user-attachments/assets/1b9c4f87-4119-4fd6-a1a2-8c2d0376e481" />

- **Insight**: By calculating the `difference` between the district boundary and the 15-min unioned isochrone, we map 'Deserts'. These are the high-priority zones for future municipal investment.

#### Scenario 4: Multi-Category Comparison (Health, Education, Commerce)
- **Purpose**: Side-by-side analysis of different urban functions.
- <img width="2390" height="698" alt="image" src="https://github.com/user-attachments/assets/086cb682-e1b8-4d71-9cf5-876fd8ece600" />

- **Insight**: Urban livability is not just about hospitals. This scenario tests if a resident can access *all* three pillars (Health, Education, Markets) within the same 15-minute walk, identifying the 'Complete Neighborhoods' of Accra.

#### Scenario 5: Cumulative Accessibility Heatmap
- **Purpose**: Frequency analysis of node reachability.
- <img width="1589" height="1098" alt="image" src="https://github.com/user-attachments/assets/7129de25-ce6b-4182-9049-e26c2c4c4514" />

- **Insight**: We count how many different services can reach a single street node. This creates a **Density Heatmap**, shifting the focus from 'is there a clinic?' to 'how many choices does a citizen have?'.

#### Scenario 6: Dynamic Web Visualization (Pydeck)
- **Purpose**: High-fidelity interactive mapping.
- <img width="963" height="750" alt="image" src="https://github.com/user-attachments/assets/56848348-3e17-4583-9f99-34e9cbac556c" />

- **Insight**: Using WebGL-powered layers, we provide stakeholders with a 'zoomable' reality. The use of the Red Cross marker and tip labels translates abstract data into an intuitive tool for city planners.

### 4. Planning Implications
This analysis serves as a **Diagnostic Tool** for the Greater Accra Metropolitan Area. It confirms that while central Accra approximates 15-minute access, the peripheral expansion remains 'auto-dependent.' Transitioning these 'Deserts' into 'Complete Neighborhoods' is the core challenge for sustainable West African urbanism.
```
