"""
=============================================================================
CHAPTER 3 — Buildings on OSM: Categorical & Continuous Building Maps
=============================================================================
Learning objectives
───────────────────
1. Extract building footprints from OSM
2. Classify buildings by type (residential, commercial, etc.)
3. Map building area as a continuous variable (choropleth)
4. Explore height / floors data (where available)
5. Produce the "hero" visualisation — building footprints colour-coded
   by area on a dark basemap (like the example image)

Ghana context
─────────────
Building height data in OSM is sparse for most African cities.  We
handle this gracefully: where height/floors are available we use them;
otherwise we fall back to footprint area, which is a strong proxy for
building importance and is well-mapped in Accra.

Professor's note
─────────────────
  "A city's built environment IS its buildings.  The footprint layer
   alone tells you about density, land consumption, morphological
   texture, and — indirectly — about socio-economic structure."
=============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import contextily as cx
import mapclassify
from config import (
    STUDY_AREA, CRS_WGS84, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    DATA_DIR, FIGURES_DIR, DARK_BG, BUILDING_TAGS, ACCENT_CMAP,
)

print("=" * 65)
print("  CHAPTER 3 — Buildings on OSM")
print("=" * 65)

# ── 3.1  Extract building footprints ─────────────────────────────────────
print("\n🏗  Pulling building footprints (this may take a minute) ...")
buildings_raw = ox.features_from_place(STUDY_AREA, tags=BUILDING_TAGS)
print(f"   Raw features returned: {len(buildings_raw)}")

# Keep only polygon/multipolygon geometries (drop nodes/linestrings)
buildings = buildings_raw[
    buildings_raw.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()
print(f"   Polygon footprints  : {len(buildings)}")

# ── 3.2  Compute footprint area (m²) ─────────────────────────────────────
buildings_proj = buildings.to_crs(CRS_UTM_ACCRA)
buildings["area_m2"] = buildings_proj.geometry.area
buildings["area_m2"] = buildings["area_m2"].round(1)

print(f"\n── Footprint area statistics ──")
print(buildings["area_m2"].describe().to_string())

# ── 3.3  Classify buildings by type ──────────────────────────────────────
if "building" in buildings.columns:
    # OSM 'building' tag: "yes", "residential", "commercial", etc.
    buildings["bldg_type"] = buildings["building"].fillna("unknown")
    print(f"\n── Building type breakdown ──")
    type_counts = buildings["bldg_type"].value_counts().head(15)
    for btype, n in type_counts.items():
        print(f"   {btype:25s}  {n:>6}")

# ── 3.4  Explore height & floors (where available) ───────────────────────
height_cols = ["height", "building:levels"]
for col in height_cols:
    if col in buildings.columns:
        available = buildings[col].notna().sum()
        pct = 100 * available / len(buildings)
        print(f"\n   {col}: {available} records ({pct:.1f}%)")
    else:
        print(f"\n   {col}: not present in data")

# Convert height/levels to numeric where possible
if "building:levels" in buildings.columns:
    buildings["levels"] = pd.to_numeric(
        buildings["building:levels"], errors="coerce"
    )
else:
    buildings["levels"] = np.nan

if "height" in buildings.columns:
    buildings["height_m"] = pd.to_numeric(
        buildings["height"], errors="coerce"
    )
else:
    buildings["height_m"] = np.nan

# ── 3.5  Save processed buildings ────────────────────────────────────────
save_cols = ["geometry", "area_m2", "bldg_type", "levels", "height_m"]
save_cols = [c for c in save_cols if c in buildings.columns]
buildings_save = buildings[save_cols].copy()
buildings_path = DATA_DIR / "buildings.gpkg"
buildings_save.to_file(buildings_path, driver="GPKG")
print(f"\n💾 Buildings saved → {buildings_path}")

# ── 3.6  HERO VISUALISATION — Building footprints by area ────────────────
# This replicates the example image: dark basemap + coloured footprints
print("\n🎨 Creating building footprint map (area choropleth) ...")

# Load boundary for clip
boundary = ox.geocode_to_gdf(STUDY_AREA)

# Filter out extremely large polygons (likely mapping artifacts)
q99 = buildings["area_m2"].quantile(0.99)
bldg_plot = buildings[buildings["area_m2"] <= q99].copy()

fig, ax = plt.subplots(1, 1, figsize=(16, 16))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

# Plot building footprints coloured by area
bldg_plot.to_crs(CRS_WEB_MERCATOR).plot(
    ax=ax,
    column="area_m2",
    cmap=ACCENT_CMAP,
    scheme="quantiles",
    k=7,
    linewidth=0.1,
    edgecolor="#333333",
    alpha=0.9,
    legend=False,
)

# Boundary outline
boundary.to_crs(CRS_WEB_MERCATOR).plot(
    ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10
)

# Dark basemap
cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=14)

ax.set_axis_off()
ax.set_title(
    f"Building Footprints by Area — {STUDY_AREA}",
    fontsize=18, fontweight="bold", color="white", pad=20,
)

# Custom colour bar
sm = plt.cm.ScalarMappable(
    cmap=ACCENT_CMAP,
    norm=mcolors.Normalize(
        vmin=bldg_plot["area_m2"].min(),
        vmax=bldg_plot["area_m2"].max()
    ),
)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.02, shrink=0.6)
cbar.set_label("Footprint Area (m²)", color="white", fontsize=11)
cbar.ax.yaxis.set_tick_params(color="white")
plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

fig.tight_layout()
fig_path = FIGURES_DIR / "ch3_buildings_area.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  Building area map → {fig_path}")

# ── 3.7  Categorical building map ────────────────────────────────────────
print("\n🎨 Creating categorical building type map ...")

# Define colour mapping for top building types
type_palette = {
    "yes":           "#ffc107",
    "residential":   "#4caf50",
    "commercial":    "#2196f3",
    "industrial":    "#ff5722",
    "retail":        "#e91e63",
    "church":        "#9c27b0",
    "school":        "#00bcd4",
    "mosque":        "#8bc34a",
    "hospital":      "#f44336",
    "warehouse":     "#795548",
}

if "bldg_type" in bldg_plot.columns:
    bldg_plot["color"] = bldg_plot["bldg_type"].map(type_palette)
    bldg_plot["color"] = bldg_plot["color"].fillna("#757575")

    fig, ax = plt.subplots(1, 1, figsize=(16, 16))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    bldg_plot.to_crs(CRS_WEB_MERCATOR).plot(
        ax=ax, color=bldg_plot["color"],
        linewidth=0.1, edgecolor="#222222", alpha=0.85,
    )

    boundary.to_crs(CRS_WEB_MERCATOR).plot(
        ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10
    )

    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=14)
    ax.set_axis_off()
    ax.set_title(
        f"Building Types — {STUDY_AREA}",
        fontsize=18, fontweight="bold", color="white", pad=20,
    )

    # Legend
    import matplotlib.patches as mpatches
    handles = [
        mpatches.Patch(color=c, label=t)
        for t, c in type_palette.items()
    ]
    ax.legend(
        handles=handles, loc="lower left", fontsize=8,
        facecolor="#1a1a2e", edgecolor="white",
        labelcolor="white", framealpha=0.9, ncol=2
    )

    fig.tight_layout()
    fig_path = FIGURES_DIR / "ch3_buildings_type.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"🖼  Building type map → {fig_path}")

print("\n✅ Chapter 3 complete.")
print("   You produced: building area choropleth + categorical type map.")
print("   Next → Chapter 4: Road networks")
