
# Urban Analytics & Transportation: Greater Accra Livability Index Analysis

## 1. Executive Summary
This final study transitions from individual urban layers to a **Composite Livability Index** across all 29 Metropolitan, Municipal, and District Assemblies (MMDAs) of the **Greater Accra Region, Ghana**. By synthesizing amenity density, building fabric, road connectivity, and green space ratios, we have quantified the spatial inequality of urban services. The findings reveal a stark hierarchy: **Accra Metropolitan District (AMA)** serves as the high-functioning core (Score: 0.93), while peripheral districts like **Shai-Osudoku** and **Ada West** represent infrastructure frontiers with near-zero scores, highlighting a critical need for decentralized urban investment.

## 2. Technical Methodology & Assumptions
- **Indicator Selection**: Four pillars were selected to represent urban quality: *Amenity Density* (Social Infra), *Building Density* (Urban Fabric), *Road Density* (Mobility), and *Green Ratio* (Environmental Quality).
- **Scaling & Normalization**: To compare disparate units (e.g., km of road vs. count of schools), we employed **Min-Max Normalization**:
  $$x_{norm} = \frac{x - x_{min}}{x_{max} - x_{min}}$$
  This maps all values to a $[0, 1]$ range, where 1 represents the regional maximum and 0 the minimum.
- **Composite Scoring**: An unweighted arithmetic mean of the normalized indicators was used to derive the final **Livability Score**. This assumes equal importance across all four urban dimensions for a baseline assessment.
- **Geospatial Processing**: Boundary geometries were fetched via `OSMnx` and projected to **EPSG:32630 (UTM Zone 30N)** for precise area and distance calculations before being mapped in Web Mercator for visualization.

## 3. Empirical Findings

### 3.1 Regional Rank & Score Distribution (Top 5)
| Rank | District | Livability Score | Key Driver |
| :--- | :--- | :--- | :--- |
| **1** | Accra Metropolitan | 0.931 | Maximum Amenity & Building Density |
| **2** | Ablekuma Central | 0.642 | Peak Road Network Density |
| **3** | Ablekuma North | 0.595 | High Connectivity & Fabric Density |
| **4** | Tema Metropolitan | 0.483 | Significant Green Space & Planned Grid |
| **5** | Ga East | 0.230 | Emerging Secondary Infrastructure Hub |

### 3.2 The Infrastructure Divide
- **The Core Superiority**: The top 3 districts (Accra Metro, Ablekuma Central/North) significantly outperform the rest of the region. Accra Metro, in particular, achieved a perfect 1.0 in amenity and building density normalization, setting a benchmark that other districts fail to reach by a margin of over 60%.
- **Road Density as a Lead Indicator**: Ablekuma Central outperformed the regional capital in road density (1.0 vs 0.72), suggesting a more permeable local grid compared to the historic core.
- **The Periphery Desert**: Districts like **Ningo-Prampram** and **Shai-Osudoku** show normalized scores near zero across multiple categories, indicating that while they have large land areas, their functional urban service levels are virtually non-existent compared to the core.

## 4. Visual Evidence: Regional Choropleth
Our analysis produced the **Greater Accra Livability Map**, which serves as a heat map for regional development:
- **Hotspots (Green)**: Concentrated strictly within the Accra-Tema corridor.
- **Cold Zones (Red/Yellow)**: The vast majority of the region's land area, particularly to the North and East, remains in the 'Red' zone of the livability index.
- **Visual Artifact**: `outputs/figures/ch6_livability_index.png` provides the spatial proof of the **Monocentric Growth Pattern** currently dominating Ghana's capital region.
- <img width="1790" height="947" alt="download (5)" src="https://github.com/user-attachments/assets/34cbd6ab-ad91-47b4-ac08-da0a5bec3395" />


## 5. Planning Implications (Professor's Review)
1. **Aggressive Decentralization**: The data confirms that 'urbanity' in Greater Accra is a scarce resource concentrated in less than 10% of its districts. Planning policy must incentivize the 'Amenity-Led Development' of secondary hubs in Ga South and Ga West to prevent the total collapse of core infrastructure under migration pressure.
2. **The Green Space Crisis**: Even in high-scoring districts, the `green_ratio` remains the lowest performing indicator. Urban livability in Accra is currently being 'bought' at the expense of environmental cooling and public leisure space.
3. **Resilience Strategy**: The extreme scores in the core vs the periphery suggest a fragile system. If the core (AMA) faces a climate or infrastructure shock, the surrounding districts lack the 'service redundancy' to support the population. Bridging the 0.9 to 0.2 score gap is the primary challenge for the next decade of Ghanaian urbanism.
