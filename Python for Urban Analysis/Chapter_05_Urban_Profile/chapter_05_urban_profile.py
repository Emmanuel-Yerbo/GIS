"""
=============================================================================
CHAPTER 5 — The Urban Profile: Base Maps & Composed Layers
=============================================================================
Learning objectives
───────────────────
1. Create polished base maps with contextily
2. Compose multiple urban layers into a single "urban profile" figure
3. Build a reusable multi-panel layout showing all city layers
4. Apply professional cartographic styling

Ghana context
─────────────
This chapter composes everything we've built — boundary, buildings,
roads, amenities, green spaces — into a single reference figure for
Accra that works as a "city dashboard" or portfolio piece.

Professor's note
─────────────────
  "The urban profile is your single-page summary of a city's
   spatial DNA. It tells any stakeholder — planner, investor,
   researcher — what a city looks like at a glance."
=============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as cx
from config import (
    STUDY_AREA, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    FIGURES_DIR, DARK_BG, ACCENT_CMAP, AMENITY_COLOR,
    AMENITY_TAGS, BUILDING_TAGS, LEISURE_TAGS,
)

print("=" * 65)
print("  CHAPTER 5 — The Urban Profile")
print("=" * 65)

# ── 5.1  Fetch All Urban Layers Directly from OpenStreetMap ─────────────
print(f"\n🌐 Fetching Urban Layers from OpenStreetMap for: {STUDY_AREA} ...")

# 1. Geocode Study Area Boundary
boundary = ox.geocode_to_gdf(STUDY_AREA)
boundary_wm = boundary.to_crs(CRS_WEB_MERCATOR)
print(f"   ✓ Boundary   : Geocoded {STUDY_AREA}")

# 2. Fetch & Process Building Footprints
buildings_raw = ox.features_from_place(STUDY_AREA, tags=BUILDING_TAGS)
buildings = buildings_raw[
    buildings_raw.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()
buildings["area_m2"] = buildings.to_crs(CRS_UTM_ACCRA).geometry.area.round(1)
buildings_wm = buildings.to_crs(CRS_WEB_MERCATOR)
print(f"   ✓ Buildings  : {len(buildings):,} footprints (area computed)")

# 3. Fetch & Process Amenities (Points of Interest)
amenities_raw = ox.features_from_place(STUDY_AREA, tags=AMENITY_TAGS).copy()
amenities = amenities_raw.copy()
amenities["geometry"] = amenities.geometry.centroid
amenities = amenities[amenities.geometry.within(boundary.geometry.iloc[0])].copy()
amenities_wm = amenities.to_crs(CRS_WEB_MERCATOR)
print(f"   ✓ Amenities  : {len(amenities):,} POIs")

# 4. Fetch & Process Drivable Road Network Graph
G_drive = ox.graph_from_place(STUDY_AREA, network_type="drive")
roads = ox.graph_to_gdfs(G_drive, nodes=False, edges=True)
roads_wm = roads.to_crs(CRS_WEB_MERCATOR)
print(f"   ✓ Roads      : {len(roads):,} edges")

# 5. Fetch & Process Leisure & Green Space Polygons
leisure_raw = ox.features_from_place(STUDY_AREA, tags=LEISURE_TAGS)
leisure = leisure_raw[
    leisure_raw.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
].copy()
leisure_wm = leisure.to_crs(CRS_WEB_MERCATOR)
print(f"   ✓ Leisure    : {len(leisure):,} features")

# ── 5.2  Single-layer panel renderer ─────────────────────────────────────
def make_layer_panel(ax, title, plot_fn):
    """Helper: configure a dark-themed panel and plot a layer."""
    ax.set_facecolor(DARK_BG)
    plot_fn(ax)
    boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=1.5)
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
    ax.set_axis_off()
    ax.set_title(title, fontsize=11, fontweight="bold", color="white", pad=8)

# ── 5.3  Compose the Urban Profile — 2×2 multi-panel ────────────────────
print("\n🎨 Composing the Urban Profile (2×2 panels) ...")

fig, axes = plt.subplots(2, 2, figsize=(20, 20))
fig.patch.set_facecolor(DARK_BG)
fig.suptitle(
    f"URBAN PROFILE — {STUDY_AREA.upper()}",
    fontsize=22, fontweight="bold", color="white", y=0.98
)

# Panel 1: Buildings by area
def plot_buildings(ax):
    q99 = buildings_wm["area_m2"].quantile(0.99)
    bldg = buildings_wm[buildings_wm["area_m2"] <= q99]
    bldg.plot(
        ax=ax, column="area_m2", cmap=ACCENT_CMAP,
        scheme="quantiles", k=7,
        linewidth=0.05, edgecolor="#222", alpha=0.9,
        legend=False,
    )
make_layer_panel(axes[0, 0], "Buildings (by footprint area)", plot_buildings)

# Panel 2: Road network
def plot_roads(ax):
    roads_wm.plot(ax=ax, color="#ff9100", linewidth=0.3, alpha=0.7)
make_layer_panel(axes[0, 1], "Road Network (drivable)", plot_roads)

# Panel 3: Points of Interest
def plot_amenities(ax):
    amenities_wm.plot(
        ax=ax, color=AMENITY_COLOR, markersize=5, alpha=0.7, zorder=5
    )
make_layer_panel(axes[1, 0], "Points of Interest (amenities)", plot_amenities)

# Panel 4: All layers composed
def plot_all(ax):
    if len(leisure_wm) > 0:
        leisure_wm.plot(ax=ax, color="#66bb6a", alpha=0.4)
    buildings_wm.plot(
        ax=ax, color="#ffc107", linewidth=0, alpha=0.5
    )
    roads_wm.plot(ax=ax, color="#78909c", linewidth=0.2, alpha=0.5)
    amenities_wm.plot(
        ax=ax, color=AMENITY_COLOR, markersize=3, alpha=0.8, zorder=5
    )
make_layer_panel(axes[1, 1], "All Layers Composed", plot_all)

# Combined legend for bottom-right panel
legend_items = [
    mpatches.Patch(color="#ffc107", label="Buildings"),
    mpatches.Patch(color="#78909c", label="Roads"),
    mpatches.Patch(color=AMENITY_COLOR, label="Amenities"),
    mpatches.Patch(color="#66bb6a", label="Green/Leisure"),
]
axes[1, 1].legend(
    handles=legend_items, loc="lower left", fontsize=8,
    facecolor="#1a1a2e", edgecolor="white",
    labelcolor="white", framealpha=0.9,
)

fig.tight_layout(rect=[0, 0, 1, 0.96])
fig_path = FIGURES_DIR / "ch5_urban_profile.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  Urban Profile → {fig_path}")

# ── 5.4  Hero single-canvas map (all layers, one panel) ─────────────────
print("\n🎨 Creating hero single-canvas map ...")

fig, ax = plt.subplots(1, 1, figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

# Layer 1: Green spaces (bottom)
if len(leisure_wm) > 0:
    leisure_wm.plot(ax=ax, color="#2e7d32", alpha=0.5, zorder=1)

# Layer 2: Buildings
q99 = buildings_wm["area_m2"].quantile(0.99)
bldg = buildings_wm[buildings_wm["area_m2"] <= q99]
bldg.plot(
    ax=ax, column="area_m2", cmap=ACCENT_CMAP,
    scheme="quantiles", k=7,
    linewidth=0.05, edgecolor="#111", alpha=0.85,
    legend=False, zorder=2,
)

# Layer 3: Roads
roads_wm.plot(ax=ax, color="#546e7a", linewidth=0.2, alpha=0.3, zorder=3)

# Layer 4: Amenities (top)
amenities_wm.plot(
    ax=ax, color=AMENITY_COLOR, markersize=6, alpha=0.9, zorder=5
)

# Boundary
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=3, zorder=10)

cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=14)
ax.set_axis_off()
ax.set_title(
    f"Complete Urban Profile — {STUDY_AREA}",
    fontsize=20, fontweight="bold", color="white", pad=20,
)

fig.tight_layout()
fig_path = FIGURES_DIR / "ch5_hero_map.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  Hero map → {fig_path}")

print("\n✅ Chapter 5 complete.")
print("   You composed all layers directly from OpenStreetMap into a reusable urban profile.")
print("   Next → Chapter 6: Livability Index")
