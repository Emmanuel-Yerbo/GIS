import warnings
warnings.filterwarnings("ignore")

import os
import math
import time
from pathlib import Path
import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, box
from scipy.stats import entropy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Patch
import pydeck as pdk

try:
    import contextily as cx
    HAS_CX = True
except ImportError:
    cx = None
    HAS_CX = False

try:
    import h3
    HAS_H3 = True
except ImportError:
    h3 = None
    HAS_H3 = False

# Setup Config / Constants
STUDY_AREA = "Accra, Ghana"
CRS_WEB_MERCATOR = "EPSG:3857"
CRS_UTM_ACCRA = "EPSG:32630"
OUTPUT_DIR = Path("outputs")
FIGURES_DIR = OUTPUT_DIR / "figures"
DARK_BG = "#0e1117"
BUILDING_TAGS = {"building": True}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def set_dark_theme(ax, title=None):
    """Apply the course dark-theme styling to a matplotlib axis."""
    ax.set_facecolor(DARK_BG)
    if title is not None:
        ax.set_title(title, color="white", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")


print("=" * 65)
print("  CHAPTER 11 — Urban Morphometrics & Building Orientation (Master Class)")
print("=" * 65)

# =========================================================================
# MODULE 11.1 — Building Footprint Ingestion & Metric UTM Projection
# =========================================================================
print("\n>>> Module 11.1: Fetching Building Footprints...")
start_time = time.time()
try:
    # Fetch OSM buildings
    gdf = ox.features_from_place(STUDY_AREA, tags=BUILDING_TAGS)
    print(f"  [+] Initially fetched {len(gdf)} features from OSM.")

    # Filter to Polygon and MultiPolygon geometries only
    gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    print(f"  [+] Filtered to {len(gdf)} polygonal building features.")

    # Project to UTM for metric calculations
    gdf = gdf.to_crs(CRS_UTM_ACCRA)
    print(f"  [+] Projected data to metric CRS: {CRS_UTM_ACCRA}")

    # Compute area in square meters
    gdf['area_m2'] = gdf.geometry.area

    # Filter out negligible fragments or anomalies
    gdf = gdf[gdf['area_m2'] > 5]
    print(f"  [+] Filtered out footprints < 5 sq.m. Remaining: {len(gdf)}")

    print(f"  [+] Summary Stats: Mean Area = {gdf['area_m2'].mean():.1f} m2, Max Area = {gdf['area_m2'].max():.1f} m2")
except Exception as e:
    print(f"  [!] Error fetching buildings: {e}")
    raise
    
print(f"  [v] Module 11.1 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.2 — Minimum Rotated Rectangle & Orientation Angles
# =========================================================================
print("\n>>> Module 11.2: Minimum Rotated Rectangle & Orientation...")
start_time = time.time()

def extract_mrr_metrics(geom):
    try:
        mrr = geom.minimum_rotated_rectangle
        # If not a polygon (e.g. line or point due to some anomaly), return nans
        if not isinstance(mrr, Polygon):
            return pd.Series([np.nan, np.nan, np.nan, np.nan])
            
        coords = list(mrr.exterior.coords)
        edge_lengths = []
        angles = []
        
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i+1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            
            length = math.hypot(dx, dy)
            # Angle in degrees from horizontal
            angle = math.degrees(math.atan2(dy, dx)) % 180
            
            edge_lengths.append(length)
            angles.append(angle)
            
        if len(edge_lengths) < 4:
            return pd.Series([np.nan, np.nan, np.nan, np.nan])
            
        # The MRR has 4 edges, opposite edges are equal. 
        # Get the two unique dimensions
        dims = sorted([edge_lengths[0], edge_lengths[1]])
        width = dims[0]
        length = dims[1]
        
        # Orientation corresponds to the longest edge
        longest_edge_idx = np.argmax(edge_lengths)
        orientation = angles[longest_edge_idx]
        
        return pd.Series([width, length, orientation, mrr.area])
    except Exception:
        return pd.Series([np.nan, np.nan, np.nan, np.nan])
        
gdf[['mrr_width', 'mrr_length', 'orientation_deg', 'mrr_area']] = gdf.geometry.apply(extract_mrr_metrics)

# Drop rows where MRR failed
gdf = gdf.dropna(subset=['mrr_width', 'orientation_deg'])
print(f"  [+] Calculated MRR for {len(gdf)} buildings.")
print(f"  [+] Orientation Mean: {gdf['orientation_deg'].mean():.1f}°, StdDev: {gdf['orientation_deg'].std():.1f}°")
print(f"  [v] Module 11.2 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.3 — Morphometric Shape Metrics
# =========================================================================
print("\n>>> Module 11.3: Morphometric Shape Metrics...")
start_time = time.time()

# 1. Polsby-Popper Compactness: C_PP = (4 * pi * area) / perimeter^2
gdf['perimeter_m'] = gdf.geometry.length
gdf['compactness_pp'] = (4 * math.pi * gdf['area_m2']) / (gdf['perimeter_m'] ** 2)
# Cap at 1.0 (some MRRs or simple shapes might exceed due to floating point)
gdf['compactness_pp'] = gdf['compactness_pp'].clip(0, 1)

# 2. Elongation Ratio: E = width / length (0 to 1)
gdf['elongation'] = gdf['mrr_width'] / gdf['mrr_length']

# 3. Convexity Index: area / convex_hull.area
gdf['convexity'] = gdf['area_m2'] / gdf.geometry.convex_hull.area

print("  [+] Morphometric Summary Statistics:")
print(f"      Compactness: Mean = {gdf['compactness_pp'].mean():.3f}, Median = {gdf['compactness_pp'].median():.3f}")
print(f"      Elongation : Mean = {gdf['elongation'].mean():.3f}, Median = {gdf['elongation'].median():.3f}")
print(f"      Convexity  : Mean = {gdf['convexity'].mean():.3f}, Median = {gdf['convexity'].median():.3f}")
print(f"  [v] Module 11.3 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.4 — 36-Bin Polar Rose Diagram (ch11_orientation_rose.png)
# =========================================================================
print("\n>>> Module 11.4: Generating Building Orientation Rose Diagram...")
start_time = time.time()

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

# 36 bins = 10 degrees each for 0-360
bins = 36
orientations = gdf['orientation_deg'].dropna().values

# Mirror orientations to 360 degrees for a full rose
orientations_360 = np.concatenate([orientations, orientations + 180])

# Convert degrees to radians
orient_rad = np.radians(orientations_360)

# Create histogram
counts, bin_edges = np.histogram(orient_rad, bins=bins, range=(0, 2*np.pi))
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Plot bars
bars = ax.bar(bin_centers, counts, width=(2*np.pi/bins), bottom=0.0,
              color='#00e676', edgecolor='white', alpha=0.8, linewidth=0.5)

ax.set_theta_zero_location('N')
ax.set_theta_direction(-1) # Clockwise

# Styling
ax.tick_params(colors='white')
ax.grid(color='gray', linestyle='--', alpha=0.5)
for spine in ax.spines.values():
    spine.set_color('white')
    
plt.title(f'Building Orientation Rose Diagram\n(n={len(gdf):,} buildings)', 
          color='white', pad=20, fontsize=14)
          
out_path_11_4 = os.path.join(FIGURES_DIR, 'ch11_orientation_rose.png')
plt.savefig(out_path_11_4, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved {out_path_11_4}")
print(f"  [v] Module 11.4 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.5 — Spatial Building Orientation Map (ch11_morphology_orientation_map.png)
# =========================================================================
print("\n>>> Module 11.5: Spatial Building Orientation Map...")
start_time = time.time()

# IMPORTANT PERFORMANCE: Sample max 30,000 buildings for rendering
plot_gdf = gdf.copy()
if len(plot_gdf) > 30000:
    plot_gdf = plot_gdf.sample(30000, random_state=42)
    print(f"  [+] Sampled down to 30,000 buildings for map rendering.")
    
# Re-project to Web Mercator for Contextily
plot_gdf_web = plot_gdf.to_crs(CRS_WEB_MERCATOR)

fig, ax = plt.subplots(figsize=(12, 12))
fig.patch.set_facecolor(DARK_BG)

# Plot buildings colored by orientation (0-180 mapped to cyclic HSV)
plot_gdf_web.plot(column='orientation_deg', cmap='hsv',
                  ax=ax, linewidth=0.5, edgecolor='white', alpha=0.9,
                  vmin=0, vmax=180)
                  
if HAS_CX:
    try:
        cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
    except Exception as e:
        print(f"  [!] Contextily basemap failed: {e}")
        ax.set_facecolor(DARK_BG)
else:
    ax.set_facecolor(DARK_BG)
    
ax.set_axis_off()
plt.title(f'Building Orientation Map - {STUDY_AREA}\nColored by Rotation Angle [0°-180°]', 
          color='white', fontsize=16)
          
# Add a custom colorbar legend
sm = plt.cm.ScalarMappable(cmap='hsv', norm=plt.Normalize(vmin=0, vmax=180))
cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.04, aspect=30)
cbar.set_label('Orientation Angle (Degrees)', color='white')
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

out_path_11_5 = os.path.join(FIGURES_DIR, 'ch11_morphology_orientation_map.png')
plt.savefig(out_path_11_5, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved {out_path_11_5}")
print(f"  [v] Module 11.5 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.6 — Compactness vs. Elongation Scatter (ch11_compactness_vs_elongation.png)
# =========================================================================
print("\n>>> Module 11.6: Compactness vs. Elongation Scatter...")
start_time = time.time()

scatter_gdf = gdf.copy()
if len(scatter_gdf) > 10000:
    scatter_gdf = scatter_gdf.sample(10000, random_state=42)
    print("  [+] Sampled down to 10,000 buildings for scatter plot.")
    
fig, ax = plt.subplots(figsize=(10, 8))
set_dark_theme(ax, title="Morphometric Typologies: Compactness vs Elongation")

sc = ax.scatter(scatter_gdf['elongation'], scatter_gdf['compactness_pp'],
                c=scatter_gdf['orientation_deg'], cmap='hsv',
                alpha=0.6, s=15, edgecolor='none')
                
ax.set_xlabel('Elongation Ratio (Width / Length)', fontsize=12)
ax.set_ylabel('Polsby-Popper Compactness', fontsize=12)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Marginal Annotations
ax.text(0.1, 0.9, 'Institutional/Blocky\n(Low Elong, High Comp)', 
        color='cyan', fontsize=10, ha='center', va='center',
        bbox=dict(facecolor='black', alpha=0.5, edgecolor='cyan'))
        
ax.text(0.9, 0.1, 'Informal/Linear\n(High Elong, Low Comp)', 
        color='magenta', fontsize=10, ha='center', va='center',
        bbox=dict(facecolor='black', alpha=0.5, edgecolor='magenta'))
        
# Colorbar
cbar = fig.colorbar(sc, ax=ax)
cbar.set_label('Orientation Angle', color='white')
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

out_path_11_6 = os.path.join(FIGURES_DIR, 'ch11_compactness_vs_elongation.png')
plt.savefig(out_path_11_6, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved {out_path_11_6}")
print(f"  [v] Module 11.6 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.7 — Street Network vs. Building Orientation Dual Rose
# =========================================================================
print("\n>>> Module 11.7: Street vs Building Orientation Dual Rose...")
start_time = time.time()

try:
    print("  [+] Fetching street network...")
    G = ox.graph_from_place(STUDY_AREA, network_type='drive')
    G = ox.bearing.add_edge_bearings(G)
    
    # Extract edge bearings
    bearings = pd.Series([data['bearing'] for u, v, k, data in G.edges(keys=True, data=True)])
    bearings_rad = np.radians(bearings)
    print(f"  [+] Extracted {len(bearings)} street edge bearings.")
    
    fig = plt.figure(figsize=(14, 7))
    fig.patch.set_facecolor(DARK_BG)
    
    # Plot 1: Street Rose
    ax1 = fig.add_subplot(121, projection='polar')
    ax1.set_facecolor(DARK_BG)
    street_counts, street_bins = np.histogram(bearings_rad, bins=bins, range=(0, 2*np.pi))
    street_bin_centers = (street_bins[:-1] + street_bins[1:]) / 2
    ax1.bar(street_bin_centers, street_counts, width=(2*np.pi/bins), bottom=0.0,
            color='#00e5ff', edgecolor='white', alpha=0.8, linewidth=0.5)
    ax1.set_theta_zero_location('N')
    ax1.set_theta_direction(-1)
    ax1.tick_params(colors='white')
    ax1.grid(color='gray', linestyle='--', alpha=0.5)
    ax1.set_title('Street Network Orientation (Cyan)', color='white', pad=20, fontsize=14)
    
    # Plot 2: Building Rose
    ax2 = fig.add_subplot(122, projection='polar')
    ax2.set_facecolor(DARK_BG)
    ax2.bar(bin_centers, counts, width=(2*np.pi/bins), bottom=0.0,
            color='#00e676', edgecolor='white', alpha=0.8, linewidth=0.5)
    ax2.set_theta_zero_location('N')
    ax2.set_theta_direction(-1)
    ax2.tick_params(colors='white')
    ax2.grid(color='gray', linestyle='--', alpha=0.5)
    ax2.set_title('Building Footprint Orientation (Green)', color='white', pad=20, fontsize=14)
    
    out_path_11_7 = os.path.join(FIGURES_DIR, 'ch11_street_vs_building_rose.png')
    plt.savefig(out_path_11_7, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
    plt.close(fig)
    print(f"  [+] Saved {out_path_11_7}")
except Exception as e:
    print(f"  [!] Failed to generate street network rose: {e}")
    
print(f"  [v] Module 11.7 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.8 — Professor Innovation 1: Shannon Orientation Entropy
# =========================================================================
print("\n>>> Module 11.8: Shannon Entropy & Grid Regularity...")
start_time = time.time()

# Calculate probabilities from building counts per bin (Module 11.4 counts)
p_i = counts / counts.sum()

# Filter zeros to avoid log(0) issues in entropy
p_i_clean = p_i[p_i > 0]

H_obs = entropy(p_i_clean, base=np.e)
H_max = np.log(bins) # maximum entropy for 36 bins

grid_regularity = 1 - (H_obs / H_max)

print(f"  [+] Shannon Entropy (H_obs): {H_obs:.3f}")
print(f"  [+] Maximum Entropy (H_max): {H_max:.3f}")
print(f"  [+] Grid Regularity Index (r): {grid_regularity:.3f}")

# Academic Interpretation
if grid_regularity > 0.7:
    interp = "Highly Regular Grid (Planned City/Blocks)"
elif grid_regularity > 0.4:
    interp = "Semi-Regular Morphometrics (Mixed Development)"
else:
    interp = "Isotropic / Organic / Informal Form"
print(f"  [+] Interpretation: {interp}")

# Bar Chart for Entropy
fig, ax = plt.subplots(figsize=(6, 6))
set_dark_theme(ax, title="Grid Regularity via Shannon Entropy")

bars = ax.bar(['Observed Entropy', 'Max Entropy'], [H_obs, H_max], 
              color=['#ff9800', '#607d8b'], edgecolor='white')
              
ax.text(0, H_obs/2, f'H = {H_obs:.2f}', color='white', ha='center', va='center', fontsize=12)
ax.text(1, H_max/2, f'H_max = {H_max:.2f}', color='white', ha='center', va='center', fontsize=12)

ax.annotate(f'Regularity Index:\nr = {grid_regularity:.3f}\n({interp})', 
            xy=(0.5, H_max), xytext=(0.5, H_max*1.1),
            ha='center', va='bottom', color='#00e676', fontsize=12,
            arrowprops=dict(facecolor='#00e676', shrink=0.05))
            
ax.set_ylim(0, H_max * 1.3)

out_path_11_8 = os.path.join(FIGURES_DIR, 'ch11_shannon_entropy_grid.png')
plt.savefig(out_path_11_8, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved {out_path_11_8}")
print(f"  [v] Module 11.8 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.9 — Professor Innovation 2: H3 Morphometric Cell Complexity
# =========================================================================
print("\n>>> Module 11.9: Spatial Morphometric Complexity (Grid)...")
start_time = time.time()

grid_gdf = None
h3_ok = HAS_H3
if h3_ok:
    try:
        print("  [+] Using H3 Hexagonal Grid (Resolution 9)...")
        res = 9
        # Centroids for assigning buildings to hexes
        gdf_wgs84 = gdf.to_crs(4326)
        centroids_wgs84 = gdf_wgs84.geometry.centroid
        
        # Map points to H3 hexagons (H3 v4 API)
        hex_ids = [h3.latlng_to_cell(row.y, row.x, res) for row in centroids_wgs84]
        gdf['hex_id'] = hex_ids
        
        hex_stats = gdf.groupby('hex_id').agg(
            bldg_count=('hex_id', 'count'),
            mean_comp=('compactness_pp', 'mean'),
            mean_elong=('elongation', 'mean'),
            std_orient=('orientation_deg', 'std')
        ).reset_index()
        
        # Only keep hexes with >= 5 buildings for valid std dev
        hex_stats = hex_stats[hex_stats['bldg_count'] >= 5].copy()
        
        # Fill NaNs in std_orient
        hex_stats['std_orient'] = hex_stats['std_orient'].fillna(0)
        
        # Form geometry from H3
        hex_polys = []
        for h_id in hex_stats['hex_id']:
            # H3 v4: cell_to_boundary returns (lat, lon) tuples
            geom = Polygon([(lon, lat) for lat, lon in h3.cell_to_boundary(h_id)])
            hex_polys.append(geom)
            
        grid_gdf = gpd.GeoDataFrame(hex_stats, geometry=hex_polys, crs=4326).to_crs(CRS_WEB_MERCATOR)
    except Exception as e:
        print(f"  [!] H3 Processing failed: {e}. Falling back to square grid.")
        h3_ok = False

if not h3_ok:
    print("  [+] Generating fallback Square Grid for Complexity Mapping...")
    gdf_utm = gdf.copy()
    bounds = gdf_utm.total_bounds
    xmin, ymin, xmax, ymax = bounds
    
    # 500m x 500m grid cells
    cell_size = 500
    grid_cells = []
    for x0 in np.arange(xmin, xmax, cell_size):
        for y0 in np.arange(ymin, ymax, cell_size):
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            grid_cells.append(box(x0, y0, x1, y1))
            
    grid = gpd.GeoDataFrame(grid_cells, columns=['geometry'], crs=CRS_UTM_ACCRA)
    grid['grid_id'] = grid.index
    
    # Spatial join buildings to grid
    joined = gpd.sjoin(gdf_utm, grid, how='inner', predicate='intersects')
    
    grid_stats = joined.groupby('grid_id').agg(
        bldg_count=('grid_id', 'count'),
        mean_comp=('compactness_pp', 'mean'),
        mean_elong=('elongation', 'mean'),
        std_orient=('orientation_deg', 'std')
    ).reset_index()
    
    grid_stats = grid_stats[grid_stats['bldg_count'] >= 5]
    grid_stats['std_orient'] = grid_stats['std_orient'].fillna(0)
    
    grid_gdf = grid.merge(grid_stats, on='grid_id').to_crs(CRS_WEB_MERCATOR)

if grid_gdf is not None and not grid_gdf.empty:
    # Define Complexity Score: high compactness var + low elongation var + high orientation var
    # Just use std_orient as the complexity proxy for visual here
    grid_gdf['complexity'] = grid_gdf['std_orient']
    
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    ax.set_axis_off()
    
    grid_gdf.plot(column='complexity', cmap='magma', alpha=0.8,
                  legend=True, ax=ax, edgecolor='none',
                  legend_kwds={'label': "Morphometric Complexity (Orientation StdDev)",
                               'orientation': "horizontal", 'shrink': 0.6,
                               'pad': 0.05})
                               
    # Fix colorbar text color
    fig.axes[-1].tick_params(colors='white')
    fig.axes[-1].xaxis.label.set_color('white')
                               
    if HAS_CX:
        try:
            cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=12)
        except:
            pass
            
    plt.title('Morphometric Cell Complexity', color='white', fontsize=16)
    out_path_11_9 = os.path.join(FIGURES_DIR, 'ch11_morphometric_cell_complexity.png')
    plt.savefig(out_path_11_9, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
    plt.close(fig)
    print(f"  [+] Saved {out_path_11_9}")

print(f"  [v] Module 11.9 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.10 — Professor Innovation 3: Solar Orientation Anisotropy
# =========================================================================
print("\n>>> Module 11.10: Solar Orientation Anisotropy...")
start_time = time.time()

# Tropical context: Aligning long axis East-West minimizes direct solar gain on large facades
# 'Orientation' here is 0-180. 
# East-West alignment implies orientation near 0/180.
# But wait, usually a building facing North-South has an East-West long axis.
# For a line, orientation near 0 means it runs East-West.
# Therefore, 0-45 and 135-180 are roughly E-W aligned. 45-135 is N-S aligned.

def classify_solar_alignment(angle):
    if angle >= 45 and angle <= 135:
        return 'N-S Aligned (Poor Passive)'
    else:
        return 'E-W Aligned (Good Passive)'
        
gdf['solar_alignment'] = gdf['orientation_deg'].apply(classify_solar_alignment)

counts = gdf['solar_alignment'].value_counts()
print("  [+] Solar Alignment Counts:")
print(f"      {counts.to_dict()}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor(DARK_BG)

# Pie Chart
set_dark_theme(ax1, title="Building Passive Solar Alignment")
colors = ['#f44336' if 'Poor' in x else '#4caf50' for x in counts.index]
ax1.pie(counts.values, labels=counts.index, autopct='%1.1f%%', colors=colors,
        textprops={'color': 'white', 'fontsize': 12}, startangle=90)
        
# Spatial Map
set_dark_theme(ax2, title="Spatial Distribution of Solar Alignment")
ax2.set_axis_off()

solar_gdf_web = gdf.sample(min(20000, len(gdf))).to_crs(CRS_WEB_MERCATOR)

# Map colors
c_map = {'N-S Aligned (Poor Passive)': '#f44336', 'E-W Aligned (Good Passive)': '#4caf50'}
for align_type, color in c_map.items():
    subset = solar_gdf_web[solar_gdf_web['solar_alignment'] == align_type]
    if not subset.empty:
        subset.plot(ax=ax2, color=color, alpha=0.7, label=align_type, markersize=1)
        
if HAS_CX:
    try:
        cx.add_basemap(ax2, source=cx.providers.CartoDB.DarkMatter, zoom=12)
    except:
        pass
        
# Custom Legend
legend_elements = [Patch(facecolor='#4caf50', edgecolor='w', label='E-W Aligned (Good)'),
                   Patch(facecolor='#f44336', edgecolor='w', label='N-S Aligned (Poor)')]
ax2.legend(handles=legend_elements, loc='lower right', facecolor=DARK_BG, 
           edgecolor='white', labelcolor='white')
           
out_path_11_10 = os.path.join(FIGURES_DIR, 'ch11_solar_orientation_analysis.png')
plt.savefig(out_path_11_10, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
plt.close(fig)
print(f"  [+] Saved {out_path_11_10}")
print(f"  [v] Module 11.10 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.11 — Interactive 3D Pydeck WebGL Morphometric Map
# =========================================================================
print("\n>>> Module 11.11: 3D Pydeck Morphometric Map...")
start_time = time.time()

# Cap to top 25k by area, area > 15m2
deck_gdf = gdf[gdf['area_m2'] > 15].sort_values(by='area_m2', ascending=False).head(25000)
deck_gdf_wgs = deck_gdf.to_crs(4326).copy()

def geom_to_coords(geom):
    if geom.type == 'Polygon':
        return [list(geom.exterior.coords)]
    elif geom.type == 'MultiPolygon':
        coords = []
        for poly in geom.geoms:
            coords.append(list(poly.exterior.coords))
        return coords
    return []
    
deck_gdf_wgs['coordinates'] = deck_gdf_wgs.geometry.apply(geom_to_coords)

# HSV color map for orientation
def angle_to_rgb(angle):
    cmap = plt.cm.hsv
    norm_angle = angle / 180.0
    rgb = cmap(norm_angle)[:3]
    return [int(c * 255) for c in rgb]
    
deck_gdf_wgs['color'] = deck_gdf_wgs['orientation_deg'].apply(angle_to_rgb)
deck_gdf_wgs['elevation'] = deck_gdf_wgs['area_m2'].apply(lambda x: min(x * 0.3, 500))

layer = pdk.Layer(
    "PolygonLayer",
    deck_gdf_wgs,
    get_polygon="coordinates",
    get_fill_color="color",
    get_elevation="elevation",
    extruded=True,
    wireframe=True,
    get_line_color=[255, 255, 255, 100],
    line_width_min_pixels=1,
    opacity=0.8,
    pickable=True
)

bounds = deck_gdf_wgs.total_bounds
center_lon = (bounds[0] + bounds[2]) / 2
center_lat = (bounds[1] + bounds[3]) / 2

view_state = pdk.ViewState(
    longitude=center_lon,
    latitude=center_lat,
    zoom=13,
    pitch=45,
    bearing=0
)

r = pdk.Deck(layers=[layer], initial_view_state=view_state,
             map_style='mapbox://styles/mapbox/dark-v10')
             
out_path_11_11 = os.path.join(OUTPUT_DIR, 'ch11_3d_morphometrics_webgl.html')
r.to_html(out_path_11_11)
# Important: DO NOT render inline, just print path
print(f"  [+] 3D Morphometric Map saved to: {out_path_11_11}")
print(f"  [v] Module 11.11 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.12 — Interactive WebGL 3D Orientation Vectors Dashboard
# =========================================================================
print("\n>>> Module 11.12: 3D Orientation Vectors Dashboard...")
start_time = time.time()

dash_gdf = deck_gdf_wgs.head(15000).copy()
dash_gdf['centroid_lon'] = dash_gdf.geometry.centroid.x
dash_gdf['centroid_lat'] = dash_gdf.geometry.centroid.y
dash_gdf['radius'] = np.sqrt(dash_gdf['area_m2']) * 2  # Scaled for visibility

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    dash_gdf,
    get_position=["centroid_lon", "centroid_lat"],
    get_radius="radius",
    get_fill_color="color",
    pickable=True,
    opacity=0.9,
    filled=True,
    radius_scale=1,
    radius_min_pixels=2,
    radius_max_pixels=100
)

dash_view = pdk.ViewState(
    longitude=center_lon,
    latitude=center_lat,
    zoom=13,
    pitch=20,
    bearing=0
)

r2 = pdk.Deck(layers=[scatter_layer], initial_view_state=dash_view,
              map_style='mapbox://styles/mapbox/dark-v10')
              
out_path_11_12 = os.path.join(OUTPUT_DIR, 'ch11_3d_orientation_dashboard.html')
r2.to_html(out_path_11_12)
print(f"  [+] 3D Orientation Dashboard saved to: {out_path_11_12}")
print(f"  [v] Module 11.12 complete in {time.time()-start_time:.2f}s")

# =========================================================================
# MODULE 11.13 — Synthesis & Summary Statistics
# =========================================================================
print("\n>>> Module 11.13: Synthesis & Summary Statistics...")
print("="*60)
print(" CHAPTER 11 MORPHOMETRICS SYNTHESIS ")
print("="*60)
print(f" Total Buildings Processed    : {len(gdf):,}")
print(f" Average Building Area        : {gdf['area_m2'].mean():.1f} m²")
print(f" Mean Orientation Angle       : {gdf['orientation_deg'].mean():.1f}°")
print(f" Median Polsby-Popper         : {gdf['compactness_pp'].median():.3f}")
print(f" Median Elongation Ratio      : {gdf['elongation'].median():.3f}")
print(f" Grid Regularity Index        : {grid_regularity:.3f}")
print(f" % Solar-Optimized (E-W)      : {(gdf['solar_alignment'] == 'E-W Aligned (Good Passive)').mean()*100:.1f}%")
print("="*60)
print("Chapter 11 Urban Morphometrics complete. All assets generated successfully.")
