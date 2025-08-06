# Flood Risk Mapping in the Volta Region, Ghana

This repository contains a Google Earth Engine (GEE) script to model flood susceptibility in the Volta region of Ghana using a multi-criteria weighted overlay analysis. The analysis combines land cover, elevation, slope, distance to open water, height above nearest drainage, and flood frequency data to produce a flood risk map.

---

## Overview

Flooding is a significant hazard in many regions, including Ghana's Volta region. This project leverages remote sensing datasets and terrain analysis to assess flood susceptibility. The workflow integrates multiple environmental factors known to influence flooding risk.

---

## Data Sources

- **ESA WorldCover 2020** (`ESA/WorldCover/v100`): Global land cover classification used for land use/land cover (LULC) data.
- **SRTM Global 1 Arc-Second DEM** (`USGS/SRTMGL1_003`): Elevation data used to derive elevation classes and slope.
- **MERIT Hydro Dataset** (`MERIT/Hydro/v1_0_1`): Height Above Nearest Drainage (HAND) data.
- **JRC Global Surface Water (GSW) Monthly History** (`JRC/GSW1_0/MonthlyHistory`): Historical surface water occurrence to estimate flood frequency.

---

## Methodology

1. **Land Cover Reclassification**  
   The ESA WorldCover classification is remapped into four classes representing different flooding susceptibilities:
   - 1: Trees, shrubland (low susceptibility)
   - 2: Grassland, cropland
   - 3: Built-up, barren
   - 4: Open water, wetlands, mangroves (high susceptibility)

2. **Elevation Reclassification**  
   Elevation values from SRTM are reclassified into four classes based on elevation ranges, where lower elevations have higher flooding susceptibility.

3. **Slope Reclassification**  
   Terrain slope is derived from SRTM and reclassified into four classes, with flatter slopes more susceptible to flooding.

4. **Distance to Open Water**  
   Distance to open water bodies is calculated using the ESA WorldCover water class, and distances are reclassified such that proximity to water corresponds to higher flood risk.

5. **Height Above Nearest Drainage (HAND)**  
   HAND data are reclassified to represent relative susceptibility, with lower HAND values indicating higher flood risk.

6. **Flood Frequency**  
   Using JRC monthly surface water data from 2000 to 2024, flood frequency is calculated as the percentage of observations with water presence.

7. **Weighted Overlay Analysis**  
   All reclassified layers are combined using a weighted sum expression with the following weights based on their influence on flood risk:
   - Flood Frequency: 2.5
   - Land Cover: 2.0
   - Elevation: 2.5
   - Slope: 2.5
   - Distance to Open Water: 1.5
   - HAND: 1.5

---
8. **Output with ArcGIS PRO**
   ![TTTT](https://github.com/user-attachments/assets/36e6d224-ef2c-4996-9e58-2ddc832eabd7)

## Acknowledgments

Thanks to the Google Earth Engine team and contributors of the datasets used.

## Code Section

```javascript
// Define your region of interest (roi) before running the script
// var roi = ee.Geometry.Polygon([...]);

// Load and reclassify ESA WorldCover land cover map
var lulc = ee.ImageCollection('ESA/WorldCover/v100')
    .first()
    .select('Map')
    .remap(
      [10, 20, 30, 40, 50, 60, 80, 90, 95],  // original classes
      [1, 1, 2, 2, 3, 3, 4, 4, 4]             // reclassified classes
    );

// Classes:
// 1 - Trees, shrubland (low flooding susceptibility)
// 2 - Grassland, cropland
// 3 - Built-up, barren
// 4 - Open water, herbaceous wetland, mangroves (high flooding susceptibility)

var landcover = lulc.clip(roi);
Map.centerObject(roi, 10);
print(landcover);

// Visualization for land cover
var vis = {
  bands: ['remapped'],
  palette: ['4be450', 'f096ff', 'fa0000', '0064c8']
};
Map.addLayer(landcover, vis, 'Land Cover');

// Load SRTM elevation data
var STRM = ee.Image("USGS/SRTMGL1_003");
var elev = STRM.clip(roi);

// Reclassify elevation:
// 1 = 1201m - 2600m (low susceptibility)
// 2 = 651m - 1200m
// 3 = 301m - 650m
// 4 = 0m - 300m (high susceptibility)
var elev_reclass = ee.Image(0).rename('elevation')
    .where(elev.gt(1201).and(elev.lte(2600)), 1)
    .where(elev.gt(651).and(elev.lte(1200)), 2)
    .where(elev.gt(301).and(elev.lte(650)), 3)
    .where(elev.gt(0).and(elev.lte(300)), 4);

var palettes = require('users/gena/packages:palettes');
var palette = palettes.cmocean.Solar[7];

Map.addLayer(elev_reclass.clip(roi), {min: 1, max: 4, palette: palette}, 'Elev Reclass', false);

// Derive slope from SRTM and reclassify slope:
// 1 = 19-78 degrees (low susceptibility)
// 2 = 5-18
// 3 = 2.5-4
// 4 = 0-2.4 (high susceptibility)
var slope = ee.Terrain.slope(STRM).clip(roi);
var slope_reclass = ee.Image(1).rename('slope')
  .where(slope.gt(19).and(slope.lte(78)), 1)
  .where(slope.gt(5).and(slope.lte(18)), 2)
  .where(slope.gt(3).and(slope.lte(4)), 3)
  .where(slope.gt(0).and(slope.lte(2)), 4);

Map.addLayer(slope_reclass.clip(roi), {min:1, max:4, palette:palette}, 'Slope Reclass', false);

// ESA classes for open water reclassification
var open_w = ee.ImageCollection('ESA/WorldCover/v100')
    .first()
    .select('Map')
    .remap([10, 20, 30, 40, 50, 60, 80, 90, 95], [0, 0, 0, 0, 0, 0, 1, 0, 0]);

// Compute euclidean distance to open water areas (up to 10km)
var ow = open_w.select('remapped')
  .distance({kernel: ee.Kernel.euclidean(10000, 'meters'), skipMasked: false})
  .rename('distance')
  .clip(roi);

print('Distance to Open water', ow);

// Visualization for distance to open water
var ow_vis = {
  opacity: 1,
  bands: ['distance'],
  max: 10000.2,
  palette: ['22ff20', '1a35ff', 'ffa925', 'ff0a36', '2fe1ff', 'fd4bff']
};
Map.addLayer(ow, ow_vis, 'Distance to Open Water');

// Distance to water reclassification:
// 1 = 801-10000m (low susceptibility)
// 2 = 401-800m
// 3 = 201-400m
// 4 = 0-200m (high susceptibility)
var ow_reclass = ee.Image(0).rename('dist')
  .where(ow.gt(4001).and(ow.lte(10000)), 1)
  .where(ow.gt(801).and(ow.lte(4000)), 2)
  .where(ow.gt(401).and(ow.lte(800)), 3)
  .where(ow.gt(0).and(ow.lte(400)), 4);

Map.addLayer(ow_reclass.clip(roi), {min:1, max:4, palette:palette}, 'Distance to OW', false);

// Load MERIT Hydro Height Above Nearest Drainage (HAND)
var hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').clip(roi);

// Reclassify HAND:
// 1 = 89-1800m (low susceptibility)
// 2 = 29-90m
// 3 = 9-30m
// 4 = 0-8m (high susceptibility)
var hand_reclass = ee.Image(1).rename('hnd')
  .where(hand.gt(89).and(hand.lte(1800)), 1)
  .where(hand.gt(29).and(hand.lte(90)), 2)
  .where(hand.gt(9).and(hand.lte(30)), 3)
  .where(hand.gt(0).and(hand.lte(8)), 4);

Map.addLayer(hand_reclass.clip(roi), {min:1, max:4, palette:palette}, 'Hand Reclass', false);

// Load JRC Global Surface Water monthly history
var jrc = ee.ImageCollection('JRC/GSW1_0/MonthlyHistory');

// Define study period
var startDate = ee.Date.fromYMD(2000, 1, 1);
var endDate = ee.Date.fromYMD(2024, 4, 30);

// Filter JRC data by region and date
var myjrc = jrc.filterBounds(roi).filterDate(startDate, endDate);

// Detect observations (presence of data)
myjrc = myjrc.map(function(img){
  var obs = img.gt(0);
  return img.addBands(obs.rename('obs')
    .set('system:time_start', img.get('system:time_start')));
});

// Detect water presence (water class == 2)
myjrc = myjrc.map(function(img){
  var water = img.select('water').eq(2);
  return img.addBands(water.rename('onlywater')
    .set('system:time_start', img.get('system:time_start')));
});

// Sum total observations and total water observations
var totalobs = ee.ImageCollection(myjrc.select('obs')).sum().toFloat();
var totalWater = ee.ImageCollection(myjrc.select('onlywater')).sum().toFloat();

// Calculate flood frequency (%) = (water observations / total observations) * 100
var floodfreq = totalWater.divide(totalobs).multiply(100);

// Mask zero flood frequency areas
var myMask = floodfreq.neq(0);
floodfreq = floodfreq.updateMask(myMask);

// Visualization for flood frequency
var vis1 = {min: 0, max: 90, palette: ['c10000', 'd742f4', 'b7d2f7']};
Map.addLayer(floodfreq.clip(roi), vis1, 'Flood Frequency');

// Combine all reclassified layers and flood frequency for weighted overlay
var image = floodfreq
  .addBands(landcover)
  .addBands(elev_reclass)
  .addBands(slope_reclass)
  .addBands(ow_reclass)
  .addBands(hand_reclass);

// Calculate flood risk using weighted sum expression
var Risk = image.expression(
  '2.5 * floodfreq + 2 * land_cover + 2.5 * elev_reclass + 2.5 * slope_reclass + 1.5 * dist_ow_reclass + 1.5 * hand_reclass', {
    'land_cover': image.select('remapped'),
    'floodfreq': image.select('onlywater'),
    'elev_reclass': image.select('elevation'),
    'slope_reclass': image.select('slope'),
    'dist_ow_reclass': image.select('dist'),
    'hand_reclass': image.select('hnd')
  });

// Visualization for flood risk
var vis2 = {min: 0, max: 1000, palette: ['ffff00', 'ffa500', 'c00000']};
Map.addLayer(Risk.clip(roi), vis2, 'Flood Risk Map');
```javascript


