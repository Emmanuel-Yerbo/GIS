# NDVI Calculation Using Sentinel-2 Imagery in Google Earth Engine

## Overview

This project demonstrates how to calculate the **Normalized Difference Vegetation Index (NDVI)** from Sentinel-2 satellite imagery using Google Earth Engine (GEE). The workflow includes cloud masking, compositing images over a date range, and visualizing both a true color composite and the NDVI layer.

---

## What is NDVI?

NDVI stands for **Normalized Difference Vegetation Index**. It is a widely used remote sensing index that measures the presence and condition of green vegetation on the Earth's surface. NDVI values range from -1 to +1, where:

- Values close to +1 (e.g., 0.8 - 1) indicate dense, healthy green vegetation.
- Values near 0 suggest bare soil, urban areas, or sparse vegetation.
- Negative values typically represent water, clouds, or snow.

NDVI is a crucial indicator in agricultural monitoring, forestry, ecosystem management, and environmental studies as it helps assess plant health, biomass, and vegetation cover.

---

## Bands Used in NDVI Calculation

NDVI is calculated using the following spectral bands from Sentinel-2 imagery:

- **Near Infrared (NIR) band:** `B8` (in this script, the 15th percentile composite is labeled `B8_p15`)
- **Red band:** `B4` (in this script, labeled `B4_p15`)

The formula for NDVI is:
## NDVI = (NIR - Red) / (NIR + Red)

Where `NIR` corresponds to the reflectance in the near-infrared band and `Red` corresponds to the reflectance in the red visible band

## Applications of NDVI
- Agriculture: Monitoring crop health, detecting stress, and estimating yields.
- Forestry: Assessing forest cover, health, and biomass.
- Environmental Monitoring: Tracking droughts, desertification, and land degradation.
- Urban Planning: Assessing green spaces and urban vegetation.
- Climate Studies: Understanding vegetation responses to climate change.

## Output 
![Layout3](https://github.com/user-attachments/assets/c098406f-31b7-4d60-9624-5540695d8cee)


## CODE SECTION
```javascript
// Cloud masking function using QA60 band
function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;

  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
      .and(qa.bitwiseAnd(cirrusBitMask).eq(0));

  return image.updateMask(mask).divide(10000);
}

// Create composite from Sentinel-2 data
var composite = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterDate('2024-01-01', '2024-12-31')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .map(maskS2clouds)
                  .map(function(image) {
                    return image.clip(roi);
                  })
                  .reduce(ee.Reducer.percentile([15]));

// Visualization parameters for true-color composite
var visualization = {
  min: 0.0308,
  max: 0.2763,
  bands: ['B4_p15', 'B3_p15', 'B2_p15'],
};

Map.centerObject(roi, 12);
Map.addLayer(composite, visualization, 'RGB Composite');

// Calculate NDVI using NIR and Red bands
var ndvi = composite.normalizedDifference(['B8_p15', 'B4_p15']).rename('NDVI');
Map.addLayer(ndvi, {min: 0, max: 1, palette: ['red', 'green']}, 'NDVI');

