# Urban Analytics & Transportation: Accra Road Network Analysis

## 1. Executive Summary
This study quantifies the structural and functional topology of **Accra, Ghana**, utilizing OpenStreetMap (OSM) data. By comparing the 'Drivable' and 'Walkable' layers, we identify a city defined by high pedestrian permeability but significant vehicular bottlenecks. The analysis provides empirical evidence for transport interventions based on network centrality and road hierarchy.

## 2. Technical Methodology & Assumptions
- **Data Source**: OSM geometries for the 'Accra, Ghana' boundary.
- **Graph Projection**: All spatial metrics are calculated in **EPSG:32630 (UTM Zone 30N)** for metric accuracy.
- **Centrality Assumption**: Due to the computational complexity of exact Betweenness Centrality ($O(V^3)$), we utilized an **approximate calculation** using a sample of $k=500$ nodes. Shortest paths were weighted by `travel_time` (calculated via imputed edge speeds).

## 3. Empirical Findings

### 3.1 Network Topology Comparison
| Metric | Drivable Network | Walkable Network |
| :--- | :--- | :--- |
| **Nodes (Intersections)** | 18,823 | 37,080 |
| **Edges (Segments)** | 46,672 | 93,594 |
| **Avg. Circuity** | 1.04 | 1.06 |
| **Connectivity ($k_{avg}$)** | 4.96 | 5.05 |
<img width="2390" height="820" alt="COMPARE" src="https://github.com/user-attachments/assets/c61acd13-95c6-4d44-aed8-bf6dad4677ab" />

**Key Insight**: The walkable network is nearly **2x as dense** as the drivable network. While vehicles are restricted to formal arteries, the pedestrian logic of Accra suggests a much finer-grained connectivity that utilizes informal paths and narrow connectors.

### 3.2 Network Hubs (Betweenness Centrality)
Our analysis identified specific 'structural bottlenecks' where the city's traffic flow is most concentrated. The top nodes by Betweenness Centrality ($BC$) are:
1. **Node 12486742677** ($BC=0.1737$)
2. **Node 12486742689** ($BC=0.1736$)
3. **Node 1984328632** ($BC=0.1349$)

<img width="1105" height="866" alt="CENTRALITY" src="https://github.com/user-attachments/assets/2016d3c0-855b-4943-84b0-6fff540af757" />

These hubs, concentrated around the primary arteries, represent points where network failure or localized congestion would have the greatest city-wide impact.

### 3.3 Functional Hierarchy & Road Classification
The road network is heavily skewed toward secondary connectivity:
- **Residential/Unclassified**: ~39,291 segments (The vast majority of the network).
- **Primary/Trunk**: ~1,208 segments.
- **Motorway**: Only 18 segments identified.

<img width="1389" height="967" alt="ROADTYPE" src="https://github.com/user-attachments/assets/3b2a1bc8-4fb6-4d19-9a3a-84bd9267dc30" />

**Visual Finding**: The Road Type Map highlights a lack of 'Arterial Redundancy.' High traffic volumes are forced from residential zones onto a very small number of primary/trunk connectors, creating the high-centrality 'hotspots' observed in our hub analysis.

## 4. Planning Implications
The high circuity and low density of the drivable network relative to the walkable fabric indicate that Accra's vehicular movement is inefficient. Urban planning efforts should prioritize the 'Missing Middle' of the road hierarchy and reinforce the identified high-centrality hubs to alleviate systemic congestion.
