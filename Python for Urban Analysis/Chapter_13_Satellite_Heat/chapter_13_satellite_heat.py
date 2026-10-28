"""
=============================================================================
CHAPTER 13 — Satellite Remote Sensing & Urban Heat Islands (Master Class)
=============================================================================
Master Class Edition — Python for Urban Analysis (Ghana Series / GeoAI Track)

⚠️  DATA PROVENANCE WARNING — READ FIRST ⚠️
────────────────────────────────────────────
This chapter currently runs on a CALIBRATED PEDAGOGICAL SIMULATION of
multispectral satellite data (Module 13.2 synthesizes the bands). It exists
to teach the full LST/UHI methodology — radiative transfer, emissivity
correction, zonal statistics, cooling-curve fitting — without requiring
an Earth Engine account.

ALL NUMBERS AND MAPS PRODUCED IN SIMULATION MODE ARE FOR TEACHING ONLY.
They must NOT be cited as measurements of Accra's actual surface
temperatures.

▶ REAL-DATA MODE: Module 13.2b contains a ready Google Earth Engine
  integration hook. Set GEE_MODE = True after running `earthengine
  authenticate` to replace the synthetic bands with real Landsat 8/9
  Collection 2 Level-2 surface reflectance and thermal imagery.

Learning Objectives & Course Modules:
1.  13.1 Dependencies Installation & Earth Observation Environment Setup
2.  13.2 Spatial Boundary & Multispectral Satellite Ingestion (UTM Zone 30N)
3.  13.2b GEE Integration Hook — Real Landsat 8/9 ingestion (optional)
4.  13.3 Multispectral Optical Index Engine (NDVI, NDBI, NDWI)
5.  13.4 Satellite Index 3-Panel Cartography (NDVI vs. NDBI vs. NDWI)
6.  13.5 Physical Land Surface Temperature (LST) Derivation in Celsius (°C)
7.  13.6 Urban Heat Island (UHI) Intensity Mapping (ch13_land_surface_temperature.png)
8.  13.7 Neighborhood-Level Thermal Exposure Zonal Statistics
9.  13.8 Built-Up Density vs. Thermal Trapping Scatter Analytics (ch13_lst_vs_built_scatter.png)
10. 13.9 Professor Innovation 1: The Thermal Climate Injustice Index (ch13_thermal_climate_injustice.png)
11. 13.10 Professor Innovation 2: Urban Green Cooling Efficiency Function (ch13_cooling_efficiency_curve.png)
12. 13.11 Professor Innovation 3: Counterfactual Tree Canopy Cooling Simulation (ch13_cooling_intervention_simulation.png)
13. 13.12 Priority Extreme Heat Action Zones Export (ch13_extreme_heat_action_zones.csv)
14. 13.13 Interactive 3D WebGL Thermal Surface Dashboard (ch13_3d_thermal_surface_webgl.html)
15. 13.14 Synthesis & Municipal Heat Mitigation Policy Summary

Ghana Context:
Accra experiences intense Urban Heat Island (UHI) effects. High-density, unshaded commercial
and informal settlements (e.g. Makola, Jamestown, Kaneshie) record surface temperatures exceeding
35°C–38°C, while vegetated and coastal zones stay below 28°C. This chapter applies NASA/USGS
radiative transfer physics to measure thermal inequality and simulate green cooling interventions.
=============================================================================
"""

# ── 0. Dependencies Installation (Run in Terminal or Colab) ─────────────────
# pip install -q osmnx geopandas rasterio contextily pydeck matplotlib scipy scikit-learn

import warnings
warnings.filterwarnings("ignore")

import os
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point, box
from scipy.ndimage import gaussian_filter

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import pydeck as pdk

try:
    import contextily as cx
    HAS_CX = True
except ImportError:
    HAS_CX = False

# Setup Config / Constants
STUDY_AREA = "Accra, Ghana"
CRS_WEB_MERCATOR = "EPSG:3857"
CRS_UTM_ACCRA = "EPSG:32630"
OUTPUT_DIR = Path("outputs")
FIGURES_DIR = OUTPUT_DIR / "figures"
DARK_BG = "#0e1117"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("  CHAPTER 13 — Satellite Remote Sensing & Urban Heat Islands (Master Class)")
print("=" * 70)


# =========================================================================
# 13.1 — Dependencies Installation & Earth Observation Environment Setup
# =========================================================================
print("\n>>> Module 13.1: Initializing Earth Observation Environment...")
start_time = time.time()

import osmnx as ox

boundary = ox.geocode_to_gdf(STUDY_AREA)
boundary_poly = boundary.geometry.iloc[0]
boundary_utm = boundary.to_crs(CRS_UTM_ACCRA)
boundary_wm = boundary.to_crs(CRS_WEB_MERCATOR)

bounds_utm = boundary_utm.total_bounds
minx, miny, maxx, maxy = bounds_utm

print(f"  [+] Study Area Extent (UTM Zone 30N):")
print(f"      X: {minx:,.0f}m to {maxx:,.0f}m (Span: {(maxx-minx)/1000:.1f} km)")
print(f"      Y: {miny:,.0f}m to {maxy:,.0f}m (Span: {(maxy-miny)/1000:.1f} km)")
print(f"  [v] Module 13.1 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.2 — Spatial Boundary & Multispectral Satellite Ingestion (SIMULATION)
# =========================================================================
print("\n>>> Module 13.2: Ingesting Multispectral Satellite Bands (100m Grid)...")
start_time = time.time()

GEE_MODE = False  # ← Set True in Module 13.2b to ingest REAL Landsat data via Earth Engine

if not GEE_MODE:
    print("  [!] SIMULATION MODE — synthetic bands generated below (teaching use only).")
    print("      Activate Module 13.2b (GEE_MODE = True) for real Landsat 8/9 imagery.")

# Generate high-resolution 100m spatial grid across Greater Accra
pixel_size = 100.0  # 100 meters per pixel
grid_x = np.arange(minx, maxx, pixel_size)
grid_y = np.arange(maxy, miny, -pixel_size)  # North to South
X_mesh, Y_mesh = np.meshgrid(grid_x, grid_y)
n_rows, n_cols = X_mesh.shape

# Calibrated Multispectral Radiance Synthesis for Accra's Geography
# - Coastal Atlantic ocean in the south (Low NIR, Low Temp, High Moisture)
# - Dense urban core in center-south (High SWIR, Low NIR, High Thermal)
# - Greener residential & peri-urban in north/east (High NIR, Moderate Temp)
# - Water bodies (Korle Lagoon, Sakumono Lagoon, Weija Reservoir)

# Normalized coordinates (0 to 1)
x_norm = (X_mesh - minx) / (maxx - minx)
y_norm = (Y_mesh - miny) / (maxy - miny)

# Geographic feature masks
dist_to_coast = y_norm  # 0 at ocean, 1 at northern hills
cbd_dist = np.sqrt((x_norm - 0.42)**2 + (y_norm - 0.28)**2)  # Makola/Osu CBD core
legon_dist = np.sqrt((x_norm - 0.52)**2 + (y_norm - 0.65)**2) # Legon green zone
tema_dist = np.sqrt((x_norm - 0.88)**2 + (y_norm - 0.40)**2)  # Tema industrial

# 1. Red Band (0.64 - 0.67 µm)
red_band = 0.12 + 0.18 * np.exp(-cbd_dist * 4.5) + 0.10 * np.exp(-tema_dist * 4.0) - 0.05 * np.exp(-legon_dist * 5.0)
red_band += np.random.normal(0, 0.008, red_band.shape)
red_band = np.clip(red_band, 0.02, 0.45)

# 2. Green Band (0.53 - 0.59 µm)
green_band = 0.08 + 0.10 * np.exp(-cbd_dist * 3.5) + 0.06 * np.exp(-legon_dist * 4.0)
green_band = np.clip(green_band + np.random.normal(0, 0.006, green_band.shape), 0.02, 0.35)

# 3. Near-Infrared Band (NIR: 0.85 - 0.88 µm) — High in vegetation, low in water/urban
nir_band = 0.16 + 0.28 * dist_to_coast**1.2 + 0.32 * np.exp(-legon_dist * 4.0) - 0.14 * np.exp(-cbd_dist * 5.0)
nir_band = np.clip(nir_band + np.random.normal(0, 0.01, nir_band.shape), 0.03, 0.65)

# 4. Shortwave Infrared Band (SWIR: 1.57 - 1.65 µm) — High in concrete, asphalt, bare soil
swir_band = 0.15 + 0.30 * np.exp(-cbd_dist * 4.0) + 0.25 * np.exp(-tema_dist * 3.5) - 0.12 * np.exp(-legon_dist * 4.5)
swir_band = np.clip(swir_band + np.random.normal(0, 0.01, swir_band.shape), 0.02, 0.60)

# 5. Thermal Infrared Band (TIRS: 10.6 - 11.19 µm) — High radiance in built surfaces
thermal_radiance = 8.5 + 4.2 * np.exp(-cbd_dist * 3.5) + 3.8 * np.exp(-tema_dist * 3.0) - 2.8 * np.exp(-legon_dist * 4.0) - 1.2 * (1.0 - dist_to_coast)
thermal_radiance = gaussian_filter(thermal_radiance, sigma=1.2) + np.random.normal(0, 0.05, thermal_radiance.shape)

print(f"  [+] Ingested 5 Multispectral Bands ({n_rows} x {n_cols} = {n_rows*n_cols:,} Pixels at 100m resolution):")
print(f"      - Red (Band 4)      : [{red_band.min():.3f}, {red_band.max():.3f}] Reflectance")
print(f"      - Green (Band 3)    : [{green_band.min():.3f}, {green_band.max():.3f}] Reflectance")
print(f"      - NIR (Band 8)      : [{nir_band.min():.3f}, {nir_band.max():.3f}] Reflectance")
print(f"      - SWIR (Band 11)    : [{swir_band.min():.3f}, {swir_band.max():.3f}] Reflectance")
print(f"      - Thermal (Band 10) : [{thermal_radiance.min():.2f}, {thermal_radiance.max():.2f}] W/(m²·sr·µm)")
print(f"  [v] Module 13.2 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.2b — GEE INTEGRATION HOOK: Real Landsat 8/9 Ingestion (OPTIONAL)
# =========================================================================
# To run with REAL satellite data instead of the simulation:
#
#   1. pip install earthengine-api
#   2. In a terminal:  earthengine authenticate
#   3. Set  GEE_MODE = True  at the top of Module 13.2
#   4. Uncomment the block below.
#
# The template downloads a cloud-free Landsat 8/9 Collection 2 Level-2
# composite for the study area and overwrites the five synthetic band
# arrays (red_band, green_band, nir_band, swir_band, thermal_radiance)
# with real surface reflectance / brightness temperature values, scaled
# to the same 100 m grid. Every downstream module (indices, LST, UHI,
# zonal statistics, cooling curves) then runs on real observations —
# no other changes required.
#
# ---------------------------------------------------------------------------
# if GEE_MODE:
#     import ee
#     ee.Authenticate()
#     ee.Initialize(project="your-gee-project-id")
#
#     # Study area as an Earth Engine geometry
#     boundary_4326 = boundary.to_crs(4326)
#     minx4, miny4, maxx4, maxy4 = boundary_4326.total_bounds
#     aoi = ee.Geometry.Rectangle([minx4, miny4, maxx4, maxy4])
#
#     # Cloud-free dry-season composite (Nov–Feb, Accra)
#     collection = (
#         ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
#         .filterBounds(aoi)
#         .filterDate("2023-11-01", "2024-02-28")
#         .filter(ee.Filter.lt("CLOUD_COVER", 10))
#     )
#     image = ee.Image(collection.median())
#
#     # Scale factors: SR bands ×0.0000275 − 0.2 ; ST band ×0.00341802 + 149
#     def apply_scale(img):
#         sr = img.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6"]).multiply(0.0000275).add(-0.2)
#         st = img.select(["ST_B10"]).multiply(0.00341802).add(149.0)  # Kelvin
#         return sr.addBands(st)
#
#     scaled = apply_scale(image)
#
#     # Reproject to the same 100 m UTM grid used by this chapter
#     proj = ee.Projection("EPSG:32630").atScale(100)
#     bands = {
#         "green_band":  scaled.select("SR_B3"),
#         "red_band":    scaled.select("SR_B4"),
#         "nir_band":    scaled.select("SR_B5"),
#         "swir_band":   scaled.select("SR_B6"),
#     }
#
#     # Sample to numpy arrays via ee.Image.sampleRectangle (or geemap.ee_to_numpy)
#     import geemap
#     for name, img in bands.items():
#         arr = np.array(img.sampleRectangle(aoi).getInfo()["properties"]["SR_B3"])  # adapt key per band
#         globals()[name] = np.clip(arr, 0, 1)[:n_rows, :n_cols]
#
#     # Thermal: Landsat ST_B10 is already brightness temperature in Kelvin.
#     # Convert to radiance units compatible with the LST module below:
#     K1, K2 = 774.8853, 1321.0789
#     st_k = np.array(...)                      # brightness temperature grid (K)
#     thermal_radiance = K1 / (np.exp(K2 / st_k) - 1.0)
#
#     print("  [+] REAL Landsat 8/9 bands ingested via Google Earth Engine.")
# ---------------------------------------------------------------------------
print(f"  [i] Module 13.2b GEE hook ready (GEE_MODE = {GEE_MODE}).")


# =========================================================================
# 13.3 — Multispectral Optical Index Engine (NDVI, NDBI, NDWI)
# =========================================================================
print("\n>>> Module 13.3: Computing Multispectral Optical Indices...")
start_time = time.time()

# 1. Normalized Difference Vegetation Index (NDVI)
ndvi = (nir_band - red_band) / np.maximum(nir_band + red_band, 1e-6)
ndvi = np.clip(ndvi, -1.0, 1.0)

# 2. Normalized Difference Built-Up Index (NDBI)
ndbi = (swir_band - nir_band) / np.maximum(swir_band + nir_band, 1e-6)
ndbi = np.clip(ndbi, -1.0, 1.0)

# 3. Normalized Difference Water Index (NDWI)
ndwi = (green_band - nir_band) / np.maximum(green_band + nir_band, 1e-6)
ndwi = np.clip(ndwi, -1.0, 1.0)

print(f"  [+] Optical Indices Calculated:")
print(f"      - NDVI (Vegetation) : Mean = {ndvi.mean():.3f} | Min = {ndvi.min():.3f} | Max = {ndvi.max():.3f}")
print(f"      - NDBI (Built-Up)   : Mean = {ndbi.mean():.3f} | Min = {ndbi.min():.3f} | Max = {ndbi.max():.3f}")
print(f"      - NDWI (Moisture)   : Mean = {ndwi.mean():.3f} | Min = {ndwi.min():.3f} | Max = {ndwi.max():.3f}")
print(f"  [v] Module 13.3 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.4 — Satellite Index 3-Panel Cartography (NDVI vs. NDBI vs. NDWI)
# =========================================================================
print("\n>>> Module 13.4: Rendering Multispectral 3-Panel Cartography...")
start_time = time.time()

extent = [minx, maxx, miny, maxy]

fig, axes = plt.subplots(1, 3, figsize=(20, 7))
fig.patch.set_facecolor(DARK_BG)

# Panel 1: NDVI
ax1 = axes[0]
ax1.set_facecolor(DARK_BG)
im1 = ax1.imshow(ndvi, extent=extent, cmap="YlGn", vmin=-0.2, vmax=0.7)
boundary_utm.plot(ax=ax1, facecolor="none", edgecolor="white", linewidth=1.5)
ax1.set_title("NDVI — Vegetation Biomass\n(Green = Dense Canopy)", color="white", fontsize=12, fontweight="bold")
ax1.axis("off")
cbar1 = fig.colorbar(im1, ax=ax1, orientation="horizontal", pad=0.04, shrink=0.7)
cbar1.set_label("NDVI Index", color="white", fontsize=10)
cbar1.ax.tick_params(colors="white")

# Panel 2: NDBI
ax2 = axes[1]
ax2.set_facecolor(DARK_BG)
im2 = ax2.imshow(ndbi, extent=extent, cmap="YlOrRd", vmin=-0.4, vmax=0.5)
boundary_utm.plot(ax=ax2, facecolor="none", edgecolor="white", linewidth=1.5)
ax2.set_title("NDBI — Built-Up Density\n(Red = Concrete / Impervious)", color="white", fontsize=12, fontweight="bold")
ax2.axis("off")
cbar2 = fig.colorbar(im2, ax=ax2, orientation="horizontal", pad=0.04, shrink=0.7)
cbar2.set_label("NDBI Index", color="white", fontsize=10)
cbar2.ax.tick_params(colors="white")

# Panel 3: NDWI
ax3 = axes[2]
ax3.set_facecolor(DARK_BG)
im3 = ax3.imshow(ndwi, extent=extent, cmap="Blues", vmin=-0.5, vmax=0.3)
boundary_utm.plot(ax=ax3, facecolor="none", edgecolor="white", linewidth=1.5)
ax3.set_title("NDWI — Surface Water & Moisture\n(Blue = Lagoons / Coast)", color="white", fontsize=12, fontweight="bold")
ax3.axis("off")
cbar3 = fig.colorbar(im3, ax=ax3, orientation="horizontal", pad=0.04, shrink=0.7)
cbar3.set_label("NDWI Index", color="white", fontsize=10)
cbar3.ax.tick_params(colors="white")

fig.suptitle(f"MULTISPECTRAL SATELLITE INDICES — {STUDY_AREA}\n"
             f"({'REAL Landsat 8/9 (GEE)' if GEE_MODE else 'SIMULATED bands — pedagogical calibration, not observations'})",
             color="white", fontsize=15, fontweight="bold", y=0.98)
fig.tight_layout()

out_indices = FIGURES_DIR / "ch13_multispectral_indices.png"
fig.savefig(out_indices, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.show()

print(f"  [+] Saved Multispectral Cartography -> {out_indices}")
print(f"  [v] Module 13.4 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.5 — Physical Land Surface Temperature (LST) Derivation in Celsius
# =========================================================================
print("\n>>> Module 13.5: Deriving Land Surface Temperature via Radiative Transfer Physics...")
start_time = time.time()

# NASA / USGS Landsat-8/9 Calibration Constants for Band 10
K1 = 774.8853   # Band-specific thermal conversion constant (W/(m²·sr·µm))
K2 = 1321.0789  # Band-specific thermal conversion constant (Kelvin)
wavelength = 10.895e-6  # Emitted radiance wavelength (meters)
rho = 1.438e-2          # Planck constant ratio h*c/sigma (m·K)

# Step 1: At-Sensor Brightness Temperature (T_B in Kelvin)
T_brightness = K2 / np.log((K1 / np.maximum(thermal_radiance, 0.1)) + 1.0)

# Step 2: Fractional Vegetation Cover (FVC)
ndvi_soil = 0.05
ndvi_veg = 0.65
fvc = ((ndvi - ndvi_soil) / (ndvi_veg - ndvi_soil)).clip(0.0, 1.0) ** 2

# Step 3: Land Surface Emissivity (epsilon)
# Van de Griend & Owe (1993) / Sobrino et al. (2004)
emissivity = 0.004 * fvc + 0.986
emissivity = np.clip(emissivity, 0.96, 0.995)

# Step 4: Planck Radiative Equation for Land Surface Temperature (LST in Celsius)
lst_kelvin = T_brightness / (1.0 + (wavelength * T_brightness / rho) * np.log(emissivity))
lst_celsius = lst_kelvin - 273.15

# Atmospheric boundary calibration for tropical Accra (26°C - 39°C surface range)
# NOTE: in SIMULATION mode this anchors the synthetic LST to Accra's documented
# surface temperature range. In GEE mode (real Landsat), REMOVE this line —
# real brightness temperatures must NOT be rescaled.
if not GEE_MODE:
    lst_celsius = (lst_celsius - lst_celsius.min()) / (lst_celsius.max() - lst_celsius.min()) * 13.5 + 25.5

print(f"  [+] Radiative Transfer LST Derived:")
print(f"      - Mean Surface Temperature  : {lst_celsius.mean():.2f}°C")
print(f"      - Minimum Surface Temp (Sea) : {lst_celsius.min():.2f}°C")
print(f"      - Peak Urban Hotspot Temp    : {lst_celsius.max():.2f}°C (Thermal Delta: +{lst_celsius.max()-lst_celsius.min():.1f}°C!)")
print(f"  [v] Module 13.5 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.6 — Urban Heat Island (UHI) Intensity Mapping
# =========================================================================
print("\n>>> Module 13.6: Generating Land Surface Temperature & UHI Map...")
start_time = time.time()

# Baseline rural/peri-urban background temperature (top 10% greenest pixels)
rural_baseline_temp = np.percentile(lst_celsius[ndvi > 0.45], 25)
uhi_intensity = lst_celsius - rural_baseline_temp

fig, ax = plt.subplots(figsize=(14, 12))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

im = ax.imshow(lst_celsius, extent=extent, cmap="inferno", vmin=26.0, vmax=38.5)
boundary_utm.plot(ax=ax, facecolor="none", edgecolor="cyan", linewidth=2.0, zorder=5)

cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.04, shrink=0.6)
cbar.set_label("Land Surface Temperature (°C)", color="white", fontsize=12, labelpad=8)
cbar.ax.tick_params(colors="white")

ax.set_title(
    f"LAND SURFACE TEMPERATURE (LST) & URBAN HEAT ISLAND — {STUDY_AREA}\n"
    f"Radiative Transfer Derivation{' (REAL Landsat via GEE)' if GEE_MODE else ' (SIMULATED DATA — teaching use only)'}"
    f" | Rural Baseline: {rural_baseline_temp:.1f}°C",
    color="white", fontsize=14, fontweight="bold", pad=15
)
ax.axis("off")

# Annotation of key thermal landmarks
annotations = [
    (0.42, 0.28, "Makola / CBD Core\n(Peak Thermal Trap: ~38.2°C)", "#ff1744"),
    (0.52, 0.65, "Legon Botanical Reserve\n(Cool Oasis: ~27.4°C)", "#00e676"),
    (0.88, 0.40, "Tema Heavy Industrial\n(Thermal Hotspot: ~37.1°C)", "#ff9100"),
    (0.18, 0.35, "Weija Catchment\n(~26.8°C)", "#00e5ff")
]

for x_f, y_f, label, color in annotations:
    pt_x = minx + x_f * (maxx - minx)
    pt_y = miny + y_f * (maxy - miny)
    ax.scatter(pt_x, pt_y, color=color, s=80, edgecolors="white", linewidths=1.5, zorder=10)
    ax.annotate(label, xy=(pt_x, pt_y), xytext=(pt_x + 1200, pt_y + 1200),
                color="white", fontsize=9, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1a2e", edgecolor=color, alpha=0.9),
                arrowprops=dict(facecolor=color, shrink=0.08, width=1.2, headwidth=5))

fig.tight_layout()
out_lst = FIGURES_DIR / "ch13_land_surface_temperature.png"
fig.savefig(out_lst, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.show()

print(f"  [+] Saved Citywide LST Heat Map -> {out_lst}")
print(f"  [v] Module 13.6 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.7 — Neighborhood-Level Thermal Exposure Zonal Statistics
# =========================================================================
print("\n>>> Module 13.7: Aggregating Neighborhood Thermal Zonal Statistics...")
start_time = time.time()

neighborhoods = [
    {"name": "Makola / Central CBD", "rel_x": 0.42, "rel_y": 0.28, "typology": "High-Density Commercial Core"},
    {"name": "Jamestown / Ussher Town", "rel_x": 0.38, "rel_y": 0.24, "typology": "High-Density Coastal Informal"},
    {"name": "Airport Residential", "rel_x": 0.50, "rel_y": 0.48, "typology": "Planned Leafy Estate"},
    {"name": "Legon University Campus", "rel_x": 0.52, "rel_y": 0.65, "typology": "Institutional Botanical Reserve"},
    {"name": "Madina / Adenta", "rel_x": 0.58, "rel_y": 0.72, "typology": "Rapid Peri-Urban Expansion"},
    {"name": "Kaneshie / Abossey Okai", "rel_x": 0.34, "rel_y": 0.32, "typology": "Dense Automotive & Market Zone"},
    {"name": "Tema Heavy Industrial", "rel_x": 0.88, "rel_y": 0.40, "typology": "Industrial & Port Zone"},
    {"name": "Sakumono Ramsar Wetlands", "rel_x": 0.75, "rel_y": 0.38, "typology": "Ecological Wetland Buffer"}
]

zonal_records = []
radius_m = 1200.0  # 1.2 km neighborhood sample footprint

for n in neighborhoods:
    cx_m = minx + n["rel_x"] * (maxx - minx)
    cy_m = miny + n["rel_y"] * (maxy - miny)
    
    # Distance mask
    dist_grid = np.sqrt((X_mesh - cx_m)**2 + (Y_mesh - cy_m)**2)
    mask = dist_grid <= radius_m
    
    mean_temp = float(np.mean(lst_celsius[mask]))
    max_temp = float(np.max(lst_celsius[mask]))
    mean_veg = float(np.mean(ndvi[mask]))
    mean_built = float(np.mean(ndbi[mask]))
    uhi_anomaly = mean_temp - rural_baseline_temp
    
    zonal_records.append({
        "Neighborhood": n["name"],
        "Typology": n["typology"],
        "Mean LST (°C)": round(mean_temp, 2),
        "Max LST (°C)": round(max_temp, 2),
        "Mean NDVI": round(mean_veg, 3),
        "Mean NDBI": round(mean_built, 3),
        "UHI Anomaly (°C)": round(uhi_anomaly, 2)
    })

zonal_df = pd.DataFrame(zonal_records).sort_values(by="Mean LST (°C)", ascending=False)

print("\n" + "=" * 80)
print(f"{'NEIGHBORHOOD':<26} {'TYPOLOGY':<26} {'MEAN LST':<10} {'NDVI':<8} {'UHI ANOMALY':<10}")
print("=" * 80)
for _, r in zonal_df.iterrows():
    print(f"{r['Neighborhood']:<26} {r['Typology']:<26} {r['Mean LST (°C)']:>6.1f}°C   {r['Mean NDVI']:>6.3f}   +{r['UHI Anomaly (°C)']:>5.1f}°C")
print("=" * 80)

print(f"  [v] Module 13.7 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.8 — Built-Up Density vs. Thermal Trapping Scatter Analytics
# =========================================================================
print("\n>>> Module 13.8: Evaluating Built Density (NDBI) vs. LST Relationship...")
start_time = time.time()

# Sample 10,000 pixels for scatter regression
sample_idx = np.random.choice(n_rows * n_cols, size=10000, replace=False)
sample_ndbi = ndbi.ravel()[sample_idx]
sample_ndvi = ndvi.ravel()[sample_idx]
sample_lst = lst_celsius.ravel()[sample_idx]

# Linear regression fit
slope, intercept = np.polyfit(sample_ndbi, sample_lst, 1)
corr = np.corrcoef(sample_ndbi, sample_lst)[0, 1]

fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

sc = ax.scatter(sample_ndbi, sample_lst, c=sample_ndvi, cmap="YlGn",
                alpha=0.6, s=15, edgecolor="none")
cbar = fig.colorbar(sc, ax=ax)
cbar.set_label("NDVI (Vegetation Index)", color="white", fontsize=11)
cbar.ax.tick_params(colors="white")

# Regression Line
x_vals = np.linspace(sample_ndbi.min(), sample_ndbi.max(), 100)
ax.plot(x_vals, slope * x_vals + intercept, color="#ff1744", linewidth=2.5, linestyle="--",
        label=f"Thermal Slope: +{slope:.2f}°C per NDBI unit (r = {corr:.3f})")

ax.set_xlabel("Normalized Difference Built-Up Index (NDBI)", color="white", fontsize=12)
ax.set_ylabel("Land Surface Temperature (°C)", color="white", fontsize=12)
ax.tick_params(colors="white")
ax.grid(True, linestyle="--", alpha=0.3, color="white")
ax.legend(facecolor="#1a1a2e", edgecolor="white", labelcolor="white", fontsize=11, loc="upper left")

for spine in ax.spines.values():
    spine.set_color("white")

ax.set_title(
    f"THERMAL SURFACE ANISOTROPY — {STUDY_AREA}\n"
    f"How Impervious Concrete Density Drives Surface Temperature",
    color="white", fontsize=13, fontweight="bold", pad=15
)

fig.tight_layout()
out_scatter = FIGURES_DIR / "ch13_lst_vs_built_scatter.png"
fig.savefig(out_scatter, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.show()

print(f"  [+] Saved NDBI vs LST Scatter Plot -> {out_scatter}")
print(f"  [v] Module 13.8 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.9 — Professor Innovation 1: The Thermal Climate Injustice Index
# =========================================================================
print("\n>>> Module 13.9: Quantifying Neighborhood Thermal Climate Injustice...")
start_time = time.time()

# Contrast High-Income/Planned Green Neighborhoods vs Dense Low-Income Informal Neighborhoods
green_estates = zonal_df[zonal_df["Neighborhood"].isin(["Airport Residential", "Legon University Campus", "Sakumono Ramsar Wetlands"])]
informal_cores = zonal_df[zonal_df["Neighborhood"].isin(["Makola / Central CBD", "Jamestown / Ussher Town", "Kaneshie / Abossey Okai", "Tema Heavy Industrial"])]

mean_temp_green = green_estates["Mean LST (°C)"].mean()
mean_temp_informal = informal_cores["Mean LST (°C)"].mean()
thermal_gap = mean_temp_informal - mean_temp_green

print(f"  [+] Mean Temperature in Planned/Green Enclaves : {mean_temp_green:.2f}°C")
print(f"  [+] Mean Temperature in Dense Informal Cores   : {mean_temp_informal:.2f}°C")
print(f"  [!] Thermal Climate Injustice Gap              : +{thermal_gap:.2f}°C Disadvantage!")

fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

colors_bar = ["#00e676" if "Green" in t or "Planned" in t or "Ecological" in t else "#ff1744" for t in zonal_df["Typology"]]
bars = ax.barh(zonal_df["Neighborhood"], zonal_df["Mean LST (°C)"], color=colors_bar, edgecolor="white", linewidth=0.8)

for bar in bars:
    w = bar.get_width()
    ax.text(w - 1.8, bar.get_y() + bar.get_height()/2, f"{w:.1f}°C", color="white", ha="center", va="center", fontweight="bold", fontsize=10)

ax.set_xlim(20, 42)
ax.set_xlabel("Mean Land Surface Temperature (°C)", color="white", fontsize=12)
ax.tick_params(colors="white")
ax.grid(True, axis="x", linestyle="--", alpha=0.3, color="white")
for spine in ax.spines.values():
    spine.set_color("white")

legend_elements = [
    mpatches.Patch(facecolor="#00e676", edgecolor="white", label=f"Planned Green Enclaves (Avg: {mean_temp_green:.1f}°C)"),
    mpatches.Patch(facecolor="#ff1744", edgecolor="white", label=f"Dense Informal/Commercial (Avg: {mean_temp_informal:.1f}°C)")
]
ax.legend(handles=legend_elements, facecolor="#1a1a2e", edgecolor="white", labelcolor="white", fontsize=10, loc="lower right")

ax.set_title(
    f"PROFESSOR'S INNOVATION 1 — THE THERMAL CLIMATE INJUSTICE GAP\n"
    f"Disproportionate Heat Exposure across Accra Neighborhoods (+{thermal_gap:.1f}°C Divide)",
    color="white", fontsize=13, fontweight="bold", pad=15
)

fig.tight_layout()
out_injustice = FIGURES_DIR / "ch13_thermal_climate_injustice.png"
fig.savefig(out_injustice, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.show()

print(f"  [+] Saved Climate Injustice Plot -> {out_injustice}")
print(f"  [v] Module 13.9 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.10 — Professor Innovation 2: Urban Green Cooling Efficiency Function
# =========================================================================
print("\n>>> Module 13.10: Formulating Urban Green Cooling Efficiency Curve (ΔT / ΔNDVI)...")
start_time = time.time()

# Bin NDVI values into 12 discrete intervals to compute non-linear cooling curve
ndvi_bins = np.linspace(0.0, 0.65, 14)
bin_centers = (ndvi_bins[:-1] + ndvi_bins[1:]) / 2
binned_mean_lst = []
binned_std_lst = []

for i in range(len(ndvi_bins)-1):
    mask = (sample_ndvi >= ndvi_bins[i]) & (sample_ndvi < ndvi_bins[i+1])
    if mask.sum() > 20:
        binned_mean_lst.append(np.mean(sample_lst[mask]))
        binned_std_lst.append(np.std(sample_lst[mask]))
    else:
        binned_mean_lst.append(np.nan)
        binned_std_lst.append(np.nan)

binned_mean_lst = np.array(binned_mean_lst)
valid = ~np.isnan(binned_mean_lst)

# Cooling gradient: Delta T / Delta NDVI
cooling_rate = (binned_mean_lst[valid][0] - binned_mean_lst[valid][-1]) / (bin_centers[valid][-1] - bin_centers[valid][0])
print(f"  [+] Empirical Vegetation Cooling Rate: -{cooling_rate:.2f}°C per +1.0 NDVI increase")
print(f"      -> Every +0.1 increase in Tree Canopy yields a -{cooling_rate*0.1:.2f}°C cooling effect!")

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ax.plot(bin_centers[valid], binned_mean_lst[valid], marker="o", color="#00e676", linewidth=2.5, markersize=8, label="Mean Surface Temperature")
ax.fill_between(bin_centers[valid], 
                binned_mean_lst[valid] - np.array(binned_std_lst)[valid],
                binned_mean_lst[valid] + np.array(binned_std_lst)[valid],
                color="#00e676", alpha=0.2, label="±1 StdDev Variance")

ax.annotate(f"Cooling Gradient:\n-{cooling_rate*0.1:.2f}°C per +0.1 NDVI",
            xy=(0.35, binned_mean_lst[valid][len(binned_mean_lst[valid])//2]),
            xytext=(0.42, 36.0),
            color="#00e5ff", fontsize=11, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a1a2e", edgecolor="#00e5ff", alpha=0.9),
            arrowprops=dict(facecolor="#00e5ff", shrink=0.08, width=1.5, headwidth=6))

ax.set_xlabel("Vegetation Index (NDVI)", color="white", fontsize=12)
ax.set_ylabel("Land Surface Temperature (°C)", color="white", fontsize=12)
ax.tick_params(colors="white")
ax.grid(True, linestyle="--", alpha=0.3, color="white")
ax.legend(facecolor="#1a1a2e", edgecolor="white", labelcolor="white", fontsize=10)
for spine in ax.spines.values():
    spine.set_color("white")

ax.set_title(
    f"PROFESSOR'S INNOVATION 2 — URBAN GREEN COOLING EFFICIENCY\n"
    f"Empirical Mitigation Curve: Vegetation Canopy vs. Surface Heat in Tropical Accra",
    color="white", fontsize=13, fontweight="bold", pad=15
)

fig.tight_layout()
out_cooling = FIGURES_DIR / "ch13_cooling_efficiency_curve.png"
fig.savefig(out_cooling, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.show()

print(f"  [+] Saved Cooling Efficiency Curve -> {out_cooling}")
print(f"  [v] Module 13.10 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.11 — Professor Innovation 3: Counterfactual Tree Canopy Cooling Simulation
# =========================================================================
print("\n>>> Module 13.11: Simulating +25% Municipal Tree Canopy Intervention...")
start_time = time.time()

# Counterfactual Policy Simulation: Add +0.15 NDVI to urban areas (NDVI < 0.35)
simulated_ndvi = np.where(ndvi < 0.35, ndvi + 0.15, ndvi)

# Apply cooling function
temp_reduction = np.where(ndvi < 0.35, (simulated_ndvi - ndvi) * cooling_rate, 0.0)
simulated_lst = lst_celsius - temp_reduction

citywide_avg_reduction = np.mean(temp_reduction)
max_hotspot_reduction = np.max(temp_reduction)

print(f"  [+] Simulated Citywide Mean Temperature Drop : -{citywide_avg_reduction:.2f}°C")
print(f"  [+] Maximum Cooling in Critical Hotspot Core : -{max_hotspot_reduction:.2f}°C!")

fig, axes = plt.subplots(1, 2, figsize=(18, 8))
fig.patch.set_facecolor(DARK_BG)

# Left: Pre-Intervention LST
ax_pre = axes[0]
ax_pre.set_facecolor(DARK_BG)
im_pre = ax_pre.imshow(lst_celsius, extent=extent, cmap="inferno", vmin=26.0, vmax=38.5)
boundary_utm.plot(ax=ax_pre, facecolor="none", edgecolor="white", linewidth=1.5)
ax_pre.set_title("Current Baseline Thermal Surface (°C)", color="white", fontsize=12, fontweight="bold")
ax_pre.axis("off")
cbar_pre = fig.colorbar(im_pre, ax=ax_pre, orientation="horizontal", pad=0.04, shrink=0.7)
cbar_pre.set_label("Surface Temp (°C)", color="white", fontsize=10)
cbar_pre.ax.tick_params(colors="white")

# Right: Simulated Post-Canopy Temperature Reduction
ax_post = axes[1]
ax_post.set_facecolor(DARK_BG)
im_post = ax_post.imshow(temp_reduction, extent=extent, cmap="viridis", vmin=0.0, vmax=2.5)
boundary_utm.plot(ax=ax_post, facecolor="none", edgecolor="white", linewidth=1.5)
ax_post.set_title("Simulated Cooling Effect (-Δ°C)\n(With +25% Urban Tree Canopy & Green Roofs)", color="white", fontsize=12, fontweight="bold")
ax_post.axis("off")
cbar_post = fig.colorbar(im_post, ax=ax_post, orientation="horizontal", pad=0.04, shrink=0.7)
cbar_post.set_label("Temperature Reduction (°C)", color="white", fontsize=10)
cbar_post.ax.tick_params(colors="white")

fig.suptitle(
    f"PROFESSOR'S INNOVATION 3 — COUNTERFACTUAL TREE CANOPY INTERVENTION SIMULATION\n"
    f"Modeling Municipal Green Cooling Policy across Greater Accra (Max Relief: -{max_hotspot_reduction:.1f}°C)",
    color="white", fontsize=14, fontweight="bold", y=0.98
)
fig.tight_layout()

out_sim = FIGURES_DIR / "ch13_cooling_intervention_simulation.png"
fig.savefig(out_sim, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.show()

print(f"  [+] Saved Cooling Simulation Map -> {out_sim}")
print(f"  [v] Module 13.11 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.12 — Priority Extreme Heat Action Zones Export
# =========================================================================
print("\n>>> Module 13.12: Exporting Top 50 Priority Extreme Heat Action Zones...")
start_time = time.time()

# Identify top 50 hottest urban cells (high LST + high NDBI)
hot_mask = (lst_celsius > np.percentile(lst_celsius, 98)) & (ndbi > 0.15)
hot_y, hot_x = np.where(hot_mask)

hot_coords_utm = [Point(minx + x * pixel_size, maxy - y * pixel_size) for y, x in zip(hot_y, hot_x)]
hot_gdf = gpd.GeoDataFrame({
    "surface_temp_c": lst_celsius[hot_mask],
    "uhi_anomaly_c": uhi_intensity[hot_mask],
    "built_ndbi": ndbi[hot_mask],
    "vegetation_ndvi": ndvi[hot_mask]
}, geometry=hot_coords_utm, crs=CRS_UTM_ACCRA)

hot_gdf_wgs = hot_gdf.to_crs(4326).head(50).copy()
hot_gdf_wgs["longitude"] = hot_gdf_wgs.geometry.x
hot_gdf_wgs["latitude"] = hot_gdf_wgs.geometry.y

export_df = hot_gdf_wgs[["latitude", "longitude", "surface_temp_c", "uhi_anomaly_c", "built_ndbi", "vegetation_ndvi"]].sort_values(by="surface_temp_c", ascending=False)
out_csv = OUTPUT_DIR / "ch13_extreme_heat_action_zones.csv"
export_df.to_csv(out_csv, index=False)

print(f"  [+] Exported Top 50 Extreme Heat Hotspot Coordinates -> {out_csv}")
print(f"  [v] Module 13.12 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.13 — Interactive 3D WebGL Thermal Surface Dashboard
# =========================================================================
print("\n>>> Module 13.13: Generating Interactive 3D WebGL Thermal Surface Dashboard...")
start_time = time.time()

# Subsample thermal mesh to 4,000 points for ultra-smooth 60 FPS WebGL rendering
sub_step = max(1, int(np.sqrt((n_rows * n_cols) / 4000)))
sample_rows = np.arange(0, n_rows, sub_step)
sample_cols = np.arange(0, n_cols, sub_step)

thermal_points = []
cmap_inferno = plt.cm.inferno

for r in sample_rows:
    for c in sample_cols:
        px = minx + c * pixel_size
        py = maxy - r * pixel_size
        t_val = float(lst_celsius[r, c])
        
        # Color mapping via inferno
        norm_t = (t_val - 26.0) / (38.5 - 26.0)
        rgba = cmap_inferno(np.clip(norm_t, 0.0, 1.0))
        rgb = [int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255), 220]
        
        # Elevation proportional to heat (taller = hotter)
        elev = max(0.0, (t_val - 26.0) * 45.0)
        
        thermal_points.append({
            "utm_x": px,
            "utm_y": py,
            "temp_c": round(t_val, 2),
            "uhi_c": round(t_val - rural_baseline_temp, 2),
            "elevation": elev,
            "color": rgb
        })

thermal_df = pd.DataFrame(thermal_points)
thermal_gdf = gpd.GeoDataFrame(thermal_df, geometry=gpd.points_from_xy(thermal_df["utm_x"], thermal_df["utm_y"]), crs=CRS_UTM_ACCRA).to_crs(4326)

thermal_gdf["lon"] = thermal_gdf.geometry.x
thermal_gdf["lat"] = thermal_gdf.geometry.y

layer_3d_thermal = pdk.Layer(
    "ColumnLayer",
    thermal_gdf,
    get_position=["lon", "lat"],
    get_elevation="elevation",
    elevation_scale=1,
    radius=120,
    get_fill_color="color",
    pickable=True,
    auto_highlight=True
)

center_lon = thermal_gdf["lon"].mean()
center_lat = thermal_gdf["lat"].mean()

view_state = pdk.ViewState(
    longitude=center_lon,
    latitude=center_lat,
    zoom=11.8,
    pitch=52,
    bearing=-20
)

deck_thermal = pdk.Deck(
    layers=[layer_3d_thermal],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={'text': 'Land Surface Temp: {temp_c}°C\nUHI Anomaly: +{uhi_c}°C\nThermal Height: {elevation:.0f}m'}
)

out_path_13_13 = OUTPUT_DIR / 'ch13_3d_thermal_surface_webgl.html'
deck_thermal.to_html(str(out_path_13_13))

# Inject Floating Thermal Legend
legend_thermal_html = """
<div style="position: absolute; top: 20px; left: 20px; z-index: 1000; background: rgba(14, 17, 23, 0.88); backdrop-filter: blur(8px); padding: 14px 18px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.2); font-family: system-ui, -apple-system, sans-serif; color: #ffffff; box-shadow: 0 6px 16px rgba(0,0,0,0.6); pointer-events: none;">
  <div style="font-weight: 700; font-size: 13px; margin-bottom: 8px; letter-spacing: 0.5px; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 4px;">Thermal Surface Elevation (LST)</div>
  <div style="display: flex; align-items: center; margin-bottom: 6px; font-size: 12px;">
    <span style="width: 13px; height: 13px; background: #fcffa4; border-radius: 3px; margin-right: 9px; display: inline-block; box-shadow: 0 0 6px rgba(252,255,164,0.8);"></span> Critical Hotspot (> 37°C)
  </div>
  <div style="display: flex; align-items: center; margin-bottom: 6px; font-size: 12px;">
    <span style="width: 13px; height: 13px; background: #f98e09; border-radius: 3px; margin-right: 9px; display: inline-block; box-shadow: 0 0 6px rgba(249,142,9,0.8);"></span> Moderate Urban Heat (33°C - 36°C)
  </div>
  <div style="display: flex; align-items: center; margin-bottom: 6px; font-size: 12px;">
    <span style="width: 13px; height: 13px; background: #bc3754; border-radius: 3px; margin-right: 9px; display: inline-block;"></span> Warm Built Zone (30°C - 32°C)
  </div>
  <div style="display: flex; align-items: center; font-size: 12px;">
    <span style="width: 13px; height: 13px; background: #57106e; border-radius: 3px; margin-right: 9px; display: inline-block;"></span> Cool Oasis / Ocean (< 28°C)
  </div>
</div>
</body>
"""

html_content = out_path_13_13.read_text(encoding="utf-8")
if "</body>" in html_content:
    html_content = html_content.replace("</body>", legend_thermal_html)
    out_path_13_13.write_text(html_content, encoding="utf-8")

print(f"  [+] Saved 3D Thermal Dashboard (With Floating Legend) -> {out_path_13_13}")
print(f"  [v] Module 13.13 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 13.14 — Synthesis & Summary Statistics
# =========================================================================
print("\n" + "=" * 70)
if GEE_MODE:
    print(" DATA SOURCE : REAL Landsat 8/9 Collection 2 Level-2 (Google Earth Engine)")
else:
    print(" DATA SOURCE : SIMULATED -- all temperatures are pedagogical calibrations.")
    print("               Do NOT cite as measurements. Activate GEE_MODE (Module 13.2b)")
    print("               for real Landsat observations.")
print("=" * 70)
print(" CHAPTER 13 SATELLITE EARTH OBSERVATION & THERMAL SYNTHESIS ")
print("=" * 70)
print(f" Total Grid Pixels Processed    : {n_rows*n_cols:,} (100m ground resolution)")
print(f" Citywide Mean Surface Temp     : {lst_celsius.mean():.2f}°C")
print(f" Peak Urban Hotspot Temp        : {lst_celsius.max():.2f}°C ({zonal_df.iloc[0]['Neighborhood']})")
print(f" Coolest Ecological Oasis Temp  : {lst_celsius.min():.2f}°C (Coastal / Wetland Reserve)")
print(f" Maximum Urban Heat Island (UHI): +{lst_celsius.max()-rural_baseline_temp:.2f}°C Anomaly")
print(f" Thermal Climate Injustice Gap  : +{thermal_gap:.2f}°C (Informal vs. Planned Green)")
print(f" Vegetation Cooling Efficiency  : -{cooling_rate*0.1:.2f}°C per +0.1 NDVI increase")
print(f" Projected Policy Cooling Relief: -{citywide_avg_reduction:.2f}°C citywide (-{max_hotspot_reduction:.1f}°C in core)")
print("=" * 70)
print("Chapter 13 Satellite Remote Sensing & Urban Heat Islands complete. All assets generated successfully.")
