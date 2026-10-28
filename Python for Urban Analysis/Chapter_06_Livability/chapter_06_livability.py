"""
=============================================================================
CHAPTER 6 — A Simple Livability Index: Scoring All 29 Districts
=============================================================================
Learning objectives
───────────────────
1. Scale the pipeline across multiple districts (Greater Accra's 29 MMDAs)
2. Compute per-district indicators from OSM data
3. Normalise and combine indicators into a composite livability score
4. Produce a choropleth ranking map and summary table

Indicators used (all derived from OSM)
──────────────────────────────────────
  A. Amenity density      — POIs per km²
  B. Road network density — total road km per km²
  C. Building density     — building footprint count per km²
  D. Green space ratio    — leisure area / district area × 100

Methodology
───────────
  1. For each district, pull boundary → clip features → compute indicators
  2. Min-max normalise each indicator to [0, 1]
  3. Simple equal-weight average → composite livability score

Ghana context
─────────────
Greater Accra Region has 29 MMDAs — more diverse than Vienna's 23
Bezirke, spanning dense urban cores (Accra Metro, Korle Klottey) to
peri-urban/rural areas (Shai-Osudoku, Ada East).  This makes the
livability index especially revealing.

Professor's note
─────────────────
  "A livability index is only as good as its indicators.  Ours is
   intentionally simple — 4 indicators, equal weights, open data.
   But the PATTERN is what matters: boundary → features → indicators
   → normalise → score → map.  You can plug in any indicator set."

NOTE: This chapter queries OSM for each of the 29 districts.  Depending
on your internet connection, this may take 15–30 minutes.  We cache
intermediate results to allow resumption.
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
import json
import time
from config import (
    STUDY_AREA, STUDY_REGION, GREATER_ACCRA_DISTRICTS,
    CRS_WGS84, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    DATA_DIR, FIGURES_DIR, OUTPUT_DIR, DARK_BG,
    AMENITY_TAGS, BUILDING_TAGS, LEISURE_TAGS,
)

print("=" * 65)
print("  CHAPTER 6 — Livability Index for Greater Accra")
print("=" * 65)

# ── 6.1  Helper: compute indicators for one district ─────────────────────
def compute_district_indicators(district_name, timeout=120):
    """
    Pull boundary, amenities, buildings, roads, leisure for a district.
    Return a dict of raw indicators.
    """
    result = {
        "district": district_name,
        "amenity_count": 0,
        "building_count": 0,
        "road_km": 0.0,
        "green_area_m2": 0.0,
        "district_area_km2": 0.0,
        "status": "ok",
    }

    try:
        # 1. Boundary
        gdf = ox.geocode_to_gdf(district_name)
        area_m2 = gdf.to_crs(CRS_UTM_ACCRA).area.iloc[0]
        result["district_area_km2"] = area_m2 / 1e6

        # 2. Amenities
        try:
            am = ox.features_from_place(district_name, tags=AMENITY_TAGS)
            result["amenity_count"] = len(am)
        except:
            pass

        # 3. Buildings
        try:
            bl = ox.features_from_place(district_name, tags=BUILDING_TAGS)
            bl_poly = bl[bl.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
            result["building_count"] = len(bl_poly)
        except:
            pass

        # 4. Roads
        try:
            G = ox.graph_from_place(district_name, network_type="drive")
            edges = ox.graph_to_gdfs(G, nodes=False)
            total_m = edges["length"].sum()
            result["road_km"] = total_m / 1000.0
        except:
            pass

        # 5. Leisure / green space
        try:
            ls = ox.features_from_place(district_name, tags=LEISURE_TAGS)
            ls_poly = ls[ls.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
            if len(ls_poly) > 0:
                result["green_area_m2"] = ls_poly.to_crs(CRS_UTM_ACCRA).area.sum()
        except:
            pass

    except Exception as e:
        result["status"] = f"error: {e}"

    return result


# ── 6.2  Process all districts (with caching) ───────────────────────────
cache_path = DATA_DIR / "district_indicators_cache.json"

if cache_path.exists():
    print("\n📂 Loading cached district indicators ...")
    with open(cache_path, "r") as f:
        all_results = json.load(f)
    print(f"   Cached districts: {len(all_results)}")
else:
    all_results = []

cached_names = {r["district"] for r in all_results}
remaining = [d for d in GREATER_ACCRA_DISTRICTS if d not in cached_names]

if remaining:
    print(f"\n🔄 Processing {len(remaining)} remaining districts ...")
    for i, district in enumerate(remaining, 1):
        short_name = district.split(",")[0]
        print(f"\n   [{i}/{len(remaining)}] {short_name} ...", end=" ", flush=True)
        t0 = time.time()
        result = compute_district_indicators(district)
        elapsed = time.time() - t0
        print(f"({elapsed:.0f}s) — {result['status']}")

        # Print key metrics
        a = result["district_area_km2"]
        if a > 0:
            print(f"      Area: {a:.1f} km²  |  "
                  f"Amenities: {result['amenity_count']}  |  "
                  f"Buildings: {result['building_count']}  |  "
                  f"Roads: {result['road_km']:.0f} km")

        all_results.append(result)

        # Save cache after each district
        with open(cache_path, "w") as f:
            json.dump(all_results, f, indent=2)

# ── 6.3  Build the indicator DataFrame ──────────────────────────────────
print("\n📊 Building indicator table ...")
df = pd.DataFrame(all_results)
df["short_name"] = df["district"].apply(lambda x: x.split(",")[0])

# Compute density indicators
df["amenity_density"]  = df["amenity_count"]  / df["district_area_km2"]
df["building_density"] = df["building_count"] / df["district_area_km2"]
df["road_density"]     = df["road_km"]        / df["district_area_km2"]
df["green_ratio"]      = (df["green_area_m2"] / (df["district_area_km2"] * 1e6)) * 100

# Replace inf/nan
df = df.replace([np.inf, -np.inf], 0).fillna(0)

# ── 6.4  Min-max normalisation ───────────────────────────────────────────
indicators = ["amenity_density", "building_density", "road_density", "green_ratio"]

for col in indicators:
    mn, mx = df[col].min(), df[col].max()
    if mx > mn:
        df[f"{col}_norm"] = (df[col] - mn) / (mx - mn)
    else:
        df[f"{col}_norm"] = 0.0

# ── 6.5  Composite livability score (equal weights) ─────────────────────
norm_cols = [f"{c}_norm" for c in indicators]
df["livability_score"] = df[norm_cols].mean(axis=1)
df["livability_rank"]  = df["livability_score"].rank(ascending=False).astype(int)

# Sort by rank
df = df.sort_values("livability_rank")

print("\n── LIVABILITY INDEX — Greater Accra Region ──")
print(f"{'Rank':>4}  {'District':40s}  {'Score':>6}  "
      f"{'Amen':>6}  {'Bldg':>6}  {'Road':>6}  {'Green':>6}")
print("-" * 90)
for _, row in df.iterrows():
    print(f"{row['livability_rank']:>4}  {row['short_name']:40s}  "
          f"{row['livability_score']:.3f}  "
          f"{row['amenity_density_norm']:.3f}  "
          f"{row['building_density_norm']:.3f}  "
          f"{row['road_density_norm']:.3f}  "
          f"{row['green_ratio_norm']:.3f}")

# ── 6.6  Save results ───────────────────────────────────────────────────
csv_path = OUTPUT_DIR / "livability_index.csv"
df.to_csv(csv_path, index=False)
print(f"\n💾 Index table → {csv_path}")

# ── 6.7  Choropleth map — Livability by district ────────────────────────
print("\n🎨 Creating livability choropleth ...")

# Pull all district boundaries for mapping
print("   Pulling district boundaries for mapping ...")
district_gdfs = []
for district_name in GREATER_ACCRA_DISTRICTS:
    try:
        gdf = ox.geocode_to_gdf(district_name)
        gdf["district"] = district_name
        district_gdfs.append(gdf)
    except:
        pass

if district_gdfs:
    districts_gdf = pd.concat(district_gdfs, ignore_index=True)

    # Merge livability scores
    districts_gdf = districts_gdf.merge(
        df[["district", "livability_score", "livability_rank", "short_name"]],
        on="district", how="left"
    )

    # Plot choropleth
    fig, ax = plt.subplots(1, 1, figsize=(18, 14))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    districts_gdf.to_crs(CRS_WEB_MERCATOR).plot(
        ax=ax,
        column="livability_score",
        cmap="RdYlGn",
        edgecolor="white",
        linewidth=1.5,
        alpha=0.8,
        legend=False,
    )

    # Add district labels
    for _, row in districts_gdf.to_crs(CRS_WEB_MERCATOR).iterrows():
        centroid = row.geometry.centroid
        label = row.get("short_name", "")
        if label and len(label) < 35:
            short = label.replace(" Municipal District", "").replace(
                " Metropolitan District", "").replace(" District", "")
            ax.annotate(
                short, xy=(centroid.x, centroid.y),
                fontsize=5.5, color="white", ha="center", va="center",
                fontweight="bold",
                path_effects=[
                    plt.matplotlib.patheffects.withStroke(
                        linewidth=2, foreground="black"
                    )
                ],
            )

    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=11)
    ax.set_axis_off()
    ax.set_title(
        f"LIVABILITY INDEX — Greater Accra Region (29 MMDAs)",
        fontsize=18, fontweight="bold", color="white", pad=20,
    )

    # Colour bar
    sm = plt.cm.ScalarMappable(
        cmap="RdYlGn",
        norm=mcolors.Normalize(
            vmin=districts_gdf["livability_score"].min(),
            vmax=districts_gdf["livability_score"].max()
        ),
    )
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.02, shrink=0.6)
    cbar.set_label("Livability Score", color="white", fontsize=12)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

    fig.tight_layout()
    fig_path = FIGURES_DIR / "ch6_livability_index.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"🖼  Livability map → {fig_path}")

    # Save district boundaries with scores
    districts_path = DATA_DIR / "districts_with_scores.gpkg"
    districts_gdf.to_file(districts_path, driver="GPKG")
    print(f"💾 District data  → {districts_path}")

print("\n" + "=" * 65)
print("  🎉  PIPELINE COMPLETE — Python for Urban Analysis (Ghana)")
print("=" * 65)
print("""
You now have a complete, reusable urban analytics pipeline.

To re-target it at any city on Earth:
  1. Open config.py
  2. Change STUDY_AREA to your target city
  3. Update the district list for Chapter 6
  4. Re-run chapters 1–6

Outputs produced:
  📁 data/          — GeoPackages for all layers
  📁 outputs/       — CSV tables and HTML maps
  📁 outputs/figures/ — All publication-ready maps
""")
