# Deriving Land Surface Temperature (LST) using Landsat Imagery

## Project Overview
This project leverages **Landsat 5, 8, and 9** satellite imagery to analyze the spatiotemporal evolution of Land Surface Temperature (LST) in **Accra, Ghana**, over a 34-year period. By quantifying the rise in surface temperature, this study identifies critical "hot spots" and tracks the intensifying **Urban Heat Island (UHI)** effect in one of Africa's fastest-growing metropolitan areas.

## Importance of Land Surface Temperature (LST)
Land Surface Temperature (LST) is a key parameter in various scientific and environmental studies. It provides critical insights into the Earth's surface energy balance, environmental dynamics, and climate change. Unlike air temperature, LST measures the physical warmth of the "skin" of the Earth, making it a more direct indicator of how different land covers (e.g., asphalt vs. forest) interact with solar radiation.

## Why Study LST in Accra?
Monitoring LST in Accra is not just a scientific exercise; it is a critical necessity for urban resilience and public health.

### 1. Rapid Urbanization and Vegetation Loss
Accra has undergone massive spatial expansion since the 1980s. Natural landscapes and wetlands have been replaced by impervious surfaces like concrete and asphalt. These materials absorb solar radiation and re-emit it as heat, leading to significantly higher surface temperatures than the surrounding rural areas.

### 2. Public Health and Heat Stress
As LST rises, the risk of heat-related illnesses (heat stroke, respiratory issues, and cardiovascular stress) increases for the city's residents. This study helps identify the most vulnerable neighborhoods that require immediate intervention, such as "cool roof" initiatives or tree-planting programs.

### 3. Energy Consumption
Higher surface temperatures correlate directly with increased demand for air conditioning and refrigeration. Understanding LST patterns is vital for energy planning and promoting sustainable, energy-efficient building designs in the tropics.

### 4. Climate Change Mitigation
Cities are at the forefront of climate change. By documenting the rise from **~26°C in 1986 to over ~39°C in 2020**, this project provides the empirical data needed for local policymakers to integrate "Nature-Based Solutions" (NBS) into the Accra Metropolitan Assembly’s urban planning framework.

---

## Workflow Overview
The derivation follows a sequence from raw data (DN) to radiance, then to brightness temperature, and finally to emissivity-corrected Land Surface Temperature.

### 1. Conversion of Digital Numbers (DN) to TOA Radiance
The first step is converting the raw quantized pixel values (Digital Numbers) into Top-of-Atmosphere (TOA) spectral radiance ($L_\lambda$).

**Formula:**
$$L_\lambda = M_L \cdot Q_{cal} + A_L$$

*   $L_\lambda$: TOA spectral radiance ($W/(m^2 \cdot sr \cdot \mu m)$).
*   $M_L$: Radiance multiplicative scaling factor (from metadata).
*   $A_L$: Radiance additive scaling factor (from metadata).
*   $Q_{cal}$: Standard product pixel values (DN).

**Importance:**
This step normalizes the data. Satellite sensors record light intensity as arbitrary numbers (0–255 or 0–65535). Converting to radiance ensures the measurements are in physical units of energy, allowing for comparison between different dates and sensors.

---

### 2. Conversion to Top-of-Atmosphere Brightness Temperature (BT)
Thermal radiance is converted into Brightness Temperature, which is the temperature of a blackbody emitting the same amount of radiation.

**Formula:**
$$BT = \frac{K_2}{\ln\left(\frac{K_1}{L_\lambda} + 1\right)}$$

**Sensor-Specific Constants ($K_1$ and $K_2$):**

| Sensor | Thermal Band | $K_1$ Constant | $K_2$ Constant |
| :--- | :--- | :--- | :--- |
| **Landsat 5 TM (1986)** | Band 6 | 607.76 | 1260.56 |
| **Landsat 8 TIRS (2017/2020)** | Band 10 | 774.89 | 1321.08 |
| **Landsat 9 TIRS-2 (2020+)** | Band 10 | 799.03 | 1329.03 |

**Importance:**
$BT$ provides a "raw" temperature in Kelvin. However, it assumes the Earth is a perfect "blackbody" (which it isn't), necessitating further correction for surface emissivity.

---

### 3. NDVI and Proportion of Vegetation ($P_v$)
To correct for surface emissivity, we must first understand the land cover. In urban areas like Accra, the mix of vegetation and concrete significantly affects heat retention.

**NDVI Formula:**
$$NDVI = \frac{NIR - RED}{NIR + RED}$$
*(Landsat 5: B4 & B3; Landsat 8/9: B5 & B4)*

**Proportion of Vegetation ($P_v$):**
$$P_v = \left( \frac{NDVI - NDVI_{min}}{NDVI_{max} - NDVI_{min}} \right)^2$$

**Importance:**
$P_v$ quantifies how much of a pixel is covered by vegetation versus bare soil or man-made surfaces. This is the foundation for calculating emissivity.

---

### 4. Land Surface Emissivity (LSE) Calculation
Emissivity ($\varepsilon$) is the efficiency with which a surface emits thermal energy. Different materials (asphalt, grass, water) emit heat differently.

**Formula (Sobrino et al.):**
$$\varepsilon = 0.004 \cdot P_v + 0.986$$

**Importance:**
Without emissivity correction, urban surfaces (which have lower emissivity than forests) would appear cooler than they actually are. This step is vital for capturing the true intensity of the **Urban Heat Island** in Accra.

---

### 5. Final Land Surface Temperature (LST) Calculation
The final LST is calculated by correcting the Brightness Temperature with the calculated Emissivity and converting the result to Celsius.

**Formula:**
$$LST (°C) = \left( \frac{BT}{1 + \left( \frac{\lambda \cdot BT}{\rho} \right) \ln(\varepsilon)} \right) - 273.15$$

*   $\lambda$: Wavelength of emitted radiance (approx. $11.5 \mu m$ for L5; $10.8 \mu m$ for L8).
*   $\rho$: $h \cdot c / \sigma$ (approx. $14380 \mu m K$).

<p align="center">
  <img src="https://github.com/user-attachments/assets/6fd255db-9200-4fb0-b166-ba5c68159c8a" width="800" alt="LST Analysis Accra">
</p>

## Summary for Accra
Based on the maps produced, a clear and alarming trend is evident in Accra’s thermal environment:

1.  **Temporal Warming Trend**: There is a staggering **13.48°C increase** in peak Land Surface Temperature (LST) over the 34-year study period. The maximum recorded temperature rose from **25.83°C in 1986** to **39.31°C in 2020**.
2.  **Disappearance of Cool Islands**: In the 1986 map, several "cool islands" (represented in green/yellow-green) are visible, particularly in the western and coastal zones. By 2020, these cooler areas have largely disappeared or become highly fragmented, indicating a loss of urban vegetation and wetlands.
3.  **Core-to-Periphery Intensification**: The heat intensity (visible in deep red) was initially confined to small pockets in the inland areas in 1986. However, by 2017 and 2020, these hot zones have merged and expanded to cover the majority of the central and eastern metropolitan area, reflecting the densification of built-up environment.
4.  **Baseline Temperature Shift**: Not just the peaks, but the "baseline" (minimum) temperatures have also risen. The minimum LST increased from **18.83°C in 1986** to **22.96°C in 2020**, suggesting that even the city's cooler areas are now warmer than they were thirty years ago.
