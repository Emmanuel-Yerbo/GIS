"""
=============================================================================
CHAPTER 7 — Isochrone & 15-Minute City Analysis (Master Class Edition)
=============================================================================
Learning Objectives & Course Modules:
1. Scenario 1: Korle-Bu Teaching Hospital Spotlight (Smooth Polygon Rings + Callout Arrow)
2. Scenario 2: 10-POI Sample Spotlight (Individual Facility Polygon Rings)
3. Scenario 3: Citywide Healthcare Coverage & Service Deserts
4. Scenario 4: Multi-Category Access Comparison (Health vs Education vs Markets)
5. Scenario 5: Cumulative Accessibility Density Heatmap
6. Scenario 6: Interactive Pydeck Web Map (Outline Rings, Tip Labels, Red Cross Marker)
7. Professor Innovation 1: Accessibility Gini Index & Lorenz Curve
8. Professor Innovation 2: Multimodal Travel Comparison (15-min Walk vs Bike vs Drive)
9. Professor Innovation 3: Strategic Facility Location Optimization

Ghana Context:
Evaluates pedestrian accessibility across Accra starting from Korle-Bu Teaching Hospital
using smooth convex hull polygon rings per facility to quantify 15-minute city
performance, measure spatial inequality, and optimize public health infrastructure.

Professor's Note:
  "A true urban data scientist doesn't just draw maps -- they quantify spatial inequality
   with the Accessibility Gini Index, compare transport modalities, and solve city problems
   by calculating optimal facility placements."
=============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
import networkx as nx
import pydeck as pdk
from shapely.geometry import Point, MultiPoint
from shapely.ops import unary_union
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as cx
from config import (
    STUDY_AREA, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    OUTPUT_DIR, FIGURES_DIR, DARK_BG,
)

print("=" * 65)
print("  CHAPTER 7 -- Isochrone Analysis (Master Class Edition)")
print("=" * 65)

# =====================================================================
# 7.1 — Fetch Walkable Network & Healthcare Facilities
# =====================================================================
print(f"\n7.1 Fetching walkable network & facilities for: {STUDY_AREA} ...")

boundary = ox.geocode_to_gdf(STUDY_AREA)
boundary_wm = boundary.to_crs(CRS_WEB_MERCATOR)
boundary_utm = boundary.to_crs(CRS_UTM_ACCRA).geometry.iloc[0]

G_walk = ox.graph_from_place(STUDY_AREA, network_type="walk")
print(f"    Pedestrian network : {len(G_walk.nodes):,} nodes, {len(G_walk.edges):,} edges")

# Walking speed: 4.5 km/h = 1.25 m/s
WALK_SPEED_MPS = 1.25
for u, v, k, data in G_walk.edges(keys=True, data=True):
    data["time"] = data.get("length", 0) / WALK_SPEED_MPS

nodes_gdf, edges_gdf = ox.graph_to_gdfs(G_walk)
nodes_gdf = nodes_gdf.to_crs(CRS_UTM_ACCRA)
edges_gdf = edges_gdf.to_crs(CRS_UTM_ACCRA)
edges_wm = edges_gdf.to_crs(CRS_WEB_MERCATOR)

# Healthcare facilities
health_tags = {"amenity": ["hospital", "clinic", "pharmacy"]}
facilities_raw = ox.features_from_place(STUDY_AREA, tags=health_tags)
facilities = facilities_raw.copy()
facilities["geometry"] = facilities.geometry.centroid
facilities = facilities[facilities.geometry.within(boundary.geometry.iloc[0])].copy()
facilities_wm = facilities.to_crs(CRS_WEB_MERCATOR)
print(f"    Healthcare POIs    : {len(facilities):,} points")

facility_coords = list(zip(facilities.geometry.y, facilities.geometry.x))
center_nodes = ox.distance.nearest_nodes(
    G_walk,
    X=[c[1] for c in facility_coords],
    Y=[c[0] for c in facility_coords],
)
facilities["nearest_node"] = center_nodes


# =====================================================================
# CORE FUNCTION — Per-Facility Convex Hulls, Then Union
# =====================================================================
def compute_isochrones(nodes_list, trip_times=(300, 600, 900)):
    """
    For EACH facility node, build an ego-graph at each trip time,
    compute a convex hull of its reachable nodes, then union all
    individual facility hulls into one (multi)polygon.

    Returns dict {trip_time_seconds: GeoDataFrame in Web Mercator}.
    """
    polys = {}
    for trip_time in sorted(trip_times, reverse=True):
        facility_hulls = []
        for node in set(nodes_list):
            sub = nx.ego_graph(G_walk, node, radius=trip_time, distance="time")
            sub_ids = list(sub.nodes())
            if len(sub_ids) >= 3:
                pts = nodes_gdf.loc[sub_ids]
                hull = MultiPoint(pts.geometry.tolist()).convex_hull
                facility_hulls.append(hull)
            elif len(sub_ids) >= 1:
                pts = nodes_gdf.loc[sub_ids]
                facility_hulls.append(unary_union(pts.geometry.buffer(50)))
        if facility_hulls:
            combined = unary_union(facility_hulls).intersection(boundary_utm)
            gdf = gpd.GeoDataFrame(
                geometry=[combined], crs=CRS_UTM_ACCRA
            ).to_crs(CRS_WEB_MERCATOR)
            polys[trip_time] = gdf
    return polys


# Legend colour scheme (used across scenarios)
RING_COLORS = {
    1200: ("#ff5252", 0.45, "20 min walk"),
    900:  ("#ffa726", 0.55, "15 min walk"),
    600:  ("#ffee58", 0.65, "10 min walk"),
    300:  ("#00e676", 0.75, " 5 min walk"),
}


# =====================================================================
# 7.2 — SCENARIO 1: Korle-Bu Teaching Hospital Spotlight
# =====================================================================
print("\n7.2 SCENARIO 1: Korle-Bu Teaching Hospital isochrone spotlight ...")

kb_gdf = ox.geocode_to_gdf("Korle-Bu Teaching Hospital, Accra, Ghana")
kb_centroid = kb_gdf.geometry.centroid.iloc[0]
kb_lat, kb_lon = kb_centroid.y, kb_centroid.x
kb_node = ox.distance.nearest_nodes(G_walk, X=kb_lon, Y=kb_lat)

iso_kb = compute_isochrones([kb_node], trip_times=[300, 600, 900, 1200])
kb_wm = gpd.GeoDataFrame(
    geometry=[kb_centroid], crs="EPSG:4326"
).to_crs(CRS_WEB_MERCATOR)

fig, ax = plt.subplots(figsize=(14, 14))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

for t in [1200, 900, 600, 300]:
    if t in iso_kb:
        color, alpha, _ = RING_COLORS[t]
        iso_kb[t].plot(ax=ax, facecolor=color, edgecolor="none",
                       alpha=alpha, zorder=2 + (1500 - t) // 100)

edges_wm.plot(ax=ax, linewidth=0.8, color="#ffffff", alpha=0.3, zorder=10)
kb_wm.plot(ax=ax, color="white", edgecolor="#111", markersize=140,
           marker="o", linewidth=1.5, zorder=15)

# Callout arrow pointing outside the rings
kb_x, kb_y = kb_wm.geometry.iloc[0].x, kb_wm.geometry.iloc[0].y
ax.annotate(
    "Korle-Bu Teaching Hospital",
    xy=(kb_x, kb_y),
    xytext=(kb_x + 450, kb_y + 650),
    fontsize=11, color="white", fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.4", fc="#1a1a2e", ec="white", lw=1.2, alpha=0.95),
    arrowprops=dict(arrowstyle="->,head_width=0.4,head_length=0.6",
                    color="white", lw=1.5, connectionstyle="arc3,rad=-0.15"),
    zorder=20,
)

# Zoom tightly around the 20-min boundary
minx, miny, maxx, maxy = iso_kb[1200].total_bounds
PAD = 300
ax.set_xlim(minx - PAD, maxx + PAD)
ax.set_ylim(miny - PAD, maxy + PAD)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=15)
except Exception:
    pass

ax.set_axis_off()
ax.set_title("SCENARIO 1 -- Walking from Korle-Bu Teaching Hospital, Accra-Ghana",
             fontsize=16, fontweight="bold", color="white", pad=20)

legend_s1 = [
    mpatches.Patch(color="#ff5252", alpha=0.6, label="20 min"),
    mpatches.Patch(color="#ffa726", alpha=0.7, label="15 min"),
    mpatches.Patch(color="#ffee58", alpha=0.8, label="10 min"),
    mpatches.Patch(color="#00e676", alpha=0.9, label=" 5 min"),
]
ax.legend(handles=legend_s1, loc="upper right", fontsize=11,
          facecolor="#1a1a2e", edgecolor="white", labelcolor="white", framealpha=0.95)

fig.tight_layout()
path_s1 = FIGURES_DIR / "ch7_scenario1_korlebu_spotlight.png"
fig.savefig(path_s1, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_s1}")


# =====================================================================
# 7.3 — SCENARIO 2: 10-POI Sample Spotlight
# =====================================================================
print("\n7.3 SCENARIO 2: 10-POI sample isochrone spotlight ...")

sample_10 = facilities.head(10).copy()
sample_10_nodes = sample_10["nearest_node"].tolist()
iso_sample = compute_isochrones(sample_10_nodes, trip_times=[300, 600, 900, 1200])

fig, ax = plt.subplots(figsize=(16, 16))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

for t in [1200, 900, 600, 300]:
    if t in iso_sample:
        color, alpha, _ = RING_COLORS[t]
        iso_sample[t].plot(ax=ax, facecolor="none", edgecolor=color,
                           linewidth=2.5, alpha=alpha, zorder=2 + (1500 - t) // 100)

sample_10_wm = sample_10.to_crs(CRS_WEB_MERCATOR)
sample_10_wm.plot(ax=ax, color="white", edgecolor="#111",
                  markersize=45, linewidth=1.0, zorder=10)

# Label each POI
for idx, row in sample_10_wm.iterrows():
    name = row.get("name")
    if pd.isna(name) or not str(name).strip():
        name = f"POI #{idx}"
    else:
        name = str(name)[:20]
    ax.annotate(
        name, xy=(row.geometry.x, row.geometry.y),
        xytext=(5, 5), textcoords="offset points",
        fontsize=7, color="white", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.2", fc="#111", ec="white", lw=0.4, alpha=0.8),
        zorder=11,
    )

boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=12)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title("SCENARIO 2 -- 10-Facility Sample Isochrone Spotlight",
             fontsize=18, fontweight="bold", color="white", pad=20)
ax.legend(handles=legend_s1, loc="lower right", fontsize=10,
          facecolor="#1a1a2e", edgecolor="white", labelcolor="white", framealpha=0.9)

fig.tight_layout()
path_s2 = FIGURES_DIR / "ch7_scenario2_10_sample_spotlight.png"
fig.savefig(path_s2, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_s2}")


# =====================================================================
# 7.4 — SCENARIO 3: Citywide Healthcare Coverage & Deserts
# =====================================================================
print("\n7.4 SCENARIO 3: Citywide healthcare coverage & service deserts ...")

iso_citywide = compute_isochrones(center_nodes, trip_times=[300, 600, 900])

# Identify the 15-min coverage zone and desert gap
cov_15_utm = iso_citywide[900].to_crs(CRS_UTM_ACCRA).geometry.iloc[0]
desert_utm = boundary_utm.difference(cov_15_utm)
desert_wm = gpd.GeoDataFrame(
    geometry=[desert_utm], crs=CRS_UTM_ACCRA
).to_crs(CRS_WEB_MERCATOR)

fig, ax = plt.subplots(figsize=(16, 16))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

desert_wm.plot(ax=ax, facecolor="#ff1744", alpha=0.25, edgecolor="none", zorder=2)

for t in [900, 600, 300]:
    if t in iso_citywide:
        color, alpha, _ = RING_COLORS[t]
        iso_citywide[t].plot(ax=ax, facecolor="none", edgecolor=color,
                             linewidth=2.0, alpha=alpha, zorder=3 + (1000 - t) // 100)

facilities_wm.plot(ax=ax, color="white", edgecolor="#111",
                   markersize=12, linewidth=0.3, zorder=10)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white",
                 linewidth=2.5, zorder=12)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"SCENARIO 3 -- Citywide Healthcare 15-Min Coverage & Service Deserts ({STUDY_AREA})",
    fontsize=16, fontweight="bold", color="white", pad=20)

legend_s3 = [
    mpatches.Patch(color="#00e676", alpha=0.7, label="5-min Walk Coverage"),
    mpatches.Patch(color="#ffee58", alpha=0.6, label="10-min Walk Coverage"),
    mpatches.Patch(color="#ffa726", alpha=0.5, label="15-min Walk Coverage"),
    mpatches.Patch(color="#ff1744", alpha=0.3, label="Healthcare Desert (Unserved)"),
    plt.Line2D([0], [0], marker="o", color="w",
               label=f"Healthcare POIs ({len(facilities):,})",
               markerfacecolor="white", markersize=6, linestyle="None"),
]
ax.legend(handles=legend_s3, loc="lower right", fontsize=10,
          facecolor="#1a1a2e", edgecolor="white", labelcolor="white", framealpha=0.9)

fig.tight_layout()
path_s3 = FIGURES_DIR / "ch7_scenario3_citywide_coverage_deserts.png"
fig.savefig(path_s3, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_s3}")


# =====================================================================
# 7.5 — SCENARIO 4: Multi-Category Access Comparison
# =====================================================================
print("\n7.5 SCENARIO 4: Multi-category access comparison ...")

school_tags = {"amenity": ["school", "university", "library"]}
market_tags = {"amenity": ["marketplace", "supermarket"]}

schools_raw = ox.features_from_place(STUDY_AREA, tags=school_tags)
schools = schools_raw.copy()
schools["geometry"] = schools.geometry.centroid
schools = schools[schools.geometry.within(boundary.geometry.iloc[0])].copy()

markets_raw = ox.features_from_place(STUDY_AREA, tags=market_tags)
markets = markets_raw.copy()
markets["geometry"] = markets.geometry.centroid
markets = markets[markets.geometry.within(boundary.geometry.iloc[0])].copy()

school_nodes = ox.distance.nearest_nodes(
    G_walk, X=schools.geometry.x.tolist(), Y=schools.geometry.y.tolist())
market_nodes = ox.distance.nearest_nodes(
    G_walk, X=markets.geometry.x.tolist(), Y=markets.geometry.y.tolist())

iso_health_15 = iso_citywide[900]
iso_schools_15 = compute_isochrones(school_nodes, trip_times=[900])[900]
iso_markets_15 = compute_isochrones(market_nodes, trip_times=[900])[900]

fig, axes = plt.subplots(1, 3, figsize=(24, 8))
fig.patch.set_facecolor(DARK_BG)

categories = [
    ("Healthcare", iso_health_15, facilities.to_crs(CRS_WEB_MERCATOR), "#ff5252", axes[0]),
    ("Education",  iso_schools_15, schools.to_crs(CRS_WEB_MERCATOR),  "#29b6f6", axes[1]),
    ("Commerce",   iso_markets_15, markets.to_crs(CRS_WEB_MERCATOR),  "#ab47bc", axes[2]),
]
for title, iso_gdf, poi_gdf, color, ax in categories:
    ax.set_facecolor(DARK_BG)
    iso_gdf.plot(ax=ax, facecolor="none", edgecolor=color, linewidth=2.0, alpha=0.8)
    poi_gdf.plot(ax=ax, color="white", markersize=8, alpha=0.8)
    boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=1.5)
    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
    except Exception:
        pass
    ax.set_axis_off()
    ax.set_title(f"15-Min Walk: {title}", fontsize=13, fontweight="bold",
                 color="white", pad=10)

fig.suptitle(
    f"SCENARIO 4 -- Multi-Category 15-Minute City Access Comparison ({STUDY_AREA})",
    fontsize=16, fontweight="bold", color="white", y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.95])
path_s4 = FIGURES_DIR / "ch7_scenario4_category_comparison.png"
fig.savefig(path_s4, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_s4}")


# =====================================================================
# 7.6 — SCENARIO 5: Cumulative Accessibility Density Heatmap
# =====================================================================
print("\n7.6 SCENARIO 5: Cumulative service density heatmap ...")

all_poi_nodes = list(center_nodes) + list(school_nodes) + list(market_nodes)
reach_counts_series = pd.Series(all_poi_nodes).value_counts()
nodes_gdf_copy = nodes_gdf.copy()
nodes_gdf_copy["reach_count"] = nodes_gdf_copy.index.map(reach_counts_series).fillna(0)
nodes_gdf_wm = nodes_gdf_copy.to_crs(CRS_WEB_MERCATOR)

fig, ax = plt.subplots(figsize=(16, 16))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

nodes_gdf_wm[nodes_gdf_wm["reach_count"] > 0].plot(
    ax=ax, column="reach_count", cmap="YlOrRd",
    markersize=15, alpha=0.7, scheme="quantiles", k=7, legend=True,
    legend_kwds={
        "loc": "lower right", "fontsize": 9,
        "facecolor": "#1a1a2e", "edgecolor": "white",
        "labelcolor": "white", "framealpha": 0.9,
        "title": "Reachable Services per Node",
    },
)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"SCENARIO 5 -- Cumulative 15-Min Walk Service Density ({STUDY_AREA})",
    fontsize=16, fontweight="bold", color="white", pad=20)

fig.tight_layout()
path_s5 = FIGURES_DIR / "ch7_scenario5_cumulative_access_density.png"
fig.savefig(path_s5, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_s5}")


# =====================================================================
# 7.7 — SCENARIO 6: Interactive Pydeck Web Map
# =====================================================================
print("\n7.7 SCENARIO 6: Interactive Pydeck HTML map ...")


def geom_to_pydeck_coords(geom):
    """Convert shapely geometry to pydeck polygon coordinate lists."""
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [list(c)[:2] for c in geom.exterior.coords]
    elif geom.geom_type == "MultiPolygon":
        return [[list(c)[:2] for c in p.exterior.coords] for p in geom.geoms]
    return []


iso_layers = []
ring_label_data = []
ring_line_colors = {
    1200: [255, 82,  82,  255],
    900:  [255, 167, 38,  255],
    600:  [255, 238, 88,  255],
    300:  [0,   230, 118, 255],
}

for t in [1200, 900, 600, 300]:
    if t not in iso_kb:
        continue
    gdf_4326 = iso_kb[t].to_crs("EPSG:4326").copy()
    gdf_4326["polygon"] = gdf_4326.geometry.apply(geom_to_pydeck_coords)

    iso_layers.append(pdk.Layer(
        "PolygonLayer", gdf_4326,
        get_polygon="polygon",
        filled=False, stroked=True,
        get_line_color=ring_line_colors[t],
        line_width_min_pixels=3, pickable=True,
    ))

    # Topmost vertex for the ring tip label
    geom = gdf_4326.geometry.iloc[0]
    coords = (list(geom.exterior.coords) if geom.geom_type == "Polygon"
              else list(geom.geoms[0].exterior.coords))
    top = max(coords, key=lambda c: c[1])
    ring_label_data.append({
        "lon": top[0], "lat": top[1],
        "label": f"{t // 60} min",
        "r": ring_line_colors[t][0],
        "g": ring_line_colors[t][1],
        "b": ring_line_colors[t][2],
    })

labels_df = pd.DataFrame(ring_label_data)
ring_labels_layer = pdk.Layer(
    "TextLayer", labels_df,
    get_position="[lon, lat]", get_text="label",
    get_size=18, get_color="[r, g, b, 255]",
    get_text_anchor="'middle'", get_alignment_baseline="'bottom'",
    background=True, get_background_color="[26, 26, 46, 240]",
    font_weight="bold", character_set="auto", pickable=False,
)

# Red-cross hospital marker layers
hospital_df = pd.DataFrame([{
    "lat": kb_lat, "lon": kb_lon,
    "name": "Korle-Bu Teaching Hospital", "symbol": "+",
}])
hospital_glow = pdk.Layer(
    "ScatterplotLayer", hospital_df,
    get_position="[lon, lat]", get_color="[255, 23, 68, 255]",
    get_radius=75, pickable=False,
)
hospital_inner = pdk.Layer(
    "ScatterplotLayer", hospital_df,
    get_position="[lon, lat]", get_color="[255, 255, 255, 255]",
    get_radius=50, pickable=False,
)
hospital_cross = pdk.Layer(
    "TextLayer", hospital_df,
    get_position="[lon, lat]", get_text="symbol",
    get_size=32, get_color="[255, 23, 68, 255]",
    get_text_anchor="'middle'", get_alignment_baseline="'center'",
    font_weight="bold", character_set="auto", pickable=True,
)

view = pdk.ViewState(latitude=kb_lat, longitude=kb_lon, zoom=14, pitch=35)

deck = pdk.Deck(
    layers=iso_layers + [ring_labels_layer, hospital_glow, hospital_inner, hospital_cross],
    initial_view_state=view,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={"text": "{name}"},
)
html_path = OUTPUT_DIR / "ch7_interactive_isochrones.html"
deck.to_html(str(html_path))
print(f"    Saved -> {html_path}")


# =====================================================================
# 7.8 — PROFESSOR INNOVATION 1: Accessibility Gini Index & Lorenz Curve
# =====================================================================
print("\n7.8 PROFESSOR INNOVATION 1: Accessibility Gini Index & Lorenz Curve ...")

rc = pd.Series(center_nodes).value_counts()
nodes_gdf_copy["reach_count"] = nodes_gdf_copy.index.map(rc).fillna(0)

sorted_reach = np.sort(nodes_gdf_copy["reach_count"].values)
n = len(sorted_reach)
total = np.sum(sorted_reach)
cum_reach = np.cumsum(sorted_reach) / total if total > 0 else np.zeros(n)
cum_pop = np.linspace(0, 1, n)
gini_index = 1.0 - 2.0 * np.trapz(cum_reach, cum_pop)
print(f"    Accessibility Gini : G_A = {gini_index:.3f}")

fig, ax = plt.subplots(figsize=(8, 8))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ax.plot(cum_pop, cum_pop, color="#78909c", linestyle="--", linewidth=2,
        label="Perfect Equality (G = 0.0)")
ax.plot(cum_pop, cum_reach, color="#ff9100", linewidth=3,
        label=f"Accra Lorenz Curve (G_A = {gini_index:.3f})")
ax.fill_between(cum_pop, cum_pop, cum_reach, color="#ff9100", alpha=0.2,
                label="Inequality Gap")

ax.set_title(
    f"PROFESSOR'S INNOVATION 1 -- Healthcare Access Inequality\n"
    f"(Gini Index G_A = {gini_index:.3f})",
    fontsize=14, fontweight="bold", color="white", pad=15)
ax.set_xlabel("Cumulative Population Share", color="white", fontsize=11)
ax.set_ylabel("Cumulative 15-Min Reachable Services", color="white", fontsize=11)
ax.tick_params(colors="white")
ax.grid(True, linestyle="--", alpha=0.2, color="white")
ax.legend(loc="lower right", fontsize=10, facecolor="#1a1a2e",
          edgecolor="white", labelcolor="white")

fig.tight_layout()
path_p1 = FIGURES_DIR / "ch7_professor_lorenz_inequality_curve.png"
fig.savefig(path_p1, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p1}")


# =====================================================================
# 7.9 — PROFESSOR INNOVATION 2: Multimodal Travel Comparison
# =====================================================================
print("\n7.9 PROFESSOR INNOVATION 2: Multimodal 15-min walk / bike / drive ...")

BIKE_SPEED_MPS  = 4.17   # ~15 km/h
DRIVE_SPEED_MPS = 8.33   # ~30 km/h

def compute_multimodal_iso(speed_mps, sample_nodes=15):
    """Per-facility convex hull at 15 min for a given travel speed."""
    hulls = []
    for node in set(list(center_nodes)[:sample_nodes]):
        max_dist = speed_mps * 900.0
        sub = nx.ego_graph(G_walk, node, radius=max_dist, distance="length")
        pts = nodes_gdf.loc[list(sub.nodes())]
        if len(pts) >= 3:
            hulls.append(MultiPoint(pts.geometry.tolist()).convex_hull)
    if hulls:
        combined = unary_union(hulls).intersection(boundary_utm)
        return gpd.GeoDataFrame(geometry=[combined], crs=CRS_UTM_ACCRA).to_crs(CRS_WEB_MERCATOR)
    return gpd.GeoDataFrame(geometry=[], crs=CRS_WEB_MERCATOR)

iso_walk  = compute_multimodal_iso(WALK_SPEED_MPS)
iso_bike  = compute_multimodal_iso(BIKE_SPEED_MPS)
iso_drive = compute_multimodal_iso(DRIVE_SPEED_MPS)

fig, ax = plt.subplots(figsize=(16, 16))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

iso_drive.plot(ax=ax, facecolor="none", edgecolor="#ff1744", linewidth=2.5, alpha=0.8, zorder=3)
iso_bike.plot(ax=ax,  facecolor="none", edgecolor="#ffd700", linewidth=2.5, alpha=0.8, zorder=4)
iso_walk.plot(ax=ax,  facecolor="none", edgecolor="#00e676", linewidth=2.5, alpha=0.9, zorder=5)
facilities_wm.head(15).plot(ax=ax, color="white", edgecolor="#111",
                            markersize=35, linewidth=0.8, zorder=10)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=12)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"PROFESSOR'S INNOVATION 2 -- Multimodal 15-Min Travel Comparison ({STUDY_AREA})",
    fontsize=16, fontweight="bold", color="white", pad=20)

legend_p2 = [
    mpatches.Patch(color="#00e676", alpha=0.6, label="15-min Walk (~1.1 km)"),
    mpatches.Patch(color="#ffd700", alpha=0.4, label="15-min Bike (~3.7 km)"),
    mpatches.Patch(color="#ff1744", alpha=0.3, label="15-min Drive (~7.5 km)"),
]
ax.legend(handles=legend_p2, loc="lower right", fontsize=10,
          facecolor="#1a1a2e", edgecolor="white", labelcolor="white", framealpha=0.9)

fig.tight_layout()
path_p2 = FIGURES_DIR / "ch7_professor_multimodal_isochrones.png"
fig.savefig(path_p2, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p2}")


# =====================================================================
# 7.10 — PROFESSOR INNOVATION 3: Optimal Facility Placement
# =====================================================================
print("\n7.10 PROFESSOR INNOVATION 3: Optimal placement for next clinic ...")

desert_nodes = nodes_gdf[nodes_gdf.geometry.within(desert_utm)]
if len(desert_nodes) > 0:
    fac_utm = facilities.to_crs(CRS_UTM_ACCRA)
    best_idx = desert_nodes.geometry.apply(
        lambda g: min(g.distance(f) for f in fac_utm.geometry)
    ).idxmax()
    best_node = desert_nodes.loc[best_idx]

    opt_sub = nx.ego_graph(G_walk, best_idx, radius=900, distance="time")
    opt_pts = nodes_gdf.loc[list(opt_sub.nodes())]
    if len(opt_pts) >= 3:
        opt_poly = MultiPoint(opt_pts.geometry.tolist()).convex_hull.intersection(boundary_utm)
    else:
        opt_poly = unary_union(opt_pts.geometry.buffer(50)).intersection(boundary_utm)
    opt_gdf_wm = gpd.GeoDataFrame(
        geometry=[opt_poly], crs=CRS_UTM_ACCRA
    ).to_crs(CRS_WEB_MERCATOR)
    best_wm = gpd.GeoDataFrame(
        geometry=[best_node.geometry], crs=CRS_UTM_ACCRA
    ).to_crs(CRS_WEB_MERCATOR)

    coverage_km2 = opt_poly.area / 1e6
    print(f"    Optimal location   : ({best_node.geometry.y:.0f}, {best_node.geometry.x:.0f})")
    print(f"    Coverage gain      : +{coverage_km2:.2f} km2")

    fig, ax = plt.subplots(figsize=(16, 16))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    iso_citywide[900].plot(ax=ax, facecolor="none", edgecolor="#546e7a", linewidth=2.0, alpha=0.7, zorder=3)
    opt_gdf_wm.plot(ax=ax, facecolor="none", edgecolor="#ffd700",
                    linewidth=3.0, alpha=0.9, zorder=5)
    facilities_wm.plot(ax=ax, color="white", markersize=12, alpha=0.7, zorder=8)
    best_wm.plot(ax=ax, color="#ffd700", edgecolor="#111", markersize=150,
                 marker="*", linewidth=1.5, zorder=12)
    boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=15)

    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
    except Exception:
        pass

    ax.set_axis_off()
    ax.set_title(
        f"PROFESSOR'S INNOVATION 3 -- Strategic Clinic Placement\n"
        f"(New Facility Gain: +{coverage_km2:.2f} km2)",
        fontsize=16, fontweight="bold", color="white", pad=20)

    legend_p3 = [
        mpatches.Patch(color="#546e7a", alpha=0.4, label="Existing 15-min Coverage"),
        mpatches.Patch(color="#ffd700", alpha=0.6, label=f"New Gain (+{coverage_km2:.2f} km2)"),
        plt.Line2D([0], [0], marker="*", color="w", label="Optimal Clinic Site",
                   markerfacecolor="#ffd700", markersize=12, linestyle="None"),
    ]
    ax.legend(handles=legend_p3, loc="lower right", fontsize=10,
              facecolor="#1a1a2e", edgecolor="white", labelcolor="white", framealpha=0.9)

    fig.tight_layout()
    path_p3 = FIGURES_DIR / "ch7_professor_optimal_facility_placement.png"
    fig.savefig(path_p3, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"    Saved -> {path_p3}")
else:
    print("    No desert nodes found -- skipping Innovation 3.")

print("\n" + "=" * 65)
print("  Chapter 7 complete.")
print("=" * 65)
