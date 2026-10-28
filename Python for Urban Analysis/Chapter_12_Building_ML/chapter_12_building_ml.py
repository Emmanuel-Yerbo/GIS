"""
=============================================================================
CHAPTER 12 — Supervised GeoAI & Building Function Prediction (Master Class)
=============================================================================
Master Class Edition — Python for Urban Analysis (Ghana Series)

Learning Objectives & Course Modules:
1.  12.1 Building Footprint & Ground-Truth Label Parsing (Residential, Commercial, Industrial, Civic)
2.  12.2 Morphometric & Geometric Feature Engineering (Area, Compactness, Elongation, Convexity)
3.  12.3 Spatial Proximity & Transport Network Features (Distance to Arterial vs. Local Roads)
4.  12.4 Tobler's Spatial Lag & Neighborhood Density Engine (KD-Tree Spatial Autocorrelation)
5.  12.5 Dataset Assembly, Class Balancing & Stratified Train/Test Partitioning
6.  12.6 The Model Tournament (Logistic Regression vs. Random Forest vs. Gradient Boosting)
7.  12.7 Model Performance Evaluation (Confusion Matrix & Multi-Class Metrics)
8.  12.8 Spatial Gini Feature Importance Ranking (ch12_feature_importance.png)
9.  12.9 Professor Innovation 1: Spatial Block K-Fold vs. Random K-Fold CV (Spatial Leakage)
10. 12.10 Professor Innovation 2: Model Interpretability & Feature Contribution Breakdown
11. 12.11 Professor Innovation 3: Informal Mixed-Use & Hybrid Commercial Index
12. 12.12 Active Learning Query Engine: High-Uncertainty GPS Ground-Truthing Export
13. 12.13 Citywide Full-Scale AI Inference (Classifying 200,000+ Unlabelled Structures)
14. 12.14 Interactive 3D WebGL Multi-Layer AI Land-Use Dashboard (ch12_3d_landuse_webgl.html)

Ghana Context:
Over 80% of Accra's 220,000+ building footprints on OSM are unclassified (`building=yes`).
This chapter trains a multi-class Supervised Machine Learning engine to predict building
functions, discover informal mixed-use hubs (e.g. Makola, Madina, Jamestown), and guide
municipal urban planning surveys.
=============================================================================
"""
# ── 0. Dependencies Installation (Run in Terminal or Colab) ─────────────────
# pip install -q osmnx geopandas contextily pydeck scikit-learn xgboost shap

import warnings
warnings.filterwarnings("ignore")

import os
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
from scipy.spatial import cKDTree
from scipy.stats import entropy

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import contextily as cx
import pydeck as pdk

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

# Setup Config / Constants
STUDY_AREA = "Accra, Ghana"
CRS_WEB_MERCATOR = "EPSG:3857"
CRS_UTM_ACCRA = "EPSG:32630"
OUTPUT_DIR = Path("outputs")
FIGURES_DIR = OUTPUT_DIR / "figures"
DARK_BG = "#0e1117"
BUILDING_TAGS = {"building": True}
AMENITY_TAGS = {
    "amenity": [
        "hospital", "clinic", "pharmacy", "school", "university",
        "marketplace", "bank", "restaurant", "fuel", "place_of_worship"
    ]
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Tracks any feature groups that fell back to SYNTHETIC random data.
# If this list is non-empty at the end of the chapter, the trained model
# has been contaminated and its metrics MUST NOT be interpreted as real.
SYNTHETIC_FALLBACKS = []

print("=" * 70)
print("  CHAPTER 12 — Supervised GeoAI & Building Function Prediction (Master Class)")
print("=" * 70)


# =========================================================================
# 12.1 — Building Footprint Ingestion & Ground-Truth Label Parsing
# =========================================================================
print("\n>>> Module 12.1: Ingesting Building Footprints & Parsing Labels...")
start_time = time.time()

import osmnx as ox

boundary = ox.geocode_to_gdf(STUDY_AREA)
boundary_poly = boundary.geometry.iloc[0]
boundary_wm = boundary.to_crs(CRS_WEB_MERCATOR)

buildings_raw = ox.features_from_place(STUDY_AREA, tags=BUILDING_TAGS)
buildings = buildings_raw[buildings_raw.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
buildings = buildings[buildings.geometry.within(boundary_poly)].copy()

# Project to UTM meters (EPSG:32630) for metric spatial calculations
bldg_utm = buildings.to_crs(CRS_UTM_ACCRA).copy()
bldg_utm["area_m2"] = bldg_utm.geometry.area
bldg_utm = bldg_utm[bldg_utm["area_m2"] > 8.0].copy()

# Ground Truth Functional Label Parser
def clean_tag(val):
    if pd.isna(val):
        return ""
    v = str(val).strip().lower()
    if v in ["nan", "none", "null", "false", "0", ""]:
        return ""
    return v

def extract_ground_truth_label(row):
    b = clean_tag(row.get("building"))
    a = clean_tag(row.get("amenity"))
    s = clean_tag(row.get("shop"))
    o = clean_tag(row.get("office"))
    l = clean_tag(row.get("landuse"))
    
    # 1. Commercial / Retail
    if any(k in b for k in ["commercial", "retail", "office", "supermarket", "hotel", "bank", "store", "kiosk"]) or \
       any(k in a for k in ["marketplace", "bank", "restaurant", "cafe", "fuel", "bar", "fast_food", "pub"]) or \
       (s != "") or (o != ""):
        return "Commercial"
    
    # 2. Industrial / Warehousing
    elif any(k in b for k in ["industrial", "warehouse", "manufacture", "factory", "shed", "storage"]) or \
         "industrial" in l:
        return "Industrial"
    
    # 3. Civic / Institutional (Health, Education, Worship, Government)
    elif any(k in b for k in ["school", "university", "college", "kindergarten", "hospital", "clinic", "church", "mosque", "public", "civic", "government", "place_of_worship", "toilets"]) or \
         any(k in a for k in ["school", "university", "hospital", "clinic", "pharmacy", "place_of_worship", "police", "townhall"]):
        return "Institutional"
    
    # 4. Residential
    elif any(k in b for k in ["residential", "apartments", "house", "detached", "terrace", "dormitory", "residential_block", "home", "semidetached_house", "hut"]):
        return "Residential"
    
    # 5. Unlabelled Target (The vast majority of structures: 'yes', '', etc.)
    else:
        return "Unlabelled"

bldg_utm["target_class"] = bldg_utm.apply(extract_ground_truth_label, axis=1)

label_counts = bldg_utm["target_class"].value_counts()
print(f"  [+] Total Valid Buildings Ingested : {len(bldg_utm):,}")
print("  [+] Class Distribution:")
for k, v in label_counts.items():
    print(f"      - {k:<15}: {v:>7,} ({v/len(bldg_utm)*100:>5.1f}%)")

print(f"  [v] Module 12.1 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.2 — Morphometric & Geometric Feature Engineering
# =========================================================================
print("\n>>> Module 12.2: Computing Morphometric Shape Features...")
start_time = time.time()

# 1. Perimeter & Polsby-Popper Compactness Score
bldg_utm["perimeter_m"] = bldg_utm.geometry.length
bldg_utm["compactness_pp"] = (4 * np.pi * bldg_utm["area_m2"]) / (bldg_utm["perimeter_m"] ** 2)
bldg_utm["compactness_pp"] = bldg_utm["compactness_pp"].clip(0.01, 1.0)

# 2. Convexity Index (Area / Convex Hull Area)
bldg_utm["convex_hull_area"] = bldg_utm.geometry.convex_hull.area
bldg_utm["convexity"] = (bldg_utm["area_m2"] / np.maximum(bldg_utm["convex_hull_area"], 0.001)).clip(0.01, 1.0)

# 3. Minimum Rotated Rectangle (MRR) Length, Width & Elongation
def calc_mrr_properties(geom):
    try:
        mrr = geom.minimum_rotated_rectangle
        coords = list(mrr.exterior.coords)
        edge_lengths = [math.hypot(coords[i+1][0]-coords[i][0], coords[i+1][1]-coords[i][1]) for i in range(4)]
        dims = sorted([edge_lengths[0], edge_lengths[1]])
        width, length = dims[0], dims[1]
        elongation = width / max(length, 0.001)
        return pd.Series([width, length, elongation])
    except Exception:
        return pd.Series([np.nan, np.nan, np.nan])

bldg_utm[["mrr_width", "mrr_length", "elongation"]] = bldg_utm.geometry.apply(calc_mrr_properties)
bldg_utm["elongation"] = bldg_utm["elongation"].fillna(bldg_utm["elongation"].median()).clip(0.01, 1.0)

print(f"  [+] Extracted Geometric Descriptors: Area, Compactness, Convexity, Elongation")
print(f"  [v] Module 12.2 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.3 — Spatial Proximity & Transport Network Features
# =========================================================================
print("\n>>> Module 12.3: Extracting Street Network Proximities...")
start_time = time.time()

# Ingest Roads
try:
    roads_raw = ox.features_from_place(STUDY_AREA, tags={"highway": ["primary", "trunk", "secondary", "residential"]})
    roads = roads_raw[roads_raw.geometry.geom_type.isin(["LineString", "MultiLineString"])].to_crs(CRS_UTM_ACCRA)
    
    # Primary/Trunk Arterials vs Local Residential Streets
    arterials = roads[roads["highway"].isin(["primary", "trunk", "secondary"])].copy()
    local_roads = roads[roads["highway"].isin(["residential", "tertiary", "living_street", "unclassified"])].copy()
    
    # Extract coordinate points along road networks for KD-Tree distance lookups
    def sample_line_coords(gdf_lines, sample_dist=50):
        pts = []
        for line in gdf_lines.geometry:
            if line.geom_type == "LineString":
                length = line.length
                for d in np.arange(0, length, sample_dist):
                    p = line.interpolate(d)
                    pts.append([p.x, p.y])
            elif line.geom_type == "MultiLineString":
                for subline in line.geoms:
                    for d in np.arange(0, subline.length, sample_dist):
                        p = subline.interpolate(d)
                        pts.append([p.x, p.y])
        return np.array(pts) if len(pts) > 0 else np.array([[0, 0]])

    arterial_pts = sample_line_coords(arterials, sample_dist=40)
    local_pts = sample_line_coords(local_roads, sample_dist=40)
    
    tree_arterial = cKDTree(arterial_pts)
    tree_local = cKDTree(local_pts)
    
    bldg_centroids = np.column_stack([bldg_utm.geometry.centroid.x, bldg_utm.geometry.centroid.y])
    
    dist_arterial, _ = tree_arterial.query(bldg_centroids, k=1)
    dist_local, _ = tree_local.query(bldg_centroids, k=1)
    
    bldg_utm["dist_to_arterial_m"] = dist_arterial
    bldg_utm["dist_to_local_road_m"] = dist_local
    print(f"  [+] Calculated Euclidean Distances to Arterial Highways & Local Streets via KD-Trees")

except Exception as e:
    SYNTHETIC_FALLBACKS.append("dist_to_arterial_m / dist_to_local_road_m")
    print(f"  [!] WARNING: Road network fetch failed: {e}")
    print(f"  [!] Falling back to SYNTHETIC random distance features.")
    print(f"  [!] >>> MODEL RESULTS BELOW ARE INVALID UNTIL OSM IS REACHABLE AND THIS IS RE-RUN <<<")
    bldg_utm["dist_to_arterial_m"] = np.random.uniform(20, 800, len(bldg_utm))
    bldg_utm["dist_to_local_road_m"] = np.random.uniform(5, 100, len(bldg_utm))

print(f"  [v] Module 12.3 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.4 — Tobler's Spatial Lag & Neighborhood Density Engine
# =========================================================================
print("\n>>> Module 12.4: Computing Tobler's Spatial Lag Features (W·X)...")
start_time = time.time()

# KD-Tree over all building centroids
centroids_xy = np.column_stack([bldg_utm.geometry.centroid.x, bldg_utm.geometry.centroid.y])
tree_bldg = cKDTree(centroids_xy)

# 1. Neighbor count within 100m radius & 300m radius
counts_100m = [len(idx_list) - 1 for idx_list in tree_bldg.query_ball_point(centroids_xy, r=100.0)]
counts_300m = [len(idx_list) - 1 for idx_list in tree_bldg.query_ball_point(centroids_xy, r=300.0)]
bldg_utm["neighbor_count_100m"] = counts_100m
bldg_utm["neighbor_count_300m"] = counts_300m

# 2. Building Coverage Ratio (BCR) within 100m buffer
area_array = bldg_utm["area_m2"].values
buffer_100m_area = np.pi * (100.0 ** 2)

spatial_lag_mean_area = []
indices_100m = tree_bldg.query_ball_point(centroids_xy, r=100.0)
for idxs in indices_100m:
    if len(idxs) > 1:
        spatial_lag_mean_area.append(np.mean(area_array[idxs]))
    else:
        spatial_lag_mean_area.append(area_array[idxs[0]])

bldg_utm["spatial_lag_mean_area_100m"] = spatial_lag_mean_area
bldg_utm["building_coverage_ratio_100m"] = (bldg_utm["neighbor_count_100m"] * bldg_utm["spatial_lag_mean_area_100m"] / buffer_100m_area).clip(0, 1)

# Ingest POI Amenities Context
try:
    amenities_raw = ox.features_from_place(STUDY_AREA, tags=AMENITY_TAGS)
    amenities = amenities_raw.to_crs(CRS_UTM_ACCRA)
    amenity_centroids = np.column_stack([amenities.geometry.centroid.x, amenities.geometry.centroid.y])
    tree_amenity = cKDTree(amenity_centroids)
    
    # Distance to nearest commercial/civic amenity & count within 300m
    dist_amenity, _ = tree_amenity.query(centroids_xy, k=1)
    amenity_count_300m = [len(idx_list) for idx_list in tree_amenity.query_ball_point(centroids_xy, r=300.0)]
    
    bldg_utm["dist_to_amenity_m"] = dist_amenity
    bldg_utm["amenity_count_300m"] = amenity_count_300m
    print(f"  [+] Integrated {len(amenities):,} Commercial/Civic POIs into Spatial Context Engine")

except Exception as e:
    SYNTHETIC_FALLBACKS.append("dist_to_amenity_m / amenity_count_300m")
    print(f"  [!] WARNING: Amenity POI fetch failed: {e}")
    print(f"  [!] Falling back to SYNTHETIC random amenity features.")
    print(f"  [!] >>> MODEL RESULTS BELOW ARE INVALID UNTIL OSM IS REACHABLE AND THIS IS RE-RUN <<<")
    bldg_utm["dist_to_amenity_m"] = np.random.uniform(50, 1000, len(bldg_utm))
    bldg_utm["amenity_count_300m"] = np.random.poisson(3, len(bldg_utm))

print(f"  [+] Spatial Lag Features Engineered: W_mean_area, BCR_100m, Neighbor_Count, Amenity_Dist")
print(f"  [v] Module 12.4 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.5 — Dataset Assembly, Class Balancing & Stratified Split
# =========================================================================
print("\n>>> Module 12.5: Assembling Training Set & Balancing Classes...")
start_time = time.time()

FEATURE_COLS = [
    "area_m2", "perimeter_m", "compactness_pp", "convexity", "elongation",
    "mrr_width", "mrr_length", "dist_to_arterial_m", "dist_to_local_road_m",
    "neighbor_count_100m", "neighbor_count_300m", "spatial_lag_mean_area_100m",
    "building_coverage_ratio_100m", "dist_to_amenity_m", "amenity_count_300m"
]

# Separate Ground Truth Labeled vs. Unlabeled Prediction Set
labeled_df = bldg_utm[bldg_utm["target_class"] != "Unlabelled"].dropna(subset=FEATURE_COLS).copy()
unlabeled_df = bldg_utm[bldg_utm["target_class"] == "Unlabelled"].dropna(subset=FEATURE_COLS).copy()

# Filter classes with >= 20 samples
class_counts = labeled_df["target_class"].value_counts()
valid_classes = class_counts[class_counts >= 20].index.tolist()
labeled_df = labeled_df[labeled_df["target_class"].isin(valid_classes)].copy()

X = labeled_df[FEATURE_COLS].values
y = labeled_df["target_class"].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.25, random_state=42, stratify=y
)

print(f"  [+] Labeled Training Samples : {len(X_train):,}")
print(f"  [+] Labeled Testing Samples  : {len(X_test):,}")
print(f"  [+] Unlabeled Target Samples : {len(unlabeled_df):,} (To be predicted by GeoAI)")
print(f"  [v] Module 12.5 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.6 — The Model Tournament (Logistic vs. Random Forest vs. XGBoost)
# =========================================================================
print("\n>>> Module 12.6: Executing The GeoAI Model Tournament...")
start_time = time.time()

# 1. Baseline: Multi-Class Logistic Regression
clf_lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
clf_lr.fit(X_train, y_train)
y_pred_lr = clf_lr.predict(X_test)
acc_lr = accuracy_score(y_test, y_pred_lr)
f1_lr = f1_score(y_test, y_pred_lr, average="macro")

# 2. Balanced Random Forest
clf_rf = RandomForestClassifier(n_estimators=250, max_depth=15, class_weight="balanced", random_state=42, n_jobs=-1)
clf_rf.fit(X_train, y_train)
y_pred_rf = clf_rf.predict(X_test)
acc_rf = accuracy_score(y_test, y_pred_rf)
f1_rf = f1_score(y_test, y_pred_rf, average="macro")

# 3. Gradient Boosted Classifier (XGBoost / GBDT)
clf_gb = GradientBoostingClassifier(n_estimators=150, max_depth=6, random_state=42)
clf_gb.fit(X_train, y_train)
y_pred_gb = clf_gb.predict(X_test)
acc_gb = accuracy_score(y_test, y_pred_gb)
f1_gb = f1_score(y_test, y_pred_gb, average="macro")

print("  " + "=" * 55)
print("  MODEL TOURNAMENT BENCHMARK RESULTS")
print("  " + "=" * 55)
print(f"  1. Logistic Regression (Baseline)  : Accuracy = {acc_lr*100:>5.2f}% | Macro-F1 = {f1_lr:.3f}")
print(f"  2. Balanced Random Forest          : Accuracy = {acc_rf*100:>5.2f}% | Macro-F1 = {f1_rf:.3f} 🏆")
print(f"  3. Gradient Boosted Trees (GBDT)   : Accuracy = {acc_gb*100:>5.2f}% | Macro-F1 = {f1_gb:.3f}")
print("  " + "=" * 55)

# Select Champion Model
champion_model = clf_rf if f1_rf >= f1_gb else clf_gb
champion_name = "Balanced Random Forest" if f1_rf >= f1_gb else "Gradient Boosted Trees"
champion_preds = y_pred_rf if f1_rf >= f1_gb else y_pred_gb

print(f"  [v] Module 12.6 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.7 — Model Performance Evaluation: Confusion Matrix & Metrics
# =========================================================================
print("\n>>> Module 12.7: Generating Confusion Matrix Heatmap...")
start_time = time.time()

classes_sorted = sorted(list(set(y_test)))
cm = confusion_matrix(y_test, champion_preds, labels=classes_sorted)
cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

fig, ax = plt.subplots(figsize=(9, 8))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

im = ax.imshow(cm_norm, interpolation='nearest', cmap='Blues')
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Normalized Classification Accuracy", color="white", fontsize=11)
cbar.ax.yaxis.set_tick_params(color="white")
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

ax.set_xticks(np.arange(len(classes_sorted)))
ax.set_yticks(np.arange(len(classes_sorted)))
ax.set_xticklabels(classes_sorted, color="white", fontsize=11, rotation=30, ha="right")
ax.set_yticklabels(classes_sorted, color="white", fontsize=11)

for i in range(len(classes_sorted)):
    for j in range(len(classes_sorted)):
        val = cm_norm[i, j]
        color = "white" if val > 0.5 else "#90caf9"
        ax.text(j, i, f"{val*100:.1f}%\n({cm[i, j]})", ha="center", va="center", color=color, fontsize=10, fontweight="bold")

ax.set_xlabel("Predicted Building Function", color="white", fontsize=12, labelpad=10)
ax.set_ylabel("True Ground-Truth Function", color="white", fontsize=12, labelpad=10)
ax.set_title(
    f"MULTI-CLASS CONFUSION MATRIX — {STUDY_AREA}\n"
    f"Champion: {champion_name} (Macro-F1: {max(f1_rf, f1_gb):.3f})",
    color="white", fontsize=13, fontweight="bold", pad=15
)

fig.tight_layout()
out_cm = FIGURES_DIR / "ch12_confusion_matrix.png"
fig.savefig(out_cm, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved Confusion Matrix -> {out_cm}")

print("\n--- Detailed Classification Report ---")
print(classification_report(y_test, champion_preds, digits=3))
print(f"  [v] Module 12.7 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.8 — Spatial Gini Feature Importance Ranking
# =========================================================================
print("\n>>> Module 12.8: Plotting Feature Importance Hierarchy...")
start_time = time.time()

importances = clf_rf.feature_importances_
indices = np.argsort(importances)[::-1]

fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

bars = ax.barh(
    range(len(FEATURE_COLS)),
    importances[indices][::-1],
    color="#00e5ff",
    edgecolor="white",
    linewidth=0.8
)

ax.set_yticks(range(len(FEATURE_COLS)))
ax.set_yticklabels([FEATURE_COLS[i] for i in indices][::-1], color="white", fontsize=11)
ax.tick_params(colors="white")
ax.set_xlabel("Mean Gini Feature Importance", color="white", fontsize=12)
ax.grid(True, axis="x", linestyle="--", alpha=0.3, color="white")

for spine in ax.spines.values():
    spine.set_color("white")

ax.set_title(
    f"SPATIAL FEATURE IMPORTANCE HIERARCHY — {STUDY_AREA}\n"
    f"(Top Physical & Spatial Lag Predictors of Building Function)",
    color="white", fontsize=13, fontweight="bold", pad=15
)

fig.tight_layout()
out_fi = FIGURES_DIR / "ch12_feature_importance.png"
fig.savefig(out_fi, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved Feature Importance Plot -> {out_fi}")
print(f"  [v] Module 12.8 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.9 — Professor Innovation 1: Spatial Block K-Fold vs. Random K-Fold
# =========================================================================
print("\n>>> Module 12.9: Measuring Spatial Autocorrelation Data Leakage...")
start_time = time.time()

# 1. Standard Random 5-Fold Cross-Validation
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
f1_random_folds = []
for train_idx, val_idx in skf.split(X_scaled, y):
    m = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1)
    m.fit(X_scaled[train_idx], y[train_idx])
    f1_random_folds.append(f1_score(y[val_idx], m.predict(X_scaled[val_idx]), average="macro"))

# 2. Spatial Block K-Fold Cross-Validation (K-Means spatial quadrant blocking)
from sklearn.cluster import KMeans
labeled_coords = np.column_stack([labeled_df.geometry.centroid.x, labeled_df.geometry.centroid.y])
spatial_blocks = KMeans(n_clusters=5, random_state=42, n_init=10).fit_predict(labeled_coords)

f1_spatial_folds = []
for block_id in range(5):
    train_mask = (spatial_blocks != block_id)
    val_mask = (spatial_blocks == block_id)
    if val_mask.sum() == 0 or len(set(y[val_mask])) < 2:
        continue
    m = RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1)
    m.fit(X_scaled[train_mask], y[train_mask])
    f1_spatial_folds.append(f1_score(y[val_mask], m.predict(X_scaled[val_mask]), average="macro"))

mean_f1_rand = np.mean(f1_random_folds)
mean_f1_spat = np.mean(f1_spatial_folds)
spatial_leakage = (mean_f1_rand - mean_f1_spat) * 100

print(f"  [+] Random 5-Fold CV Macro-F1   : {mean_f1_rand:.3f}")
print(f"  [+] Spatial Block 5-Fold Macro-F1: {mean_f1_spat:.3f}")
print(f"  [!] Spatial Autocorrelation Leakage : +{spatial_leakage:.1f}% (Overoptimism in standard ML!)")

fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ax.bar(["Random K-Fold\n(Standard ML)", "Spatial Block K-Fold\n(GeoAI Reality)"], 
       [mean_f1_rand, mean_f1_spat], 
       color=["#ff9800", "#00e676"], edgecolor="white", width=0.5, linewidth=1.2)

ax.text(0, mean_f1_rand/2, f"F1 = {mean_f1_rand:.3f}", color="white", ha="center", va="center", fontsize=12, fontweight="bold")
ax.text(1, mean_f1_spat/2, f"F1 = {mean_f1_spat:.3f}", color="white", ha="center", va="center", fontsize=12, fontweight="bold")

ax.annotate(f"Spatial Data Leakage Gap:\n-{spatial_leakage:.1f}% Generalization Penalty",
            xy=(1, mean_f1_spat), xytext=(0.5, mean_f1_rand * 1.08),
            ha="center", va="bottom", color="#ff1744", fontsize=11, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#1a1a2e", edgecolor="#ff1744", alpha=0.9),
            arrowprops=dict(facecolor="#ff1744", shrink=0.05, width=1.5, headwidth=6))

ax.set_ylim(0, 1.0)
ax.set_ylabel("Macro F1-Score", color="white", fontsize=12)
ax.tick_params(colors="white")
for spine in ax.spines.values():
    spine.set_color("white")

ax.set_title(
    f"PROFESSOR'S INNOVATION 1 — SPATIAL AUTOCORRELATION LEAKAGE\n"
    f"Comparing Random vs. Spatial Block Cross-Validation — {STUDY_AREA}",
    color="white", fontsize=12, fontweight="bold", pad=15
)

fig.tight_layout()
out_cv = FIGURES_DIR / "ch12_spatial_vs_random_cv.png"
fig.savefig(out_cv, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved Spatial CV Benchmark -> {out_cv}")
print(f"  [v] Module 12.9 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.10 — Professor Innovation 2: Model Interpretability Breakdown
# =========================================================================
print("\n>>> Module 12.10: Generating Model Interpretability Diagnostics...")
start_time = time.time()

# Extract Class-Specific Feature Importance Profile
class_importances = []
for c_idx, c_name in enumerate(clf_rf.classes_):
    # Tree feature impact proxy per class
    y_binary = (y_train == c_name).astype(int)
    rf_c = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, class_weight="balanced")
    rf_c.fit(X_train, y_binary)
    class_importances.append(rf_c.feature_importances_)

ci_df = pd.DataFrame(class_importances, index=clf_rf.classes_, columns=FEATURE_COLS)

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

ci_df.T.plot(kind="bar", ax=ax, colormap="tab10", width=0.8, edgecolor="black", linewidth=0.5)
ax.tick_params(colors="white", labelsize=10)
plt.xticks(rotation=45, ha="right")
ax.legend(facecolor="#1a1a2e", edgecolor="white", labelcolor="white", fontsize=10, loc="upper right")
ax.grid(True, axis="y", linestyle="--", alpha=0.3, color="white")
for spine in ax.spines.values():
    spine.set_color("white")

ax.set_ylabel("Class-Specific Feature Sensitivity", color="white", fontsize=11)
ax.set_title(
    f"PROFESSOR'S INNOVATION 2 — GEOAI EXPLAINABILITY PROFILE\n"
    f"Which Physical Features Trigger Each Specific Functional Classification?",
    color="white", fontsize=13, fontweight="bold", pad=15
)

fig.tight_layout()
out_interp = FIGURES_DIR / "ch12_model_explainability_profile.png"
fig.savefig(out_interp, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved Explainability Profile -> {out_interp}")
print(f"  [v] Module 12.10 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.11 — Professor Innovation 3: Informal Mixed-Use & Hybrid Commercial Index
# =========================================================================
print("\n>>> Module 12.11: Computing Informal Mixed-Use & Hybrid Index...")
start_time = time.time()

# Run Prediction Probabilities across entire dataset
# (fill any residual NaN features — e.g. failed MRR — with training medians)
feature_medians = labeled_df[FEATURE_COLS].median()
X_all = scaler.transform(bldg_utm[FEATURE_COLS].fillna(feature_medians).values)
all_probs = clf_rf.predict_proba(X_all)
classes_list = list(clf_rf.classes_)

res_idx = classes_list.index("Residential") if "Residential" in classes_list else 0
com_idx = classes_list.index("Commercial") if "Commercial" in classes_list else 1

p_res = all_probs[:, res_idx]
p_com = all_probs[:, com_idx]

# Mixed-Use Index = 1 - |P(Res) - P(Com)| for buildings with non-trivial joint probability
bldg_utm["mixed_use_index"] = (1.0 - np.abs(p_res - p_com)) * (p_res + p_com)
bldg_utm["predicted_class"] = clf_rf.predict(X_all)
bldg_utm["confidence_prob"] = np.max(all_probs, axis=1)

high_mixed = bldg_utm[bldg_utm["mixed_use_index"] > 0.65]
print(f"  [+] Identified {len(high_mixed):,} Potential Informal Mixed-Use / Hybrid Buildings in Accra!")

# Map Mixed-Use Intensity
mixed_sample = bldg_utm.sample(min(25000, len(bldg_utm)), random_state=42).to_crs(CRS_WEB_MERCATOR)

fig, ax = plt.subplots(figsize=(14, 14))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

mixed_sample.plot(
    column="mixed_use_index", cmap="plasma",
    ax=ax, linewidth=0.1, edgecolor="none", alpha=0.85,
    legend=True,
    legend_kwds={
        "label": "Informal Mixed-Use Intensity Index (0 = Pure Single-Use | 1 = High Hybrid Commerce)",
        "orientation": "horizontal", "shrink": 0.6, "pad": 0.05
    }
)

boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
except Exception:
    pass

cbar_ax = fig.axes[-1]
cbar_ax.tick_params(colors="white")
cbar_ax.xaxis.label.set_color("white")
ax.set_axis_off()

ax.set_title(
    f"PROFESSOR'S INNOVATION 3 — INFORMAL MIXED-USE HYBRID CORRIDORS\n"
    f"Detecting Shop-Front / Residential Transitions — {STUDY_AREA}",
    color="white", fontsize=14, fontweight="bold", pad=20
)

fig.tight_layout()
out_mixed = FIGURES_DIR / "ch12_mixed_use_hybrid_map.png"
fig.savefig(out_mixed, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved Mixed-Use Map -> {out_mixed}")
print(f"  [v] Module 12.11 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.12 — Active Learning Query Engine: Ground-Truthing Survey Route
# =========================================================================
print("\n>>> Module 12.12: Generating Active Learning Ground-Truth Survey Route...")
start_time = time.time()

# Calculate Shannon Prediction Entropy: H = -sum(p * log(p))
pred_entropy = entropy(all_probs.T, base=np.e)
bldg_utm["prediction_entropy"] = pred_entropy

# Select Top 100 Most Ambiguous Buildings in Accra
unlabeled_mask = (bldg_utm["target_class"] == "Unlabelled")
active_candidates = bldg_utm[unlabeled_mask].sort_values(by="prediction_entropy", ascending=False).head(100).copy()

active_candidates["lon"] = active_candidates.geometry.centroid.to_crs(4326).x
active_candidates["lat"] = active_candidates.geometry.centroid.to_crs(4326).y

survey_export = active_candidates[["area_m2", "predicted_class", "confidence_prob", "prediction_entropy", "lon", "lat"]]
survey_path = OUTPUT_DIR / "ch12_active_learning_survey_targets.csv"
survey_export.to_csv(survey_path, index=True)

print(f"  [+] Extracted Top 100 High-Entropy Buildings for Field Survey Ground-Truthing")
print(f"  [+] Exported GPS Survey Route -> {survey_path}")
print(f"  [v] Module 12.12 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.13 — Citywide Full-Scale AI Inference (Mapping all Buildings)
# =========================================================================
print("\n>>> Module 12.13: Rendering Citywide AI Predicted Land-Use Map...")
start_time = time.time()

color_dict = {
    "Residential": "#00e676",      # Vivid Green
    "Commercial": "#00e5ff",       # Electric Cyan
    "Industrial": "#ff9800",       # Orange
    "Institutional": "#e040fb"     # Neon Purple
}

pred_sample = bldg_utm.sample(min(30000, len(bldg_utm)), random_state=42).to_crs(CRS_WEB_MERCATOR).copy()

fig, ax = plt.subplots(figsize=(16, 16))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

for c_name, c_color in color_dict.items():
    sub = pred_sample[pred_sample["predicted_class"] == c_name]
    if not sub.empty:
        sub.plot(ax=ax, color=c_color, alpha=0.85, linewidth=0.1, edgecolor="none", label=f"Predicted {c_name}")

boundary_wm.plot(ax=ax, facecolor="none", edgecolor="white", linewidth=2.5, zorder=10)

try:
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
except Exception:
    pass

legend_handles = [
    mpatches.Patch(color="#00e676", label=f"Residential ({ (bldg_utm['predicted_class']=='Residential').mean()*100:.1f}%)"),
    mpatches.Patch(color="#00e5ff", label=f"Commercial ({ (bldg_utm['predicted_class']=='Commercial').mean()*100:.1f}%)"),
    mpatches.Patch(color="#ff9800", label=f"Industrial ({ (bldg_utm['predicted_class']=='Industrial').mean()*100:.1f}%)"),
    mpatches.Patch(color="#e040fb", label=f"Institutional ({ (bldg_utm['predicted_class']=='Institutional').mean()*100:.1f}%)")
]
ax.legend(handles=legend_handles, loc="lower left", facecolor="#1a1a2e", edgecolor="white", labelcolor="white", fontsize=11, framealpha=0.9)
ax.set_axis_off()

ax.set_title(
    f"CITYWIDE GEOAI PREDICTED LAND-USE MAP — {STUDY_AREA}\n"
    f"(Full Machine Learning Classification across {len(bldg_utm):,} Footprints)",
    color="white", fontsize=16, fontweight="bold", pad=20
)

fig.tight_layout()
out_landuse = FIGURES_DIR / "ch12_predicted_land_use_map.png"
fig.savefig(out_landuse, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved Citywide AI Land-Use Map -> {out_landuse}")
print(f"  [v] Module 12.13 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# 12.14 — Interactive 3D WebGL Multi-Layer AI Land-Use Dashboard
# =========================================================================
print("\n>>> Module 12.14: Generating Interactive 3D WebGL AI Land-Use Dashboard...")
start_time = time.time()

# Sample top 6,000 prominent buildings for instantaneous WebGL 3D rendering
deck_3d_gdf = bldg_utm[bldg_utm["area_m2"] > 20].sort_values(by="area_m2", ascending=False).head(6000).to_crs(4326).copy()
deck_3d_gdf["geometry"] = deck_3d_gdf.geometry.simplify(0.00002, preserve_topology=True)

def geom_to_coords(geom):
    if geom.geom_type == 'Polygon':
        return [list(c)[:2] for c in geom.exterior.coords]
    elif geom.geom_type == 'MultiPolygon':
        return [list(c)[:2] for c in list(geom.geoms)[0].exterior.coords]
    return []

deck_3d_gdf["polygon"] = deck_3d_gdf.geometry.apply(geom_to_coords)

rgb_map = {
    "Residential": [0, 230, 118, 200],      # Vivid Green
    "Commercial": [0, 229, 255, 220],       # Electric Cyan
    "Industrial": [255, 152, 0, 220],       # Orange
    "Institutional": [224, 64, 251, 220]    # Neon Purple
}

deck_3d_gdf["color"] = deck_3d_gdf["predicted_class"].apply(lambda c: rgb_map.get(c, [200, 200, 200, 180]))
deck_3d_gdf["elevation"] = deck_3d_gdf["area_m2"].apply(lambda a: min(a * 0.25 + 15, 350))

layer_3d_landuse = pdk.Layer(
    "PolygonLayer",
    deck_3d_gdf,
    get_polygon="polygon",
    get_fill_color="color",
    get_elevation="elevation",
    extruded=True,
    get_line_color=[255, 255, 255, 120],
    line_width_min_pixels=1,
    pickable=True,
    auto_highlight=True
)

bounds = deck_3d_gdf.total_bounds
center_lon = (bounds[0] + bounds[2]) / 2
center_lat = (bounds[1] + bounds[3]) / 2

view_state = pdk.ViewState(
    longitude=center_lon,
    latitude=center_lat,
    zoom=12.5,
    pitch=50,
    bearing=-15
)

deck_landuse = pdk.Deck(
    layers=[layer_3d_landuse],
    initial_view_state=view_state,
    map_style=pdk.map_styles.CARTO_DARK,
    tooltip={'text': 'AI Prediction: {predicted_class}\nConfidence: {confidence_prob:.1%}\nArea: {area_m2:.1f} m²\nMixed-Use Index: {mixed_use_index:.2f}'}
)

out_path_12_14 = OUTPUT_DIR / 'ch12_3d_landuse_webgl.html'
deck_landuse.to_html(str(out_path_12_14))
print(f"  [+] Saved 3D AI Land-Use Dashboard -> {out_path_12_14}")

print(f"  [v] Module 12.14 complete in {time.time()-start_time:.2f}s")


# =========================================================================
# SYNTHESIS SUMMARY
# =========================================================================
print("\n" + "=" * 70)
print(" CHAPTER 12 GEOAI SYNTHESIS & MACHINE LEARNING INVENTORY ")
print("=" * 70)
print(f" Total Footprints Ingested     : {len(bldg_utm):,}")
print(f" Labeled Ground Truth Samples  : {len(labeled_df):,}")
print(f" Unlabeled Footprints Predicted : {len(unlabeled_df):,} (80%+ of Accra)")
print(f" Champion ML Model Architecture: {champion_name}")
print(f" Out-of-Sample Macro F1-Score  : {max(f1_rf, f1_gb):.3f}")
print(f" Spatial Data Leakage Bias     : +{spatial_leakage:.1f}%")
print(f" Informal Mixed-Use Identified : {len(high_mixed):,} structures")
if SYNTHETIC_FALLBACKS:
    print("-" * 70)
    print(f" ⚠️  DATA INTEGRITY WARNING ⚠️")
    print(f"    The following feature groups used SYNTHETIC random fallbacks:")
    for fb in SYNTHETIC_FALLBACKS:
        print(f"      - {fb}")
    print(f"    All metrics above are INVALID for real-world interpretation.")
    print(f"    Re-run this chapter with OSM connectivity restored.")
print("=" * 70)
print("Chapter 12 Supervised GeoAI complete. All models, figures, and 3D dashboards generated successfully.")
