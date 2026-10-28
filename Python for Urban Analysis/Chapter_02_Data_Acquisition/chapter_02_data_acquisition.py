"""
=============================================================================
CHAPTER 2 — Acquiring Urban Data from OSM
=============================================================================
Learning objectives
───────────────────
1. Pull administrative boundaries at multiple levels (region → district)
2. Extract Points of Interest (POI) — hospitals, schools, markets, etc.
3. Extract polygon features — parks, leisure, water bodies
4. Understand OSM tags and how to compose custom queries
5. Visualise POI density and spatial distribution

Ghana context
─────────────
Greater Accra Region has 29 MMDAs (Metropolitan, Municipal, and District
Assemblies).  We pull district-level boundaries — analogous to Vienna's
23 Bezirke — so that Chapter 6 can score each one for livability.

Professor's note
─────────────────
  "Before you can analyse a city, you must *acquire* it.  OSM is
   the largest free geographic database on Earth.  Learning to
   query it efficiently is the single most transferable skill in
   urban data science."
=============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as cx
import folium
from config import (
    STUDY_AREA, STUDY_REGION, CRS_WGS84, CRS_WEB_MERCATOR,
    CRS_UTM_ACCRA, DATA_DIR, FIGURES_DIR, DARK_BG,
    AMENITY_TAGS, LEISURE_TAGS, AMENITY_COLOR,
)

print("=" * 65)
print("  CHAPTER 2 — Acquiring Urban Data from OSM")
print("=" * 65)

# ── 2.1  Administrative boundaries ────────────────────────────────────────
# Pull city-level boundary (already done in Ch 1, but we reload cleanly)
print("\n📍 Pulling study-area boundary ...")
boundary = ox.geocode_to_gdf(STUDY_AREA)
print(f"   {STUDY_AREA} → {boundary.geometry.iloc[0].geom_type}")

# ── 2.2  Points of Interest (POIs) ───────────────────────────────────────
# We use ox.features_from_place with tag dictionaries.
# Tags follow the OSM key=value model:
#   amenity=hospital, amenity=school, amenity=marketplace, etc.

print("\n🏥 Pulling amenities ...")
amenities = ox.features_from_place(STUDY_AREA, tags=AMENITY_TAGS)

# OSMnx returns mixed geometry types (points, polygons, multipolygons).
# We unify everything to point geometry (centroid) for mapping.
amenities_pts = amenities.copy()
amenities_pts["geometry"] = amenities_pts.geometry.centroid
amenities_pts = amenities_pts[amenities_pts.geometry.within(
    boundary.geometry.iloc[0]
)]

print(f"   Total amenities in study area: {len(amenities_pts)}")
print(f"   Columns: {list(amenities_pts.columns[:10])} ...")

# Breakdown by type
if "amenity" in amenities_pts.columns:
    print("\n   ── Amenity breakdown ──")
    counts = amenities_pts["amenity"].value_counts().head(15)
    for cat, n in counts.items():
        print(f"      {cat:25s}  {n:>5}")

# Save
amenities_path = DATA_DIR / "amenities.gpkg"
amenities_pts.to_file(amenities_path, driver="GPKG")
print(f"\n💾 Amenities saved → {amenities_path}")

# ── 2.3  Leisure & green spaces ──────────────────────────────────────────
print("\n🌳 Pulling leisure/green spaces ...")
try:
    leisure = ox.features_from_place(STUDY_AREA, tags=LEISURE_TAGS)
    leisure_polys = leisure[leisure.geometry.geom_type.isin(
        ["Polygon", "MultiPolygon"]
    )]
    print(f"   Leisure polygons found: {len(leisure_polys)}")
    leisure_path = DATA_DIR / "leisure.gpkg"
    leisure_polys.to_file(leisure_path, driver="GPKG")
    print(f"💾 Leisure saved → {leisure_path}")
except Exception as e:
    print(f"   ⚠ No leisure features found or error: {e}")
    leisure_polys = gpd.GeoDataFrame()

# ── 2.4  Visualise — POI map on dark basemap ─────────────────────────────
print("\n🎨 Creating POI map ...")

# Colour-code by amenity category
category_colors = {
    "hospital":         "#ff1744",
    "clinic":           "#ff5252",
    "pharmacy":         "#ff8a80",
    "school":           "#448aff",
    "university":       "#2962ff",
    "library":          "#82b1ff",
    "marketplace":      "#ffc400",
    "bank":             "#69f0ae",
    "atm":              "#b9f6ca",
    "police":           "#e040fb",
    "fire_station":     "#ea80fc",
    "place_of_worship": "#b388ff",
    "restaurant":       "#ff9100",
    "fuel":             "#ffab40",
}

fig, ax = plt.subplots(1, 1, figsize=(14, 14))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

# Boundary outline
boundary.to_crs(CRS_WEB_MERCATOR).plot(
    ax=ax, facecolor="none", edgecolor="white", linewidth=2
)

# Plot each amenity category
if "amenity" in amenities_pts.columns:
    legend_handles = []
    for cat, color in category_colors.items():
        subset = amenities_pts[amenities_pts["amenity"] == cat]
        if len(subset) > 0:
            subset.to_crs(CRS_WEB_MERCATOR).plot(
                ax=ax, color=color, markersize=12, alpha=0.8, zorder=5
            )
            legend_handles.append(
                mpatches.Patch(color=color, label=f"{cat} ({len(subset)})")
            )

    ax.legend(
        handles=legend_handles, loc="lower left",
        fontsize=7, facecolor="#1a1a2e", edgecolor="white",
        labelcolor="white", framealpha=0.9, ncol=2
    )

cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter)
ax.set_axis_off()
ax.set_title(
    f"Points of Interest — {STUDY_AREA}",
    fontsize=16, fontweight="bold", color="white", pad=20
)

fig.tight_layout()
fig_path = FIGURES_DIR / "ch2_poi_map.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  POI map saved → {fig_path}")

# ── 2.5  Interactive POI map (Folium) ─────────────────────────────────────
print("\n🌐 Creating interactive POI map ...")
centroid = boundary.geometry.iloc[0].centroid
m = folium.Map(
    location=[centroid.y, centroid.x],
    zoom_start=13,
    tiles="CartoDB dark_matter",
)

# Add boundary
folium.GeoJson(
    boundary.to_json(),
    style_function=lambda x: {
        "fillColor": "transparent", "color": "#00e5ff", "weight": 2
    },
).add_to(m)

# Add amenity markers (sample if too many)
sample = amenities_pts.head(500)  # Limit for browser performance
for _, row in sample.iterrows():
    cat = row.get("amenity", "unknown")
    name = row.get("name", cat)
    color = "red" if cat in ["hospital", "clinic"] else \
            "blue" if cat in ["school", "university"] else \
            "orange" if cat == "marketplace" else "gray"
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=4,
        color=color,
        fill=True,
        popup=f"<b>{name}</b><br>{cat}",
        tooltip=name,
    ).add_to(m)

map_path = OUTPUT_DIR / "ch2_poi_interactive.html"
m.save(str(map_path))
print(f"🌐 Interactive map → {map_path}")

print("\n✅ Chapter 2 complete.")
print("   You acquired: admin boundaries, amenities, leisure/green spaces.")
print("   Next → Chapter 3: Building footprints and morphology")
