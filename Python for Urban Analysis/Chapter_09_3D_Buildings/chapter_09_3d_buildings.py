"""
=============================================================================
CHAPTER 9 — 3D Building Volumetrics, Morphometrics & Microclimate Proxies
=============================================================================
Master Class Edition — Python for Urban Analysis (Ghana Series)

Learning Objectives & Course Modules:
1.  9.1 Footprint Ingestion — Fetch & clean 2D building footprints via OSMnx
2.  9.2 Multi-Tier Height Engine — Integrate levels, explicit height, and area proxies
3.  9.3 Volumetric Engine — Compute Area (A), Height (H), Volume (V), and Gross Floor Area (GFA)
4.  9.4 Hexagonal FAR Aggregation — Aggregate Floor Area Ratio (FAR) on H3 Res 9 grid
5.  9.5 Statistical Height Distribution — Histogram, quantiles, and volumetric distribution
6.  9.6 Footprint vs Volume Comparison — Dual-panel 2D choropleth (Flat vs 3D Density)
7.  9.7 District Volumetric Rankings — Rank Accra's MMDAs by volume & 95th percentile height
8.  9.8 Interactive 3D Pydeck Cityscape — WebGL pitch=60° 3D extrusion skyline
9.  9.9 Interactive Dual-Metric Pydeck — Height = Building Height, Color = FAR Density
10. Professor Innovation 1: Sky View Factor (SVF) & Urban Canyon Proxy (Oke, 1988)
11. Professor Innovation 2: Spatial Floor Area Ratio (FAR) & Sprawl Index (Leslie & Martin, 1972)
12. Professor Innovation 3: Volumetric Thermal Mass & UHI Vulnerability (Voogt & Oke, 2003)

Ghana Context:
Evaluates Greater Accra's vertical urban form, contrasting high-density commercial
towers (Airport City, Ridge, Osu) with horizontal low-rise compound sprawl, and
quantifying urban microclimate implications (SVF & Thermal Mass).

Professor's Note:
  "Urban density is three-dimensional. A flat 2D footprint map treats a 10-story
   hospital the same as a 1-story shed. By computing Gross Floor Area, Volume,
   Sky View Factor, and Thermal Mass, we bridge spatial data science, architecture,
   and microclimate physics."
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
from config import (
    STUDY_AREA, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    OUTPUT_DIR, FIGURES_DIR, DARK_BG, ACCENT_CMAP, BUILDING_TAGS,
)

print("=" * 65)
print("  CHAPTER 9 — 3D Building Volumetrics & Urban Morphology (Master)")
print("=" * 65)


# =====================================================================
# UTILITY — Convert H3 cell to Shapely Polygon
# =====================================================================
def h3_to_polygon(h3_idx):
    """Convert an H3 cell index to a Shapely Polygon (lon/lat)."""
    boundary_coords = h3.cell_to_boundary(h3_idx)
    return Polygon([(lon, lat) for lat, lon in boundary_coords])


# =====================================================================
# 9.1 — Fetch & Clean Building Footprints
# =====================================================================
print(f"\n9.1 Fetching building footprints for: {STUDY_AREA} ...")

boundary = ox.geocode_to_gdf(STUDY_AREA)
boundary_wm = boundary.to_crs(CRS_WEB_MERCATOR)
boundary_poly = boundary.geometry.iloc[0]

buildings_raw = ox.features_from_place(STUDY_AREA, tags=BUILDING_TAGS)
buildings = buildings_raw[
    buildings_raw.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()
buildings = buildings[buildings.geometry.within(boundary_poly)].copy()

print(f"    Raw building footprints fetched: {len(buildings):,}")


# =====================================================================
# 9.2 — Multi-Tier Height Ingestion Engine & 3D Volumetrics
# =====================================================================
print("\n9.2 & 9.3 Executing Multi-Tier Height & 3D Volumetrics Engine ...")

# Project to UTM for metric area calculation
buildings_utm = buildings.to_crs(CRS_UTM_ACCRA)
buildings["area_m2"] = buildings_utm.geometry.area.round(1)

def estimate_height(row):
    # Tier 1: building:levels
    levels = row.get("building:levels")
    try:
        if pd.notna(levels) and float(levels) > 0:
            return float(levels) * 3.5
    except Exception:
        pass

    # Tier 2: explicit height tag
    height = row.get("height")
    try:
        if pd.notna(height):
            clean_h = float(str(height).replace("m", "").replace("ft", "").strip())
            if clean_h > 0:
                return clean_h
    except Exception:
        pass

    # Tier 3: Building type heuristic
    btype = str(row.get("building", "")).lower()
    if btype in ["apartments", "commercial", "office", "hospital", "university"]:
        base_h = 12.0
    elif btype in ["industrial", "warehouse", "retail"]:
        base_h = 7.0
    elif btype in ["house", "residential", "detached", "hut", "kiosk"]:
        base_h = 4.0
    else:
        base_h = 4.5

    # Tier 4: Log-area volumetric scale proxy
    area = row["area_m2"]
    area_boost = float(np.log1p(area) * 0.8)
    return float(np.clip(base_h + area_boost, 3.5, 90.0))

buildings["height_m"] = buildings.apply(estimate_height, axis=1)

# Compute 3D metrics
buildings["floors"] = np.maximum(1, np.floor(buildings["height_m"] / 3.5)).astype(int)
buildings["volume_m3"] = buildings["area_m2"] * buildings["height_m"]
buildings["gfa_m2"] = buildings["area_m2"] * buildings["floors"]

print(f"    Height Statistics (m)   : Min={buildings['height_m'].min():.1f}, Max={buildings['height_m'].max():.1f}, Mean={buildings['height_m'].mean():.1f}")
print(f"    Total Built Volume (m³) : {buildings['volume_m3'].sum():,.0f}")
print(f"    Total Gross Floor Area  : {buildings['gfa_m2'].sum():,.0f} m²")


# =====================================================================
# 9.4 — H3 Hexagonal FAR & Volumetric Density Aggregation
# =====================================================================
print("\n9.4 Indexing 3D Volumetrics into H3 Hexagons (Res 9) ...")

H3_RES = 9
buildings["centroid"] = buildings.geometry.centroid

bldg_h3 = [
    h3.latlng_to_cell(lat, lng, H3_RES)
    for lat, lng in zip(buildings["centroid"].y, buildings["centroid"].x)
]
buildings["h3_index"] = bldg_h3

# Aggregate volume, GFA, footprint area per hex
hex_vol = buildings.groupby("h3_index").agg(
    bldg_count=("area_m2", "count"),
    total_footprint_m2=("area_m2", "sum"),
    total_volume_m3=("volume_m3", "sum"),
    total_gfa_m2=("gfa_m2", "sum"),
    mean_height_m=("height_m", "mean"),
    max_height_m=("height_m", "max"),
).reset_index()

hex_vol["geometry"] = hex_vol["h3_index"].apply(h3_to_polygon)
hex_gdf = gpd.GeoDataFrame(hex_vol, geometry="geometry", crs="EPSG:4326")

# Calculate Cell Land Area & Floor Area Ratio (FAR)
# H3 Res 9 cell area is approx 100,000 m² (0.1 km²)
cell_area_m2 = h3.cell_area(list(hex_gdf["h3_index"])[0], unit="m^2")
hex_gdf["far"] = hex_gdf["total_gfa_m2"] / cell_area_m2
hex_gdf["bcr"] = (hex_gdf["total_footprint_m2"] / cell_area_m2).clip(0, 1)  # Building Coverage Ratio

hex_gdf_wm = hex_gdf.to_crs(CRS_WEB_MERCATOR)

print(f"    Hexagons covered   : {len(hex_gdf):,}")
print(f"    Max FAR observed   : {hex_gdf['far'].max():.2f}")
print(f"    Mean FAR across city: {hex_gdf['far'].mean():.3f}")


# =====================================================================
# 9.5 — Statistical Height Distribution & Volumetric Metrics
# =====================================================================
print("\n9.5 Plotting building height distribution ...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
fig.patch.set_facecolor(DARK_BG)

# Plot 1: Height Histogram
ax1.set_facecolor(DARK_BG)
ax1.hist(buildings["height_m"], bins=45, color="#ff9800", edgecolor="#111", alpha=0.85)
ax1.axvline(buildings["height_m"].mean(), color="white", linestyle="--", linewidth=1.5, label=f"Mean ({buildings['height_m'].mean():.1f}m)")
ax1.axvline(buildings["height_m"].median(), color="#00e5ff", linestyle=":", linewidth=1.5, label=f"Median ({buildings['height_m'].median():.1f}m)")
ax1.set_title(f"Building Height Distribution -- {STUDY_AREA}", fontsize=14, fontweight="bold", color="white", pad=15)
ax1.set_xlabel("Estimated Height (meters)", color="white", fontsize=11)
ax1.set_ylabel("Building Footprint Count", color="white", fontsize=11)
ax1.tick_params(colors="white")
ax1.grid(True, linestyle="--", alpha=0.2, color="white")
ax1.legend(loc="upper right", facecolor="#1a1a2e", edgecolor="white", labelcolor="white")

# Plot 2: Log Volume vs Height Scatter
ax2.set_facecolor(DARK_BG)
scatter = ax2.scatter(
    buildings["area_m2"], buildings["height_m"],
    c=buildings["volume_m3"], cmap="YlOrRd", s=8, alpha=0.6,
)
ax2.set_xscale("log")
ax2.set_title("Footprint Area vs. Height (Color = Volume)", fontsize=14, fontweight="bold", color="white", pad=15)
ax2.set_xlabel("Footprint Area (m², log scale)", color="white", fontsize=11)
ax2.set_ylabel("Height (meters)", color="white", fontsize=11)
ax2.tick_params(colors="white")
ax2.grid(True, linestyle="--", alpha=0.2, color="white")
cbar = plt.colorbar(scatter, ax=ax2)
cbar.ax.yaxis.set_tick_params(color="white")
plt.setp(plt.getp(cbar.ax, "yticklabels"), color="white")
cbar.set_label("Volume (m³)", color="white")

fig.tight_layout()
path_95 = FIGURES_DIR / "ch9_building_heights.png"
fig.savefig(path_95, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_95}")


# =====================================================================
# 9.6 — Dual 2D Spatial Comparison (Footprint Density vs 3D Volume)
# =====================================================================
print("\n9.6 Dual 2D Spatial Comparison: 2D Footprints vs 3D Volume ...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(28, 14))
fig.patch.set_facecolor(DARK_BG)

for ax, col, cmap, title in [
    (ax1, "total_footprint_m2", "YlGnBu", "2D Building Footprint Area (m²)"),
    (ax2, "total_volume_m3", "YlOrRd", "3D Gross Building Volume (m³)"),
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
    f"2D FOOTPRINT DENSITY vs 3D VOLUMETRIC DENSITY -- {STUDY_AREA}",
    fontsize=18, fontweight="bold", color="white", y=0.97,
)
fig.tight_layout(rect=[0, 0, 1, 0.94])
path_96 = FIGURES_DIR / "ch9_footprint_vs_volume_comparison.png"
fig.savefig(path_96, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_96}")


# =====================================================================
# 9.7 — District-Level Volumetric Ranking & Skyline Profiles
# =====================================================================
print("\n9.7 District-Level Volumetric Ranking & Skyline Profiles ...")

# Spatial join buildings to districts (MMDAs)
try:
    district_names = [
        "Accra Metropolitan District, Greater Accra, Ghana",
        "Ablekuma Central Municipal District, Greater Accra, Ghana",
        "Ablekuma West Municipal District, Greater Accra, Ghana",
        "Ayawaso Central Municipal District, Greater Accra, Ghana",
        "Ayawaso East Municipal District, Greater Accra, Ghana",
        "Ayawaso West Municipal District, Greater Accra, Ghana",
        "Korle Klottey Municipal District, Greater Accra, Ghana",
        "La Dade-Kotopon Municipal District, Greater Accra, Ghana",
        "Okaikwei North Municipal District, Greater Accra, Ghana",
        "Tema Metropolitan District, Greater Accra, Ghana",
    ]
    districts_gdf = ox.geocode_to_gdf(district_names)
    bldgs_with_dist = gpd.sjoin(
        buildings.to_crs(districts_gdf.crs), districts_gdf[["display_name", "geometry"]],
        how="inner", predicate="within",
    )
    bldgs_with_dist["district_clean"] = bldgs_with_dist["display_name"].apply(
        lambda s: str(s).split(",")[0].replace("Municipal District", "").replace("Metropolitan District", "").strip()
    )

    dist_stats = bldgs_with_dist.groupby("district_clean").agg(
        total_vol_m3=("volume_m3", "sum"),
        p95_height=("height_m", lambda x: np.percentile(x, 95)),
        mean_height=("height_m", "mean"),
        count=("area_m2", "count"),
    ).reset_index().sort_values(by="total_vol_m3", ascending=False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    fig.patch.set_facecolor(DARK_BG)

    # Plot 1: Total Volume per District
    ax1.set_facecolor(DARK_BG)
    ax1.barh(dist_stats["district_clean"], dist_stats["total_vol_m3"] / 1e6, color="#ff9800", edgecolor="white", linewidth=0.8)
    ax1.set_xlabel("Total Built Volume (Million m³)", color="white", fontsize=11)
    ax1.set_title("District Ranking by Total Built Volume", fontsize=14, fontweight="bold", color="white", pad=12)
    ax1.tick_params(colors="white")
    ax1.grid(True, axis="x", linestyle="--", alpha=0.2, color="white")
    ax1.invert_yaxis()

    # Plot 2: 95th Percentile Height per District
    ax2.set_facecolor(DARK_BG)
    ax2.barh(dist_stats["district_clean"], dist_stats["p95_height"], color="#00e5ff", edgecolor="white", linewidth=0.8)
    ax2.set_xlabel("95th Percentile Building Height (m)", color="white", fontsize=11)
    ax2.set_title("District Ranking by Peak Skyline Height", fontsize=14, fontweight="bold", color="white", pad=12)
    ax2.tick_params(colors="white")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.2, color="white")
    ax2.invert_yaxis()

    fig.suptitle(f"DISTRICT SKYLINE & VOLUMETRIC PROFILES -- {STUDY_AREA}", fontsize=16, fontweight="bold", color="white", y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    path_97 = FIGURES_DIR / "ch9_district_skyline_rankings.png"
    fig.savefig(path_97, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"    Saved -> {path_97}")

except Exception as e:
    print(f"    District spatial join skipped: {e}")


# =====================================================================
# 9.8 — Interactive 3D Pydeck Cityscape (Extruded Polygons)
# =====================================================================
print("\n9.8 Rendering Interactive 3D Pydeck Cityscape ...")

# Filter out micro-footprints (< 15 m²) and 99th percentile area outliers to optimize WebGL rendering
q99_area = buildings["area_m2"].quantile(0.99)
bldg_filtered = buildings[
    (buildings["area_m2"] >= 15.0) & (buildings["area_m2"] <= q99_area)
].copy()

# Cap at top 25,000 prominent structures by volume to prevent Pydeck memory/WebGL browser crashes
if len(bldg_filtered) > 25000:
    print(f"    [Optimization] Capping {len(bldg_filtered):,} buildings to top 25,000 by volume for smooth 3D WebGL rendering ...")
    bldg_filtered = bldg_filtered.sort_values(by="volume_m3", ascending=False).head(25000)

bldg_filtered = bldg_filtered.to_crs("EPSG:4326").copy()

def get_coordinates(geom):
    if geom.geom_type == "Polygon":
        return [list(coord)[:2] for coord in geom.exterior.coords]
    elif geom.geom_type == "MultiPolygon":
        return [list(coord)[:2] for coord in list(geom.geoms)[0].exterior.coords]
    return []

bldg_filtered["polygon"] = bldg_filtered.geometry.apply(get_coordinates)
bldg_filtered = bldg_filtered[bldg_filtered["polygon"].apply(len) > 0].copy()

max_h = bldg_filtered["height_m"].quantile(0.98) or 1
bldg_filtered["norm_h"] = (bldg_filtered["height_m"] / max_h).clip(0, 1)

# Color gradient: Low (cyan/blue) -> Mid (yellow) -> High (bright red/orange)
bldg_filtered["r"] = (255 * bldg_filtered["norm_h"]).astype(int)
bldg_filtered["g"] = (180 * (1 - bldg_filtered["norm_h"])).astype(int)
bldg_filtered["b"] = (255 * (1 - bldg_filtered["norm_h"])).astype(int)
bldg_filtered["color"] = bldg_filtered.apply(
    lambda row: [int(row["r"]), int(row["g"]), int(row["b"]), 220], axis=1
)

view_state = pdk.ViewState(
    latitude=5.5600, longitude=-0.2057, zoom=14, pitch=60, bearing=-20
)

layer_3d_skyline = pdk.Layer(
    "PolygonLayer",
    bldg_filtered,
    get_polygon="polygon",
    get_elevation="height_m",
    get_fill_color="color",
    extruded=True,
    wireframe=True,
    get_line_color=[30, 30, 30, 100],
    line_width_min_pixels=1,
    pickable=True,
    auto_highlight=True,
)

deck_skyline = pdk.Deck(
    layers=[layer_3d_skyline],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={
        "text": "Building Height: {height_m}m\nEstimated Floors: {floors}\nFootprint Area: {area_m2} m²\nGross Volume: {volume_m3} m³"
    },
)

html_skyline = OUTPUT_DIR / "ch9_3d_accra_skyline.html"
deck_skyline.to_html(str(html_skyline))
print(f"    Saved -> {html_skyline}")


# =====================================================================
# 9.9 — Interactive Dual-Metric 3D Deck (Height=H, Color=FAR)
# =====================================================================
print("\n9.9 Rendering Interactive Dual-Metric 3D Pydeck Deck ...")

hex_dual_3d = hex_gdf.copy()
hex_dual_3d["elevation"] = hex_dual_3d["max_height_m"] * 15

max_far = hex_dual_3d["far"].quantile(0.98) or 1
hex_dual_3d["r"] = (255 * (hex_dual_3d["far"] / max_far).clip(0, 1)).astype(int)
hex_dual_3d["g"] = (140 * (1 - hex_dual_3d["far"] / max_far).clip(0, 1)).astype(int)
hex_dual_3d["b"] = (255 * (1 - hex_dual_3d["far"] / max_far).clip(0, 1)).astype(int)

layer_far_3d = pdk.Layer(
    "H3HexagonLayer",
    hex_dual_3d,
    get_hexagon="h3_index",
    get_fill_color="[r, g, b, 210]",
    get_elevation="elevation",
    elevation_scale=1,
    extruded=True,
    pickable=True,
    auto_highlight=True,
)

deck_far_3d = pdk.Deck(
    layers=[layer_far_3d],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={
        "text": "H3 Cell: {h3_index}\nMax Building Height: {max_height_m}m\nFloor Area Ratio (FAR): {far}\nTotal Built Volume: {total_volume_m3} m³"
    },
)

html_far = OUTPUT_DIR / "ch9_3d_far_volumetric.html"
deck_far_3d.to_html(str(html_far))
print(f"    Saved -> {html_far}")


# =====================================================================
# 9.10 — PROFESSOR INNOVATION 1: Sky View Factor (SVF) & Urban Canyon
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 1: Sky View Factor (SVF) & Urban Canyon Proxy")
print("=" * 65)

# Oke (1988) urban canyon model: SVF = cos(arctan(2 * H / W))
# We estimate mean street width W = 15.0 m for Accra urban fabric
STREET_WIDTH_M = 15.0

hex_gdf["svf_proxy"] = np.cos(
    np.arctan(2.0 * hex_gdf["mean_height_m"] / STREET_WIDTH_M)
).clip(0.1, 1.0)
hex_gdf_wm["svf_proxy"] = hex_gdf["svf_proxy"]

print(f"    SVF Statistics          : Min={hex_gdf['svf_proxy'].min():.3f}, Max={hex_gdf['svf_proxy'].max():.3f}, Mean={hex_gdf['svf_proxy'].mean():.3f}")

fig, ax = plt.subplots(figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

hex_gdf_wm.plot(
    ax=ax, column="svf_proxy", cmap="viridis_r",  # Darker = lower SVF (trapped radiation)
    scheme="natural_breaks", k=7,
    linewidth=0.1, edgecolor="#222", alpha=0.85,
    legend=True,
    legend_kwds={
        "loc": "lower left", "fontsize": 9,
        "facecolor": "#1a1a2e", "edgecolor": "white",
        "labelcolor": "white", "framealpha": 0.9,
        "title": "Sky View Factor (SVF)",
    },
)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"PROFESSOR'S INNOVATION 1 -- Sky View Factor (SVF) Urban Canyon Proxy\n"
    "Lower SVF (Dark) = High Urban Canyon Enclosure | Higher SVF (Bright) = Open Sky Access",
    fontsize=16, fontweight="bold", color="white", pad=20,
)

fig.tight_layout()
path_p1 = FIGURES_DIR / "ch9_professor_sky_view_factor.png"
fig.savefig(path_p1, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p1}")


# =====================================================================
# 9.11 — PROFESSOR INNOVATION 2: Spatial Floor Area Ratio (FAR)
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 2: Spatial Floor Area Ratio (FAR) & Sprawl Index")
print("=" * 65)

# Leslie & Martin (1972): FAR = Total Gross Floor Area / Land Area
fig, ax = plt.subplots(figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

hex_gdf_wm.plot(
    ax=ax, column="far", cmap="magma",
    scheme="natural_breaks", k=7,
    linewidth=0.1, edgecolor="#222", alpha=0.85,
    legend=True,
    legend_kwds={
        "loc": "lower left", "fontsize": 9,
        "facecolor": "#1a1a2e", "edgecolor": "white",
        "labelcolor": "white", "framealpha": 0.9,
        "title": "Floor Area Ratio (FAR)",
    },
)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"PROFESSOR'S INNOVATION 2 -- Spatial Floor Area Ratio (FAR) & Urban Intensity\n"
    "Quantifying Vertical Compaction (High FAR) vs. Horizontal Sprawl (Low FAR)",
    fontsize=16, fontweight="bold", color="white", pad=20,
)

fig.tight_layout()
path_p2 = FIGURES_DIR / "ch9_professor_spatial_far.png"
fig.savefig(path_p2, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p2}")


# =====================================================================
# 9.12 — PROFESSOR INNOVATION 3: Volumetric Thermal Mass & UHI Proxy
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 3: Volumetric Thermal Mass & UHI Vulnerability")
print("=" * 65)

# Voogt & Oke (2003): Thermal Mass Index TMI = Total Building Volume / Cell Area
hex_gdf["tmi_m"] = hex_gdf["total_volume_m3"] / cell_area_m2
hex_gdf_wm["tmi_m"] = hex_gdf["tmi_m"]

print(f"    Thermal Mass Index (m) : Min={hex_gdf['tmi_m'].min():.2f}, Max={hex_gdf['tmi_m'].max():.2f}, Mean={hex_gdf['tmi_m'].mean():.2f}")

fig, ax = plt.subplots(figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

hex_gdf_wm.plot(
    ax=ax, column="tmi_m", cmap="inferno",
    scheme="natural_breaks", k=7,
    linewidth=0.1, edgecolor="#222", alpha=0.85,
    legend=True,
    legend_kwds={
        "loc": "lower left", "fontsize": 9,
        "facecolor": "#1a1a2e", "edgecolor": "white",
        "labelcolor": "white", "framealpha": 0.9,
        "title": "Thermal Mass Index (V / A)",
    },
)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"PROFESSOR'S INNOVATION 3 -- Volumetric Thermal Mass & UHI Vulnerability\n"
    "Higher TMI (Bright Yellow) = Extreme Concrete Mass & Nocturnal Heat Retention Risk",
    fontsize=16, fontweight="bold", color="white", pad=20,
)

fig.tight_layout()
path_p3 = FIGURES_DIR / "ch9_professor_thermal_mass_uhi.png"
fig.savefig(path_p3, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p3}")


print("\n" + "=" * 65)
print("  Chapter 9 complete.")
print("=" * 65)
