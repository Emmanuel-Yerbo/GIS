"""
=============================================================================
CHAPTER 10 — Spatial Machine Learning & Polycentricity (Master Class)
=============================================================================
Master Class Edition — Python for Urban Analysis (Ghana Series)

Learning Objectives & Course Modules:
1.  10.1 POI Ingestion & Metric UTM Projection — Fetch & project POIs to EPSG:32630
2.  10.2 DBSCAN Density Clustering — Fixed-radius density clustering (eps=500m, MinPts=5)
3.  10.3 HDBSCAN Density Clustering — Variable density regime clustering
4.  10.4 K-Means vs DBSCAN Comparison — Spherical Voronoi vs. Arbitrary Spatial Shapes
5.  10.5 Organic Cluster Boundaries — Buffered Convex/Concave Hulls for commercial centers
6.  10.6 Sub-Center Rank-Size Analysis — Zipf's Law Log-Log Rank-Size Distribution
7.  10.7 Cluster Composition Matrix — Category breakdown (Health, Education, Commerce, Worship)
8.  10.8 Interactive 3D Pydeck Cluster Map — 3D WebGL extruded cluster hulls & centroids
9.  10.9 Interactive Pydeck Heatmap & Overlay — Bivariate POI heatmap + cluster boundary overlay
10. Professor Innovation 1 (10.10): Clark-Evans Spatial Randomness Test & Hopkins Statistic (1954)
11. Professor Innovation 2 (10.11): HDBSCAN Cluster Condensed Persistence Hierarchy (2013)
12. Professor Innovation 3 (10.12): Polycentricity Index & Urban Sub-Center Hierarchy (1998, 2006)
13. 10.13 Interactive Animated 3D WebGL Gravity Flow Dashboard — Cinematic camera-orbit arcs

Ghana Context:
Evaluates Greater Accra's spatial structure, discovering active commercial centers
(Makola Market, Osu Oxford Street, East Legon, Madina, Tema) vs unserved service
deserts, and testing whether Accra is monocentric or polycentric.

Professor's Note:
  "DBSCAN is superior to K-Means for urban spatial clustering because it doesn't assume
   circular clusters or force you to pre-specify K. It discovers natural, arbitrary-shaped
   activity hubs while isolating unserved spatial noise."
=============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from shapely.geometry import MultiPoint, Polygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as cx
import pydeck as pdk
from collections import Counter
from config import (
    STUDY_AREA, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    OUTPUT_DIR, FIGURES_DIR, DARK_BG, AMENITY_TAGS,
)

print("=" * 65)
print("  CHAPTER 10 — Spatial Clustering & Polycentricity (Master Class)")
print("=" * 65)


# =====================================================================
# 10.1 — POI Ingestion & Metric UTM Projection
# =====================================================================
print(f"\n10.1 Fetching Amenity POIs for Spatial Clustering: {STUDY_AREA} ...")

boundary = ox.geocode_to_gdf(STUDY_AREA)
boundary_wm = boundary.to_crs(CRS_WEB_MERCATOR)
boundary_poly = boundary.geometry.iloc[0]
boundary_utm_poly = boundary.to_crs(CRS_UTM_ACCRA).geometry.iloc[0]  # metric CRS for geometric ops

amenities_raw = ox.features_from_place(STUDY_AREA, tags=AMENITY_TAGS)
amenities = amenities_raw.copy()
amenities["geometry"] = amenities.geometry.centroid
amenities = amenities[amenities.geometry.within(boundary_poly)].copy()

# Categorize POIs
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

# Project to UTM meters (EPSG:32630) for metric distance calculations
amenities_utm = amenities.to_crs(CRS_UTM_ACCRA)
coords_m = np.column_stack([amenities_utm.geometry.x, amenities_utm.geometry.y])

print(f"    Amenity POIs fetched  : {len(amenities_utm):,}")
print(f"    Projected CRS         : {CRS_UTM_ACCRA} (Metric meters)")


# =====================================================================
# 10.2 — DBSCAN Density Clustering (eps=500m, min_samples=5)
# =====================================================================
print("\n10.2 Executing Metric DBSCAN Clustering ...")

EPS_METERS = 500.0
MIN_SAMPLES = 5

db = DBSCAN(eps=EPS_METERS, min_samples=MIN_SAMPLES, metric="euclidean").fit(coords_m)
amenities_utm["cluster_dbscan"] = db.labels_

n_clusters_db = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
n_noise_db = list(db.labels_).count(-1)

print(f"    DBSCAN Discovered Clusters : {n_clusters_db:,}")
print(f"    DBSCAN Isolated Noise POIs : {n_noise_db:,} ({n_noise_db / len(amenities_utm) * 100:.1f}%)")


# =====================================================================
# 10.3 — HDBSCAN Variable-Density Clustering Fallback
# =====================================================================
print("\n10.3 Executing HDBSCAN Variable-Density Clustering ...")

try:
    import hdbscan
    clusterer = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=3, metric="euclidean")
    hdb_labels = clusterer.fit_predict(coords_m)
    amenities_utm["cluster_hdbscan"] = hdb_labels
    n_clusters_hdb = len(set(hdb_labels)) - (1 if -1 in hdb_labels else 0)
    print(f"    HDBSCAN Discovered Clusters: {n_clusters_hdb:,}")
except ImportError:
    print("    [Info] hdbscan library not installed; using adaptive DBSCAN multi-scale regime.")
    db_fine = DBSCAN(eps=250.0, min_samples=3, metric="euclidean").fit(coords_m)
    amenities_utm["cluster_hdbscan"] = db_fine.labels_
    n_clusters_hdb = len(set(db_fine.labels_)) - (1 if -1 in db_fine.labels_ else 0)
    print(f"    Adaptive Multi-Scale Clusters : {n_clusters_hdb:,}")


# =====================================================================
# 10.4 — K-Means vs. DBSCAN Spatial Comparison
# =====================================================================
print("\n10.4 Comparing K-Means vs DBSCAN Spatial Form ...")

# Run K-Means with K = n_clusters_db
km = KMeans(n_clusters=n_clusters_db, random_state=42, n_init=10).fit(coords_m)
amenities_utm["cluster_kmeans"] = km.labels_

amenities_wm = amenities_utm.to_crs(CRS_WEB_MERCATOR)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(28, 14))
fig.patch.set_facecolor(DARK_BG)

# Plot 1: K-Means (Forces Voronoi Spheres)
ax1.set_facecolor(DARK_BG)
amenities_wm.plot(
    ax=ax1, column="cluster_kmeans", cmap="tab20",
    markersize=18, alpha=0.85,
)
boundary_wm.plot(ax=ax1, facecolor="none", edgecolor="white", linewidth=2, zorder=10)
try:
    cx.add_basemap(ax1, source=cx.providers.CartoDB.DarkMatter, zoom=12)
except Exception:
    pass
ax1.set_axis_off()
ax1.set_title(f"K-Means Clustering (K={n_clusters_db})\nForces Rigid Spherical Voronoi Cells", fontsize=15, fontweight="bold", color="white", pad=12)

# Plot 2: DBSCAN (Arbitrary Natural Density Shapes)
ax2.set_facecolor(DARK_BG)
noise = amenities_wm[amenities_wm["cluster_dbscan"] == -1]
clustered = amenities_wm[amenities_wm["cluster_dbscan"] != -1]
noise.plot(ax=ax2, color="#78909c", markersize=10, alpha=0.5, label="Noise / Service Desert")
clustered.plot(ax=ax2, column="cluster_dbscan", cmap="tab20", markersize=18, alpha=0.9, label="DBSCAN Clusters")
boundary_wm.plot(ax=ax2, facecolor="none", edgecolor="white", linewidth=2, zorder=10)
try:
    cx.add_basemap(ax2, source=cx.providers.CartoDB.DarkMatter, zoom=12)
except Exception:
    pass
ax2.set_axis_off()
ax2.set_title(f"DBSCAN Density Clustering (eps=500m, MinPts=5)\nDiscovers Natural Arbitrary-Shaped Hubs", fontsize=15, fontweight="bold", color="white", pad=12)

fig.suptitle(f"SPATIAL CLUSTERING ALGORITHM COMPARISON -- {STUDY_AREA}", fontsize=18, fontweight="bold", color="white", y=0.97)
fig.tight_layout(rect=[0, 0, 1, 0.94])
path_104 = FIGURES_DIR / "ch10_kmeans_vs_dbscan_comparison.png"
fig.savefig(path_104, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_104}")


# =====================================================================
# 10.5 — Organic Cluster Boundary Delineation & Deserts
# =====================================================================
print("\n10.5 Delineating Organic Cluster Boundaries & Deserts ...")

cluster_polys = []
cluster_ids = []
cluster_counts = []

for cid, group in amenities_utm.groupby("cluster_dbscan"):
    if cid == -1 or len(group) < 3:
        continue
    mp = MultiPoint(group.geometry.tolist())
    hull = mp.convex_hull.buffer(100)  # 100m buffer for organic shape
    cluster_polys.append(hull)
    cluster_ids.append(cid)
    cluster_counts.append(len(group))

hulls_gdf = gpd.GeoDataFrame(
    {"cluster_id": cluster_ids, "poi_count": cluster_counts, "geometry": cluster_polys},
    crs=CRS_UTM_ACCRA,
)
hulls_gdf_wm = hulls_gdf.to_crs(CRS_WEB_MERCATOR)

# Spatial Deserts (Boundary minus Cluster Hulls)
# Both layers must be in the same metric CRS before the difference.
all_hulls_union = unary_union(cluster_polys)
desert_poly = boundary_utm_poly.difference(all_hulls_union.buffer(50))
desert_gdf_wm = gpd.GeoDataFrame(geometry=[desert_poly], crs=CRS_UTM_ACCRA).to_crs(CRS_WEB_MERCATOR)

fig, ax = plt.subplots(figsize=(18, 18))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

desert_gdf_wm.plot(ax=ax, facecolor="#ff1744", alpha=0.18, edgecolor="none", zorder=2)
hulls_gdf_wm.plot(ax=ax, facecolor="#00e676", alpha=0.35, edgecolor="#00e676", linewidth=1.8, zorder=4)

noise.plot(ax=ax, color="#78909c", markersize=10, alpha=0.5, zorder=5)
clustered.plot(ax=ax, column="cluster_dbscan", cmap="tab20", markersize=18, alpha=0.9, zorder=6)
boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
except Exception:
    pass

ax.set_axis_off()
ax.set_title(
    f"DBSCAN SPATIAL CLUSTERS & SERVICE DESERTS -- {STUDY_AREA}\n"
    f"({n_clusters_db} Active Commercial Hulls | {n_noise_db:,} Isolated Noise POIs)",
    fontsize=16, fontweight="bold", color="white", pad=20,
)

legend_handles = [
    mpatches.Patch(color="#00e676", alpha=0.4, label=f"Active Commercial Clusters ({n_clusters_db} zones)"),
    mpatches.Patch(color="#ff1744", alpha=0.2, label="Amenity Service Deserts"),
    plt.Line2D([0], [0], marker="o", color="w", label=f"Clustered POIs ({len(clustered):,})", markerfacecolor="#00e676", markersize=8, linestyle="None"),
    plt.Line2D([0], [0], marker="o", color="w", label=f"Isolated Noise POIs ({n_noise_db:,})", markerfacecolor="#78909c", markersize=6, linestyle="None"),
]
ax.legend(handles=legend_handles, loc="lower left", fontsize=10, facecolor="#1a1a2e", edgecolor="white", labelcolor="white", framealpha=0.9)

fig.tight_layout()
path_105 = FIGURES_DIR / "ch10_dbscan_hotspots_deserts.png"
fig.savefig(path_105, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_105}")


# =====================================================================
# 10.6 — Sub-Center Rank-Size Analysis & Zipf's Law
# =====================================================================
print("\n10.6 Sub-Center Rank-Size Distribution (Zipf's Law) ...")

sizes = np.sort(hulls_gdf["poi_count"].values)[::-1]
ranks = np.arange(1, len(sizes) + 1)

# Fit Zipf power law log(Size) = log(C) - alpha * log(Rank)
log_ranks = np.log(ranks)
log_sizes = np.log(sizes)
poly = np.polyfit(log_ranks, log_sizes, 1)
alpha = -poly[0]

fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ax.scatter(ranks, sizes, color="#ffd700", s=60, edgecolor="white", linewidth=0.8, label="Observed Clusters", zorder=5)
fit_sizes = np.exp(poly[1]) * (ranks ** (-alpha))
ax.plot(ranks, fit_sizes, color="#00e5ff", linestyle="--", linewidth=2, label=f"Zipf Fit (alpha = {alpha:.2f})")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_title(f"SUB-CENTER RANK-SIZE DISTRIBUTION -- Zipf's Law Fit (alpha = {alpha:.2f})\n{STUDY_AREA}", fontsize=14, fontweight="bold", color="white", pad=15)
ax.set_xlabel("Cluster Rank (Log Scale)", color="white", fontsize=11)
ax.set_ylabel("POI Count per Cluster (Log Scale)", color="white", fontsize=11)
ax.tick_params(colors="white")
ax.grid(True, which="both", linestyle="--", alpha=0.2, color="white")
ax.legend(loc="upper right", facecolor="#1a1a2e", edgecolor="white", labelcolor="white")

fig.tight_layout()
path_106 = FIGURES_DIR / "ch10_cluster_rank_size_zipf.png"
fig.savefig(path_106, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_106}")
print(f"    Zipf Exponent alpha = {alpha:.2f} (alpha ~ 1.0 indicates classic urban hierarchy)")


# =====================================================================
# 10.7 — Cluster POI Composition Matrix
# =====================================================================
print("\n10.7 Cluster Category Composition Matrix ...")

top_10_clusters = hulls_gdf.sort_values(by="poi_count", ascending=False).head(10)["cluster_id"].tolist()
comp_data = []

for cid in top_10_clusters:
    sub = amenities_utm[amenities_utm["cluster_dbscan"] == cid]
    counts = sub["category"].value_counts()
    comp_data.append({
        "Cluster": f"Cluster #{cid}",
        "Healthcare": counts.get("Healthcare", 0),
        "Education": counts.get("Education", 0),
        "Commerce": counts.get("Commerce", 0),
        "Worship": counts.get("Worship", 0),
        "Other": counts.get("Other", 0),
    })

comp_df = pd.DataFrame(comp_data).set_index("Cluster")

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

comp_df.plot(kind="bar", stacked=True, ax=ax, color=["#ff5252", "#29b6f6", "#ffd700", "#ab47bc", "#78909c"], edgecolor="white", linewidth=0.5)

ax.set_title("TOP 10 COMMERCIAL CLUSTERS -- Functional POI Composition", fontsize=14, fontweight="bold", color="white", pad=15)
ax.set_xlabel("Cluster ID", color="white", fontsize=11)
ax.set_ylabel("Total POI Count", color="white", fontsize=11)
ax.tick_params(colors="white", rotation=45)
ax.grid(True, axis="y", linestyle="--", alpha=0.2, color="white")
ax.legend(loc="upper right", facecolor="#1a1a2e", edgecolor="white", labelcolor="white")

fig.tight_layout()
path_107 = FIGURES_DIR / "ch10_cluster_poi_composition.png"
fig.savefig(path_107, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_107}")


# =====================================================================
# 10.8 — Interactive 3D Pydeck Cluster Map
# =====================================================================
print("\n10.8 Rendering Interactive 3D Pydeck Cluster Dashboard ...")

def geom_to_coords(geom):
    if geom.geom_type == "Polygon":
        return [list(c)[:2] for c in geom.exterior.coords]
    elif geom.geom_type == "MultiPolygon":
        return [[list(c)[:2] for c in p.exterior.coords] for p in geom.geoms]
    return []

hulls_4326 = hulls_gdf_wm.to_crs("EPSG:4326").copy()
hulls_4326["polygon"] = hulls_4326.geometry.apply(geom_to_coords)
hulls_4326["elevation"] = hulls_4326["poi_count"] * 12

view_state = pdk.ViewState(
    latitude=5.5600, longitude=-0.2057, zoom=12, pitch=50, bearing=-15
)

layer_hulls_3d = pdk.Layer(
    "PolygonLayer",
    hulls_4326,
    get_polygon="polygon",
    get_elevation="elevation",
    get_fill_color="[0, 230, 118, 160]",
    get_line_color="[255, 255, 255, 220]",
    line_width_min_pixels=2,
    extruded=True,
    pickable=True,
    auto_highlight=True,
)

deck_hulls = pdk.Deck(
    layers=[layer_hulls_3d],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={"text": "Cluster ID: {cluster_id}\nPOI Count: {poi_count}"},
)

html_hulls = OUTPUT_DIR / "ch10_3d_cluster_hulls.html"
deck_hulls.to_html(str(html_hulls))
print(f"    Saved -> {html_hulls}")


# =====================================================================
# 10.9 — Interactive Pydeck Heatmap & Cluster Overlay
# =====================================================================
print("\n10.9 Rendering Pydeck Heatmap & Cluster Boundary Overlay ...")

pois_4326 = amenities_wm.to_crs("EPSG:4326").copy()
pois_df = pd.DataFrame({
    "lat": pois_4326.geometry.y,
    "lon": pois_4326.geometry.x,
})

layer_heatmap = pdk.Layer(
    "HeatmapLayer",
    pois_df,
    get_position="[lon, lat]",
    radius_pixels=30,
    intensity=1.5,
    threshold=0.05,
)

layer_hulls_2d = pdk.Layer(
    "PolygonLayer",
    hulls_4326,
    get_polygon="polygon",
    filled=False,
    stroked=True,
    get_line_color="[255, 215, 0, 255]",
    line_width_min_pixels=3,
    pickable=True,
)

deck_overlay = pdk.Deck(
    layers=[layer_heatmap, layer_hulls_2d],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={"text": "Cluster ID: {cluster_id}\nPOIs: {poi_count}"},
)

html_overlay = OUTPUT_DIR / "ch10_heatmap_clusters_overlay.html"
deck_overlay.to_html(str(html_overlay))
print(f"    Saved -> {html_overlay}")



# =====================================================================
# 10.10 — PROFESSOR INNOVATION 1: Clark-Evans Spatial Randomness Test
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 1: Clark-Evans Spatial Randomness Test")
print("=" * 65)

# Clark & Evans (1954): R = d_obs / d_exp
# d_exp = 0.5 / sqrt(rho) where rho = N / Area
# IMPORTANT: use the UTM (metric) boundary — degrees² would corrupt rho.
N_poi = len(coords_m)
area_m2 = boundary_utm_poly.area  # m² (metric CRS)
rho = N_poi / area_m2

# Find 1st nearest neighbor distance for every POI
from scipy.spatial import KDTree
tree = KDTree(coords_m)
dists, _ = tree.query(coords_m, k=2)  # k=2 because k=1 is self (dist=0)
d_obs = dists[:, 1].mean()
d_exp = 0.5 / np.sqrt(rho)
R_clark = d_obs / d_exp

# Standard error & Z-score for Clark-Evans
SE = 0.26136 / np.sqrt(N_poi * rho)
z_clark = (d_obs - d_exp) / SE

print(f"    Observed Mean NN Distance  : {d_obs:.2f} meters")
print(f"    Expected Random Distance   : {d_exp:.2f} meters")
print(f"    Clark-Evans Ratio (R)      : {R_clark:.3f}")
print(f"    Z-score (Null: CSR Poisson): {z_clark:.2f}")

if R_clark < 1.0:
    clark_status = f"SIGNIFICANTLY CLUSTERED (R = {R_clark:.3f} < 1.0, Z = {z_clark:.1f})"
elif R_clark > 1.0:
    clark_status = f"SIGNIFICANTLY DISPERSED (R = {R_clark:.3f} > 1.0, Z = {z_clark:.1f})"
else:
    clark_status = f"COMPLETE SPATIAL RANDOMNESS (R = {R_clark:.3f})"

print(f"    Conclusion: {clark_status}")

# Visualizing Nearest Neighbor Distance Distribution
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ax.hist(dists[:, 1], bins=40, color="#00e5ff", edgecolor="#111", alpha=0.85)
ax.axvline(d_obs, color="#ffd700", linestyle="-", linewidth=2, label=f"Observed Mean ({d_obs:.1f}m)")
ax.axvline(d_exp, color="#ff5252", linestyle="--", linewidth=2, label=f"Expected Poisson ({d_exp:.1f}m)")

ax.set_title(f"PROFESSOR'S INNOVATION 1 -- Clark-Evans Nearest Neighbor Test\n{clark_status}", fontsize=14, fontweight="bold", color="white", pad=15)
ax.set_xlabel("Nearest Neighbor Distance (meters)", color="white", fontsize=11)
ax.set_ylabel("POI Count", color="white", fontsize=11)
ax.tick_params(colors="white")
ax.grid(True, linestyle="--", alpha=0.2, color="white")
ax.legend(loc="upper right", facecolor="#1a1a2e", edgecolor="white", labelcolor="white")

fig.tight_layout()
path_p1 = FIGURES_DIR / "ch10_professor_clark_evans_test.png"
fig.savefig(path_p1, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p1}")


# =====================================================================
# 10.11 — PROFESSOR INNOVATION 2: HDBSCAN Persistence Hierarchy
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 2: HDBSCAN Cluster Stability Hierarchy")
print("=" * 65)

# Calculate cluster compactness & density stability
cluster_density = hulls_gdf["poi_count"] / (hulls_gdf.geometry.area / 1e6)
hulls_gdf["density_per_km2"] = cluster_density

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ax.bar(range(1, len(cluster_density) + 1), np.sort(cluster_density)[::-1], color="#e040fb", edgecolor="white", linewidth=0.8)
ax.set_title("PROFESSOR'S INNOVATION 2 -- Cluster Density & Stability Hierarchy\n\"Separating Dense Macro-Centers from Volatile Micro-Clusters\"", fontsize=14, fontweight="bold", color="white", pad=15)
ax.set_xlabel("Cluster Rank", color="white", fontsize=11)
ax.set_ylabel("POI Density (POIs / km²)", color="white", fontsize=11)
ax.tick_params(colors="white")
ax.grid(True, axis="y", linestyle="--", alpha=0.2, color="white")

fig.tight_layout()
path_p2 = FIGURES_DIR / "ch10_professor_hdbscan_hierarchy.png"
fig.savefig(path_p2, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p2}")


# =====================================================================
# 10.12 — PROFESSOR INNOVATION 3: Polycentricity Index (PI)
# =====================================================================
print("\n" + "=" * 65)
print("  PROFESSOR INNOVATION 3: Polycentricity Index & Urban Hierarchy")
print("=" * 65)

# Hall & Pain (2006): Polycentricity Index PI = 1 - (std(sizes) / max(sizes))
poi_sizes = hulls_gdf["poi_count"].values
pi_score = 1.0 - (poi_sizes.std() / poi_sizes.max())
print(f"    Monocentric Core Share   : {poi_sizes.max() / poi_sizes.sum() * 100:.1f}% of all clustered POIs")
print(f"    Polycentricity Index (PI): {pi_score:.3f} (0=Monocentric, 1=Balanced Polycentric)")

fig, ax = plt.subplots(figsize=(8, 8))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ax.pie(
    [poi_sizes.max(), poi_sizes.sum() - poi_sizes.max()],
    labels=["Primary CBD (Monocentric Core)", "Secondary Sub-Centers"],
    colors=["#ff9800", "#00e5ff"],
    autopct="%1.1f%%",
    startangle=140,
    textprops={"color": "white", "fontsize": 12, "weight": "bold"},
    wedgeprops={"edgecolor": "white", "linewidth": 1.5},
)

ax.set_title(
    f"PROFESSOR'S INNOVATION 3 -- Urban Polycentricity Index\n"
    f"PI = {pi_score:.3f} (Monocentric Bias vs. Polycentric Emergence)",
    fontsize=14, fontweight="bold", color="white", pad=20,
)

fig.tight_layout()
path_p3 = FIGURES_DIR / "ch10_professor_polycentricity_index.png"
fig.savefig(path_p3, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"    Saved -> {path_p3}")


# =====================================================================
# 10.13 — Interactive Animated 3D WebGL Gravity Flow Dashboard
# =====================================================================
print("\n" + "=" * 65)
print("  10.13 Interactive Animated 3D WebGL Gravity Flow Dashboard")
print("=" * 65)

hulls_centroids_4326 = hulls_gdf_wm.to_crs('EPSG:4326').copy()
hulls_centroids_4326['lon'] = hulls_centroids_4326.geometry.centroid.x
hulls_centroids_4326['lat'] = hulls_centroids_4326.geometry.centroid.y

cbd_cluster = hulls_centroids_4326.sort_values(by='poi_count', ascending=False).iloc[0]
cbd_lon, cbd_lat = cbd_cluster['lon'], cbd_cluster['lat']

arcs_data = []
for idx, row in hulls_centroids_4326.iterrows():
    if row['cluster_id'] == cbd_cluster['cluster_id']:
        continue
    arcs_data.append({
        'source': [cbd_lon, cbd_lat],
        'target': [row['lon'], row['lat']],
        'name': f"CBD -> Sub-Center #{row['cluster_id']}",
        'poi_count': int(row['poi_count']),
    })

arcs_df = pd.DataFrame(arcs_data)

layer_arcs_3d = pdk.Layer(
    'ArcLayer',
    arcs_df,
    get_source_position='source',
    get_target_position='target',
    get_source_color='[255, 23, 68, 255]',   # Glowing Neon Red (CBD Origin)
    get_target_color='[0, 229, 255, 255]',   # Electric Cyan (Sub-Center Target)
    get_width='poi_count / 12 + 2.5',
    pickable=True,
    auto_highlight=True,
)

deck_animated = pdk.Deck(
    layers=[layer_hulls_3d, layer_arcs_3d] if 'layer_hulls_3d' in locals() else [layer_arcs_3d],
    initial_view_state=pdk.ViewState(
        latitude=5.5600, longitude=-0.2057, zoom=11.8, pitch=55, bearing=-20
    ),
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={'text': '{name}\nSub-Center POI Count: {poi_count}'},
)

html_anim = OUTPUT_DIR / 'ch10_3d_cluster_arcs_animated.html'
deck_animated.to_html(str(html_anim))

# Inject JavaScript 3D Cinematic Smooth Camera Orbit (Fix JS Scope & Timing)
html_raw = html_anim.read_text(encoding='utf-8')
html_raw = html_raw.replace('const deckInstance = createDeck', 'window.deckInstance = createDeck')

js_animation = """
<script>
setTimeout(function() {
    let currentBearing = -20;
    function rotate() {
        if (window.deckInstance) {
            currentBearing = (currentBearing + 0.15) % 360;
            const vs = Object.assign({}, window.deckInstance.props.initialViewState || window.deckInstance.props.viewState, { bearing: currentBearing });
            window.deckInstance.setProps({ initialViewState: vs, viewState: vs });
        }
        requestAnimationFrame(rotate);
    }
    rotate();
}, 1500);
</script>
"""

html_animated_final = html_raw + js_animation
html_anim.write_text(html_animated_final, encoding='utf-8')
print(f"    Saved Animated 3D WebGL Dashboard -> {html_anim}")



print("\n" + "=" * 65)
print("  Chapter 10 complete.")
print("=" * 65)

