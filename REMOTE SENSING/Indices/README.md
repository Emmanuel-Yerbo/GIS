# 🌿 Multispectral Indices & Phenological Earth Observation
## Case Study: Multi-Temporal Vegetation Dynamics & Spectral Trajectories Across Ghana

[![Google Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-API-34A853?logo=google-earth&logoColor=white)](https://earthengine.google.com/)
[![Sentinel-2](https://img.shields.io/badge/Sentinel--2-L2A%2010m-003399)](https://sentinels.copernicus.eu/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)

> **Lead Researcher & Engineer:** **Emmanuel Yerbo**  
> *BSc Geography & Regional Planning (First Class Honours, GPA: 3.82/4.00, Three-Time Dean's Award Recipient) — University of Cape Coast, Ghana*  
> 🆔 [ORCID: 0009-0008-8968-6999](https://orcid.org/0009-0008-8968-6999) | 💼 [LinkedIn](https://www.linkedin.com/in/emmanuelyerbo) | 💻 [GitHub Profile](https://github.com/Emmanuel-Yerbo) | 🌐 [Interactive Portfolio](https://emmanuelyerbo.github.io/emmanuelyerbo)

---

### 📌 Overview
This module demonstrates the calculation and temporal trajectory analysis of key Earth Observation multispectral indices derived from Sentinel-2 MSI and Landsat 8/9 Collection 2:

1. **Normalized Difference Vegetation Index (NDVI):**
   $$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$$
2. **Normalized Difference Red Edge (NDRE):**
   $$\text{NDRE} = \frac{\text{NIR} - \text{RedEdge}}{\text{NIR} + \text{RedEdge}}$$
3. **Enhanced Vegetation Index (EVI):**
   $$\text{EVI} = 2.5 \times \frac{\text{NIR} - \text{Red}}{\text{NIR} + 6.0 \cdot \text{Red} - 7.5 \cdot \text{Blue} + 1}$$
4. **Modified Normalized Difference Water Index (MNDWI):**
   $$\text{MNDWI} = \frac{\text{Green} - \text{SWIR}}{\text{Green} + \text{SWIR}}$$
