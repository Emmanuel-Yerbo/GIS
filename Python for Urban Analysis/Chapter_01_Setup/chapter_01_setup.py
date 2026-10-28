"""
=============================================================================
CHAPTER 1 — Setting Up: OpenStreetMap as a Data Source
=============================================================================
Learning objectives
───────────────────
1. Understand what OpenStreetMap (OSM) is and why it matters for Africa
2. Install and verify the Python geospatial stack
3. Define a study area and pull your first boundary polygon
4. Establish the "study-area pattern" used in every later chapter

Key concepts
────────────
• OSM's tag-based data model  (nodes → ways → relations)
• Nominatim geocoding          (place name → polygon)
• GeoDataFrame basics          (geometry + attributes in one table)
• Saving/loading spatial data  (GeoPackage — the modern shapefile)

Ghana context
─────────────
Accra is one of the best-mapped cities in Sub-Saharan Africa on OSM,
thanks to HOT (Humanitarian OpenStreetMap Team) mapathons and local
mapping communities.  We use Accra as our running case study — but
you can swap it for Kumasi, Tamale, Cape Coast, or any city on Earth.
=============================================================================
"""

import sys
import warnings
warnings.filterwarnings("ignore")

# ── 1.1  Verify the environment ───────────────────────────────────────────
print("=" * 65)
print("  CHAPTER 1 — Environment Check & Study-Area Setup")
print("=" * 65)

packages = {
    "osmnx":      None,
    "geopandas":  None,
    "pandas":     None,
    "numpy":      None,
    "matplotlib": None,
    "contextily": None,
    "networkx":   None,
    "shapely":    None,
    "folium":     None,
    "mapclassify": None,
}

for pkg in packages:
    try:
        mod = __import__(pkg)
        packages[pkg] = mod.__version__
        print(f"  ✓ {pkg:20s}  v{mod.__version__}")
    except ImportError:
        print(f"  ✗ {pkg:20s}  — NOT INSTALLED")

missing = [k for k, v in packages.items() if v is None]
if missing:
    print(f"\n⚠  Missing packages: {', '.join(missing)}")
    print("   Install with:  pip install -r requirements.txt")
    sys.exit(1)

# ── 1.2  Import the stack ─────────────────────────────────────────────────
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
from config import (
    STUDY_AREA, CRS_WGS84, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    DATA_DIR, FIGURES_DIR, DARK_BG
)

# ── 1.3  The Study-Area Pattern ───────────────────────────────────────────
# This is the single most important pattern in the course:
#   1. Define a place name  →  Nominatim resolves it to a polygon
#   2. Every later chapter clips its analysis to that polygon
#
# WHY this matters:
#   • Reproducibility — anyone can re-run with a different city name
#   • Efficiency      — you only download data you need
#   • Comparability   — same boundary = same denominator

print(f"\n📍 Study area: {STUDY_AREA}")

# Pull the administrative boundary from OSM via Nominatim
study_area_gdf = ox.geocode_to_gdf(STUDY_AREA)
print(f"   CRS           : {study_area_gdf.crs}")
print(f"   Geometry type : {study_area_gdf.geometry.iloc[0].geom_type}")
print(f"   Bounding box  : {study_area_gdf.total_bounds}")

# ── 1.4  Explore the boundary GeoDataFrame ────────────────────────────────
print("\n── Boundary attributes ──")
print(study_area_gdf[["display_name", "type", "geometry"]].to_string())

# Calculate area in sq-km using a metre-based CRS
area_m2 = study_area_gdf.to_crs(CRS_UTM_ACCRA).area.iloc[0]
area_km2 = area_m2 / 1e6
print(f"\n   Area ≈ {area_km2:.2f} km²")

# ── 1.5  Save to GeoPackage (the modern shapefile) ────────────────────────
boundary_path = DATA_DIR / "study_area_boundary.gpkg"
study_area_gdf.to_file(boundary_path, driver="GPKG")
print(f"\n💾 Boundary saved → {boundary_path}")

# ── 1.6  Visualise: boundary on a dark basemap ───────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(12, 12))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

# Plot boundary — semi-transparent fill + bright outline
study_area_gdf.to_crs(CRS_WEB_MERCATOR).plot(
    ax=ax,
    facecolor="none",
    edgecolor="#ffffff",
    linewidth=2.5,
)

# Add dark basemap tiles
cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter)

ax.set_axis_off()
ax.set_title(
    f"Study Area — {STUDY_AREA}",
    fontsize=16, fontweight="bold", color="white", pad=20
)

fig.tight_layout()
fig_path = FIGURES_DIR / "ch1_study_area.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  Figure saved  → {fig_path}")

# ── 1.7  Quick interactive map with Folium ────────────────────────────────
import folium

centroid = study_area_gdf.geometry.iloc[0].centroid
m = folium.Map(
    location=[centroid.y, centroid.x],
    zoom_start=12,
    tiles="CartoDB dark_matter",
)

# Add boundary as GeoJSON overlay
folium.GeoJson(
    study_area_gdf.to_json(),
    style_function=lambda x: {
        "fillColor": "transparent",
        "color": "#00e5ff",
        "weight": 3,
    },
    tooltip=STUDY_AREA,
).add_to(m)

map_path = OUTPUT_DIR / "ch1_study_area_interactive.html"
m.save(str(map_path))
print(f"🌐 Interactive map → {map_path}")

print("\n✅ Chapter 1 complete. You now have the study-area pattern.")
print("   Next → Chapter 2: Acquiring urban data from OSM")
