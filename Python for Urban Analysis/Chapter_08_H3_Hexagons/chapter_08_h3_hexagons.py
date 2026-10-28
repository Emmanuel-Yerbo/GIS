"""
=============================================================================
CHAPTER 8 — H3 Hexagonal Spatial Intelligence (Master Class Edition)
=============================================================================
Learning Objectives & Course Modules:
1.  Fetch & Index — Amenity & building data into H3 hexagonal cells (Res 9)
2.  Aggregate — Per-hex density counts for amenities and buildings
3.  Amenity Hex Heatmap — 2D static choropleth on dark basemap
4.  Building Density Heatmap — Separate building-count visualisation
5.  Side-by-Side Comparison — Dual-panel amenity vs building mismatch
6.  Multi-Resolution View — Res 7 / 9 / 11 panels (granularity effect)
7.  K-Ring Neighbor Smoothing — Spatial filter via grid_disk averaging
8.  Hot/Cold Spot Detection — Local Getis-Ord Gi* z-scores (manual)
9.  3D Extruded Pydeck — Enhanced interactive hex column map
10. Interactive Dual-Metric Pydeck — Amenity height + building colour
11. Professor Innovation 1: MAUP Sensitivity Cascade
12. Professor Innovation 2: Shannon Spatial Entropy & Urban Evenness
13. Professor Innovation 3: Hansen Gravity Accessibility Surface

Ghana Context:
Tiles Greater Accra into a uniform hexagonal matrix to eliminate Modifiable
Areal Unit Problem (MAUP) boundary biases, quantify service evenness using
information theory, and compute distance-decay accessibility surfaces.

Professor's Note:
  "Hexagons are the ideal spatial unit — every cell has equal area and
   6 equidistant neighbours. But the real insight is what happens when you
   CHANGE the resolution, SMOOTH the noise, and measure ACCESSIBILITY
   instead of density. That is where urban science begins."
=============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
import h3
import pydeck as pdk
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as cx
from collections import Counter
from config import (
    STUDY_AREA, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    OUTPUT_DIR, FIGURES_DIR, DARK_BG, ACCENT_CMAP,
    AMENITY_TAGS, BUILDING_TAGS,
)

print("=" * 65)
print("  CHAPTER 8 — H3 Hexagonal Spatial Intelligence (Master Class)")
print("=" * 65)


# =====================================================================
# UTILITY — Convert H3 cell to Shapely Polygon
# =====================================================================
def h3_to_polygon(h3_idx):
    """Convert an H3 cell index to a Shapely Polygon (lon/lat)."""
    boundary_coords = h3.cell_to_boundary(h3_idx)
    return Polygon([(lon, lat) for lat, lon in boundary_coords])


# =====================================================================
# 8.1 — Fetch Data & Index Points into H3 Hexagons
# =====================================================================
print(f"\n8.1 Fetching urban features for H3 indexing: {STUDY_AREA} ...")

boundary = ox.geocode_to_gdf(STUDY_AREA)
boundary_wm = boundary.to_crs(CRS_WEB_MERCATOR)
boundary_poly = boundary.geometry.iloc[0]

# Amenities
amenities = ox.features_from_place(STUDY_AREA, tags=AMENITY_TAGS).copy()
amenities["geometry"] = amenities.geometry.centroid
amenities = amenities[amenities.geometry.within(boundary_poly)].copy()

# Tag each amenity with a category for Innovation 2
def classify_amenity(row):
    a = row.get("amenity", "")
    if a in ("hospital", "clinic", "pharmacy"):
        return "Healthcare"
    elif a in ("school", "university", "library"):
        return "Education"
    elif a in ("marketplace", "bank", "atm", "restaurant", "fuel"):
        return "Commerce"
    elif a in ("place_of_worship",):
        return "Worship"
    else:
        return "Other"

amenities["category"] = amenities.apply(classify_amenity, axis=1)

# Buildings
buildings_raw = ox.features_from_place(STUDY_AREA, tags=BUILDING_TAGS)
buildings = buildings_raw[
    buildings_raw.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()
buildings["centroid"] = buildings.geometry.centroid

# Index into H3 (Resolution 9: ~0.1 km² per cell, ~175 m edge)
H3_RES = 9
print(f"    Indexing into H3 cells at Resolution {H3_RES} ...")

amenity_h3 = [
    h3.latlng_to_cell(lat, lng, H3_RES)
    for lat, lng in zip(amenities.geometry.y, amenities.geometry.x)
]
amenities["h3_index"] = amenity_h3

bldg_h3 = [
    h3.latlng_to_cell(lat, lng, H3_RES)
    for lat, lng in zip(buildings.centroid.y, buildings.centroid.x)
]
buildings["h3_index"] = bldg_h3

print(f"    Amenities indexed : {len(amenities):,}")
print(f"    Buildings indexed : {len(buildings):,}")


# =====================================================================
# 8.2 — Aggregate Densities per Hexagon
# =====================================================================
print("\n8.2 Aggregating densities per hexagon ...")

amenity_counts = pd.Series(amenity_h3).value_counts().rename("amenity_count")
bldg_counts = pd.Series(bldg_h3).value_counts().rename("building_count")

hex_df = pd.concat([amenity_counts, bldg_counts], axis=1).fillna(0).reset_index()
hex_df.rename(columns={"index": "h3_index"}, inplace=True)
hex_df["geometry"] = hex_df["h3_index"].apply(h3_to_polygon)
hex_gdf = gpd.GeoDataFrame(hex_df, geometry="geometry", crs="EPSG:4326")
hex_gdf_wm = hex_gdf.to_crs(CRS_WEB_MERCATOR)

print(f"    Total H3 hexagons : {len(hex_gdf):,}")
print(f"    Max amenity/hex   : {hex_gdf['amenity_count'].max():.0f}")
print(f"    Max building/hex  : {hex_gdf['building_count'].max():.0f}")


# =====================================================================
# 8.3 — 2D Static Amenity Hex Heatmap
# =====================================================================
print("\n8.3 Rendering amenity hex heatmap ...")

fig, ax = plt.subplots(figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

hex_gdf_wm.plot(
    ax=ax, column="amenity_count", cmap=ACCENT_CMAP,
    scheme="natural_breaks", k=7,
    linewidth=0.1, edgecolor="#222", alpha=0.85,
    legend=True,
    legend_kwds={
        "loc": "lower left", "fontsize": 9,
        "facecolor": "#1a1a2e", "edgecolor": "white",
        "labelcolor": "white", "framealpha": 0.9,
        "title": "Amenity Count per Hex",
    },
)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(f"H3 HEXAGONAL AMENITY DENSITY (Res {H3_RES}) -- {STUDY_AREA}",
             fontsize=18, fontweight="bold", color="white", pad=20)

fig.tight_layout()
path_83 = FIGURES_DIR / "ch8_h3_hex_amenity_density.png"
fig.savefig(path_83, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_83}")


# =====================================================================
# 8.4 — Building Density Hex Heatmap
# =====================================================================
print("\n8.4 Rendering building density hex heatmap ...")

fig, ax = plt.subplots(figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

hex_gdf_wm.plot(
    ax=ax, column="building_count", cmap="Oranges",
    scheme="natural_breaks", k=7,
    linewidth=0.1, edgecolor="#222", alpha=0.85,
    legend=True,
    legend_kwds={
        "loc": "lower left", "fontsize": 9,
        "facecolor": "#1a1a2e", "edgecolor": "white",
        "labelcolor": "white", "framealpha": 0.9,
        "title": "Building Count per Hex",
    },
)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(f"H3 HEXAGONAL BUILDING DENSITY (Res {H3_RES}) -- {STUDY_AREA}",
             fontsize=18, fontweight="bold", color="white", pad=20)

fig.tight_layout()
path_84 = FIGURES_DIR / "ch8_h3_hex_building_density.png"
fig.savefig(path_84, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_84}")


# =====================================================================
# 8.5 — Side-by-Side Comparison (Amenity vs Building)
# =====================================================================
print("\n8.5 Side-by-side amenity vs building density ...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(28, 14))
fig.patch.set_facecolor(DARK_BG)

for ax, col, cmap, title in [
    (ax1, "amenity_count", ACCENT_CMAP, "Amenity Density"),
    (ax2, "building_count", "Oranges", "Building Density"),
]:
    ax.set_facecolor(DARK_BG)
    hex_gdf_wm.plot(
        ax=ax, column=col, cmap=cmap,
        scheme="natural_breaks", k=7,
        linewidth=0.1, edgecolor="#222", alpha=0.85,
        legend=True,
        legend_kwds={
            "loc": "lower left", "fontsize": 8,
            "facecolor": "#1a1a2e", "edgecolor": "white",
            "labelcolor": "white", "framealpha": 0.9,
            "title": col.replace("_", " ").title(),
        },
    )
    boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2, zorder=10)
    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
    except Exception:
        pass
    ax.set_axis_off()
    ax.set_title(title, fontsize=15, fontweight="bold", color="white", pad=12)

fig.suptitle(
    f"AMENITY vs BUILDING DENSITY — Spatial Mismatch ({STUDY_AREA})",
    fontsize=18, fontweight="bold", color="white", y=0.97,
)
fig.tight_layout(rect=[0, 0, 1, 0.94])
path_85 = FIGURES_DIR / "ch8_h3_side_by_side_comparison.png"
fig.savefig(path_85, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_85}")


# =====================================================================
# 8.6 — Multi-Resolution Comparison (Res 7 / 9 / 11)
# =====================================================================
print("\n8.6 Multi-resolution comparison (Res 7 / 9 / 11) ...")

resolutions = [7, 9, 11]
res_gdfs = {}

for res in resolutions:
    h3_ids = [
        h3.latlng_to_cell(lat, lng, res)
        for lat, lng in zip(amenities.geometry.y, amenities.geometry.x)
    ]
    counts = pd.Series(h3_ids).value_counts().rename("amenity_count").reset_index()
    counts.rename(columns={"index": "h3_index"}, inplace=True)
    counts["geometry"] = counts["h3_index"].apply(h3_to_polygon)
    gdf = gpd.GeoDataFrame(counts, geometry="geometry", crs="EPSG:4326")
    res_gdfs[res] = gdf.to_crs(CRS_WEB_MERCATOR)

fig, axes = plt.subplots(1, 3, figsize=(30, 10))
fig.patch.set_facecolor(DARK_BG)

for ax, res in zip(axes, resolutions):
    ax.set_facecolor(DARK_BG)
    gdf = res_gdfs[res]
    area_km2 = h3.cell_area(list(gdf.to_crs("EPSG:4326")["h3_index"])[0], unit="km^2")
    gdf.plot(
        ax=ax, column="amenity_count", cmap=ACCENT_CMAP,
        scheme="natural_breaks", k=5,
        linewidth=0.1, edgecolor="#333", alpha=0.85,
    )
    boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=1.5)
    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
    except Exception:
        pass
    ax.set_axis_off()
    ax.set_title(
        f"Resolution {res}\n({len(gdf):,} cells, ~{area_km2:.3f} km² each)",
        fontsize=13, fontweight="bold", color="white", pad=10,
    )

fig.suptitle(
    "MULTI-RESOLUTION H3 -- Same Data, Different Granularity",
    fontsize=18, fontweight="bold", color="white", y=0.98,
)
fig.tight_layout(rect=[0, 0, 1, 0.93])
path_86 = FIGURES_DIR / "ch8_h3_multi_resolution.png"
fig.savefig(path_86, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_86}")


# =====================================================================
# 8.7 — K-Ring Neighbor Smoothing
# =====================================================================
print("\n8.7 K-Ring neighbor smoothing (k=1) ...")

hex_density = dict(zip(hex_gdf["h3_index"], hex_gdf["amenity_count"]))

smoothed = {}
for h in hex_gdf["h3_index"]:
    neighbors = h3.grid_disk(h, 1)  # self + 6 neighbors
    vals = [hex_density.get(n, 0) for n in neighbors]
    smoothed[h] = np.mean(vals)

hex_gdf["amenity_smoothed"] = hex_gdf["h3_index"].map(smoothed)
hex_gdf_wm["amenity_smoothed"] = hex_gdf["amenity_smoothed"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(28, 14))
fig.patch.set_facecolor(DARK_BG)

for ax, col, title in [
    (ax1, "amenity_count", "Raw Amenity Count"),
    (ax2, "amenity_smoothed", "K-Ring Smoothed (k=1)"),
]:
    ax.set_facecolor(DARK_BG)
    hex_gdf_wm.plot(
        ax=ax, column=col, cmap=ACCENT_CMAP,
        scheme="natural_breaks", k=7,
        linewidth=0.1, edgecolor="#222", alpha=0.85,
        legend=True,
        legend_kwds={
            "loc": "lower left", "fontsize": 8,
            "facecolor": "#1a1a2e", "edgecolor": "white",
            "labelcolor": "white", "framealpha": 0.9,
        },
    )
    boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2, zorder=10)
    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
    except Exception:
        pass
    ax.set_axis_off()
    ax.set_title(title, fontsize=15, fontweight="bold", color="white", pad=12)

fig.suptitle(
    "SPATIAL SMOOTHING -- Raw vs K-Ring Averaged Amenity Density",
    fontsize=18, fontweight="bold", color="white", y=0.97,
)
fig.tight_layout(rect=[0, 0, 1, 0.94])
path_87 = FIGURES_DIR / "ch8_h3_kring_smoothing.png"
fig.savefig(path_87, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_87}")


# =====================================================================
# 8.8 — Hot/Cold Spot Detection (Getis-Ord Gi* z-scores)
# =====================================================================
print("\n8.8 Hot/cold spot detection (Getis-Ord Gi*) ...")

all_h3_indices = list(hex_gdf["h3_index"])
x_vals = hex_gdf["amenity_count"].values.astype(float)
x_mean = x_vals.mean()
x_std = x_vals.std()
n = len(x_vals)

# Build neighbor lookup (k=1 ring)
idx_map = {h: i for i, h in enumerate(all_h3_indices)}

gi_star = np.zeros(n)
for i, h in enumerate(all_h3_indices):
    neighbors = h3.grid_disk(h, 1)
    neighbor_indices = [idx_map[nb] for nb in neighbors if nb in idx_map]
    w_count = len(neighbor_indices)
    if w_count == 0 or x_std == 0:
        gi_star[i] = 0.0
        continue
    local_sum = sum(x_vals[j] for j in neighbor_indices)
    # Gi* formula: z = (local_sum - w*x_mean) / (x_std * sqrt((n*w - w^2)/(n-1)))
    expected = w_count * x_mean
    s = x_std
    denom = s * np.sqrt((n * w_count - w_count**2) / (n - 1)) if n > 1 else 1.0
    gi_star[i] = (local_sum - expected) / denom if denom > 0 else 0.0

hex_gdf["gi_star_z"] = gi_star
hex_gdf_wm["gi_star_z"] = gi_star

fig, ax = plt.subplots(figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

hex_gdf_wm.plot(
    ax=ax, column="gi_star_z", cmap="RdBu_r",
    scheme="natural_breaks", k=7,
    linewidth=0.1, edgecolor="#222", alpha=0.85,
    legend=True,
    legend_kwds={
        "loc": "lower left", "fontsize": 9,
        "facecolor": "#1a1a2e", "edgecolor": "white",
        "labelcolor": "white", "framealpha": 0.9,
        "title": "Gi* z-score",
    },
)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"HOT / COLD SPOT DETECTION (Getis-Ord Gi*) -- {STUDY_AREA}\n"
    "Red = Statistically Significant Amenity Cluster | Blue = Cold Spot",
    fontsize=16, fontweight="bold", color="white", pad=20,
)

fig.tight_layout()
path_88 = FIGURES_DIR / "ch8_h3_hotspot_gi_star.png"
fig.savefig(path_88, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_88}")
print(f"    Hot spots (z>1.96) : {(gi_star > 1.96).sum():,} hexes")
print(f"    Cold spots (z<-1.96): {(gi_star < -1.96).sum():,} hexes")


# =====================================================================
# 8.9 — 3D Extruded Pydeck (Enhanced)
# =====================================================================
print("\n8.9 Enhanced 3D extruded Pydeck map ...")

hex_pydeck = hex_gdf.copy()
hex_pydeck["elevation"] = hex_pydeck["amenity_count"] * 40

max_val = hex_pydeck["amenity_count"].max() or 1
hex_pydeck["r"] = (hex_pydeck["amenity_count"] / max_val * 255).clip(0, 255).astype(int)
hex_pydeck["g"] = (100 - hex_pydeck["amenity_count"] / max_val * 60).clip(0, 255).astype(int)
hex_pydeck["b"] = (255 - hex_pydeck["r"]).clip(0, 255).astype(int)

view_state = pdk.ViewState(
    latitude=5.5600, longitude=-0.2057, zoom=11.5, pitch=50, bearing=15
)

layer_3d = pdk.Layer(
    "H3HexagonLayer",
    hex_pydeck,
    get_hexagon="h3_index",
    get_fill_color="[r, g, b, 200]",
    get_elevation="elevation",
    elevation_scale=1,
    extruded=True,
    pickable=True,
    auto_highlight=True,
)

deck_3d = pdk.Deck(
    layers=[layer_3d],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={
        "text": "H3: {h3_index}\nAmenities: {amenity_count}\nBuildings: {building_count}"
    },
)

html_3d = OUTPUT_DIR / "ch8_h3_3d_extruded.html"
deck_3d.to_html(str(html_3d))
print(f"    Saved -> {html_3d}")


# =====================================================================
# 8.10 — Interactive Dual-Metric Pydeck
# =====================================================================
print("\n8.10 Interactive dual-metric Pydeck ...")

hex_dual = hex_gdf.copy()
hex_dual["elevation"] = hex_dual["amenity_count"] * 50
max_bldg = hex_dual["building_count"].max() or 1
hex_dual["r"] = (hex_dual["building_count"] / max_bldg * 200 + 55).clip(0, 255).astype(int)
hex_dual["g"] = (120 - hex_dual["building_count"] / max_bldg * 80).clip(0, 255).astype(int)
hex_dual["b"] = (255 - hex_dual["building_count"] / max_bldg * 200).clip(0, 255).astype(int)

layer_dual = pdk.Layer(
    "H3HexagonLayer",
    hex_dual,
    get_hexagon="h3_index",
    get_fill_color="[r, g, b, 210]",
    get_elevation="elevation",
    elevation_scale=1,
    extruded=True,
    pickable=True,
    auto_highlight=True,
)

deck_dual = pdk.Deck(
    layers=[layer_dual],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={
        "text": "H3: {h3_index}\nAmenity Count (height): {amenity_count}\n"
                "Building Count (colour): {building_count}"
    },
)

html_dual = OUTPUT_DIR / "ch8_h3_dual_metric.html"
deck_dual.to_html(str(html_dual))
print(f"    Saved -> {html_dual}")


# =====================================================================
# 8.11 — PROFESSOR INNOVATION 1: MAUP Sensitivity Cascade
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 1: MAUP Sensitivity Cascade")
print("=" * 65)

test_resolutions = [7, 8, 9, 10, 11]
maup_stats = []

for res in test_resolutions:
    h3_ids = [
        h3.latlng_to_cell(lat, lng, res)
        for lat, lng in zip(amenities.geometry.y, amenities.geometry.x)
    ]
    counts = np.array(list(Counter(h3_ids).values()), dtype=float)
    n_cells = len(counts)
    cell_area = h3.cell_area(h3_ids[0], unit="km^2")

    mean_d = counts.mean()
    std_d = counts.std()
    cv = std_d / mean_d if mean_d > 0 else 0
    max_min = counts.max() / counts.min() if counts.min() > 0 else np.inf

    # Gini coefficient
    sorted_c = np.sort(counts)
    n_c = len(sorted_c)
    total_c = sorted_c.sum()
    cum = np.cumsum(sorted_c) / total_c if total_c > 0 else np.zeros(n_c)
    pop = np.linspace(0, 1, n_c)
    gini = 1.0 - 2.0 * np.trapz(cum, pop)

    maup_stats.append({
        "Resolution": res,
        "Cells": n_cells,
        "Cell Area (km2)": round(cell_area, 4),
        "Mean": round(mean_d, 2),
        "Std Dev": round(std_d, 2),
        "CV": round(cv, 3),
        "Gini": round(gini, 3),
        "Max/Min": round(max_min, 1) if max_min != np.inf else "inf",
    })

maup_df = pd.DataFrame(maup_stats)
print("\n    MAUP Statistics Across Resolutions:")
print(maup_df.to_string(index=False))

# Plot MAUP cascade
fig, axes = plt.subplots(1, 3, figsize=(24, 7))
fig.patch.set_facecolor(DARK_BG)

metrics = [
    ("CV", "Coefficient of Variation", "#ff9100"),
    ("Gini", "Gini Coefficient", "#e040fb"),
    ("Std Dev", "Standard Deviation", "#00e5ff"),
]

for ax, (col, label, color) in zip(axes, metrics):
    ax.set_facecolor(DARK_BG)
    vals = maup_df[col].astype(float).values
    ax.plot(test_resolutions, vals, color=color, linewidth=3,
            marker="o", markersize=10, markerfacecolor="white", markeredgecolor=color)
    ax.fill_between(test_resolutions, vals, alpha=0.15, color=color)
    ax.set_xlabel("H3 Resolution", color="white", fontsize=11)
    ax.set_ylabel(label, color="white", fontsize=11)
    ax.set_title(label, fontsize=14, fontweight="bold", color="white", pad=10)
    ax.tick_params(colors="white")
    ax.grid(True, linestyle="--", alpha=0.2, color="white")
    ax.set_xticks(test_resolutions)

fig.suptitle(
    "PROFESSOR'S INNOVATION 1 -- MAUP Sensitivity Cascade\n"
    "\"Same data, different resolution, different conclusions\"",
    fontsize=16, fontweight="bold", color="white", y=1.02,
)
fig.tight_layout()
path_p1 = FIGURES_DIR / "ch8_professor_maup_cascade.png"
fig.savefig(path_p1, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p1}")


# =====================================================================
# 8.12 — PROFESSOR INNOVATION 2: Shannon Spatial Entropy
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 2: Shannon Spatial Entropy & Evenness")
print("=" * 65)

def shannon_entropy(counts_array):
    """Compute normalised Shannon entropy (0=concentrated, 1=perfectly even)."""
    counts_array = counts_array[counts_array > 0]
    total = counts_array.sum()
    if total == 0 or len(counts_array) <= 1:
        return 0.0, 0.0
    probs = counts_array / total
    H = -np.sum(probs * np.log2(probs))
    H_max = np.log2(len(counts_array))
    H_norm = H / H_max if H_max > 0 else 0.0
    return H, H_norm


# Overall amenity entropy
overall_counts = hex_gdf["amenity_count"].values.astype(float)
H_overall, H_norm_overall = shannon_entropy(overall_counts)
print(f"\n    Overall Amenity Spatial Entropy:")
print(f"      H          = {H_overall:.3f} bits")
print(f"      H_norm     = {H_norm_overall:.3f} (0=concentrated, 1=even)")

# Per-category entropy
categories = ["Healthcare", "Education", "Commerce", "Worship"]
cat_entropies = {}

for cat in categories:
    cat_amenities = amenities[amenities["category"] == cat]
    cat_h3 = [
        h3.latlng_to_cell(lat, lng, H3_RES)
        for lat, lng in zip(cat_amenities.geometry.y, cat_amenities.geometry.x)
    ]
    cat_counts = np.array(list(Counter(cat_h3).values()), dtype=float)
    H_cat, H_norm_cat = shannon_entropy(cat_counts)
    cat_entropies[cat] = H_norm_cat
    print(f"    {cat:12s}: H_norm = {H_norm_cat:.3f}  (n={len(cat_amenities):,})")

# Bar chart
fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

cats = list(cat_entropies.keys()) + ["Overall"]
vals = list(cat_entropies.values()) + [H_norm_overall]
colors = ["#ff5252", "#29b6f6", "#ffd700", "#ab47bc", "#00e676"]

bars = ax.barh(cats, vals, color=colors, edgecolor="white", linewidth=0.8, height=0.6)

# Value labels
for bar, val in zip(bars, vals):
    ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}", va="center", ha="left", color="white", fontsize=12, fontweight="bold")

ax.set_xlim(0, 1.05)
ax.axvline(x=1.0, color="#78909c", linestyle="--", linewidth=1, alpha=0.5, label="Perfect Evenness")
ax.set_xlabel("Normalised Entropy (H_norm)", color="white", fontsize=12)
ax.set_title(
    "PROFESSOR'S INNOVATION 2 -- Shannon Spatial Entropy\n"
    "\"Which services are most unevenly distributed?\"",
    fontsize=14, fontweight="bold", color="white", pad=15,
)
ax.tick_params(colors="white")
ax.grid(True, axis="x", linestyle="--", alpha=0.2, color="white")

fig.tight_layout()
path_p2 = FIGURES_DIR / "ch8_professor_shannon_entropy.png"
fig.savefig(path_p2, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p2}")


# =====================================================================
# 8.13 — PROFESSOR INNOVATION 3: Hansen Gravity Accessibility Surface
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 3: Hansen Gravity Accessibility Surface")
print("=" * 65)

BETA = 0.5       # distance decay parameter
MAX_K = 6        # max ring distance to consider (beyond this, weight ≈ 0)

print(f"    Computing Hansen index (beta={BETA}, max_k={MAX_K}) ...")

hansen_scores = {}
for h in hex_gdf["h3_index"]:
    score = 0.0
    for k in range(0, MAX_K + 1):
        if k == 0:
            ring_cells = {h}
        else:
            try:
                ring_cells = set(h3.grid_ring(h, k))
            except Exception:
                ring_cells = set(h3.grid_disk(h, k)) - set(h3.grid_disk(h, k - 1))
        weight = np.exp(-BETA * k)
        for cell in ring_cells:
            score += hex_density.get(cell, 0) * weight
    hansen_scores[h] = score

hex_gdf["hansen_access"] = hex_gdf["h3_index"].map(hansen_scores)
hex_gdf_wm["hansen_access"] = hex_gdf["hansen_access"]

# Side-by-side: raw density vs Hansen accessibility
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(28, 14))
fig.patch.set_facecolor(DARK_BG)

for ax, col, cmap, title in [
    (ax1, "amenity_count", ACCENT_CMAP, "Raw Amenity Density"),
    (ax2, "hansen_access", "magma", "Hansen Accessibility Index"),
]:
    ax.set_facecolor(DARK_BG)
    hex_gdf_wm.plot(
        ax=ax, column=col, cmap=cmap,
        scheme="natural_breaks", k=7,
        linewidth=0.1, edgecolor="#222", alpha=0.85,
        legend=True,
        legend_kwds={
            "loc": "lower left", "fontsize": 8,
            "facecolor": "#1a1a2e", "edgecolor": "white",
            "labelcolor": "white", "framealpha": 0.9,
            "title": title,
        },
    )
    boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2, zorder=10)
    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
    except Exception:
        pass
    ax.set_axis_off()
    ax.set_title(title, fontsize=15, fontweight="bold", color="white", pad=12)

fig.suptitle(
    "PROFESSOR'S INNOVATION 3 -- Hansen Gravity Accessibility\n"
    "\"Density counts what's HERE. Accessibility counts what's REACHABLE.\"",
    fontsize=16, fontweight="bold", color="white", y=0.98,
)
fig.tight_layout(rect=[0, 0, 1, 0.93])
path_p3 = FIGURES_DIR / "ch8_professor_hansen_accessibility.png"
fig.savefig(path_p3, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p3}")

# Summary stats
h_vals = hex_gdf["hansen_access"].values
print(f"    Hansen min : {h_vals.min():.2f}")
print(f"    Hansen max : {h_vals.max():.2f}")
print(f"    Hansen mean: {h_vals.mean():.2f}")

# Correlation between raw density and Hansen
corr = np.corrcoef(hex_gdf["amenity_count"].values, h_vals)[0, 1]
print(f"    Correlation (density vs Hansen): r = {corr:.3f}")
print(f"    --> {'Strong' if abs(corr) > 0.7 else 'Moderate' if abs(corr) > 0.4 else 'Weak'} "
      f"correlation — the two metrics capture {'similar' if abs(corr) > 0.7 else 'different'} spatial patterns.")


print("\n" + "=" * 65)
print("  Chapter 8 complete.")
print("=" * 65)
