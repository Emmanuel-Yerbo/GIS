"""
=============================================================================
CHAPTER 4 — Road Networks: Drivable vs. Walkable, Statistics & Hubs
=============================================================================
Learning objectives
───────────────────
1. Download drivable and walkable networks from OSM
2. Compute basic network statistics (nodes, edges, density, circuity)
3. Calculate betweenness centrality to find network hubs
4. Classify roads by type (motorway, primary, residential, etc.)
5. Visualise networks with centrality-based colouring

Ghana context
─────────────
Accra's road network tells a story of rapid, largely unplanned
urbanisation.  Major arterials (N1, George Walker Bush Highway,
Liberation Road) carry enormous loads, while the residential
network is dense but poorly connected — a pattern typical of
Sub-Saharan African cities.

Professor's note
─────────────────
  "A road network is a GRAPH.  Thinking of streets as edges and
   intersections as nodes unlocks the entire apparatus of network
   science — centrality, shortest paths, connectivity, resilience."
=============================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import osmnx as ox
import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import contextily as cx
from config import (
    STUDY_AREA, CRS_WEB_MERCATOR, CRS_UTM_ACCRA,
    DATA_DIR, FIGURES_DIR, DARK_BG, ROAD_CMAP, EDGE_COLOR,
)

print("=" * 65)
print("  CHAPTER 4 — Road Networks")
print("=" * 65)

# ── 4.1  Download drivable network ───────────────────────────────────────
print("\n🚗 Pulling DRIVABLE network ...")
G_drive = ox.graph_from_place(STUDY_AREA, network_type="drive")
print(f"   Nodes: {G_drive.number_of_nodes():,}")
print(f"   Edges: {G_drive.number_of_edges():,}")

# ── 4.2  Download walkable network ──────────────────────────────────────
print("\n🚶 Pulling WALKABLE network ...")
G_walk = ox.graph_from_place(STUDY_AREA, network_type="walk")
print(f"   Nodes: {G_walk.number_of_nodes():,}")
print(f"   Edges: {G_walk.number_of_edges():,}")

# ── 4.3  Basic network statistics ────────────────────────────────────────
print("\n── Network Statistics (Drivable) ──")
stats_drive = ox.stats.basic_stats(G_drive)
for key in ["n", "m", "k_avg", "edge_length_total",
            "edge_length_avg", "streets_per_node_avg",
            "circuity_avg"]:
    if key in stats_drive:
        val = stats_drive[key]
        if isinstance(val, float):
            print(f"   {key:30s}  {val:>12.2f}")
        else:
            print(f"   {key:30s}  {val:>12,}")

print("\n── Network Statistics (Walkable) ──")
stats_walk = ox.stats.basic_stats(G_walk)
for key in ["n", "m", "k_avg", "edge_length_total",
            "edge_length_avg", "streets_per_node_avg",
            "circuity_avg"]:
    if key in stats_walk:
        val = stats_walk[key]
        if isinstance(val, float):
            print(f"   {key:30s}  {val:>12.2f}")
        else:
            print(f"   {key:30s}  {val:>12,}")

# ── 4.4  Betweenness centrality — finding network hubs ──────────────────
print("\n🔬 Computing betweenness centrality (this may take a moment) ...")

# Add edge speeds and travel times
G_drive = ox.routing.add_edge_speeds(G_drive)
G_drive = ox.routing.add_edge_travel_times(G_drive)

# Convert to DiGraph (required for centrality)
D = ox.convert.to_digraph(G_drive, weight="travel_time")

# Compute betweenness centrality (sample k nodes for performance)
k_sample = min(500, D.number_of_nodes())
bc = nx.betweenness_centrality(D, weight="travel_time", k=k_sample)

# Add back to graph
nx.set_node_attributes(G_drive, values=bc, name="bc")

# Report top hubs
bc_sorted = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:10]
print("\n── Top 10 Network Hubs (Betweenness Centrality) ──")
for node_id, score in bc_sorted:
    lat = G_drive.nodes[node_id].get("y", 0)
    lon = G_drive.nodes[node_id].get("x", 0)
    print(f"   Node {node_id:>12}  BC={score:.4f}  ({lat:.4f}, {lon:.4f})")

# ── 4.5  Road type classification ───────────────────────────────────────
print("\n🛣  Classifying roads by type ...")
edges = ox.graph_to_gdfs(G_drive, nodes=False, edges=True)

# highway tag can be a list — flatten
def flatten_highway(val):
    if isinstance(val, list):
        return val[0]
    return val

edges["road_type"] = edges["highway"].apply(flatten_highway)

print("\n── Road type breakdown ──")
road_counts = edges["road_type"].value_counts().head(15)
for rtype, n in road_counts.items():
    print(f"   {rtype:25s}  {n:>6}")

# ── 4.6  Visualise: Drivable network with centrality ────────────────────
print("\n🎨 Creating network centrality map ...")

# Get node colours based on betweenness centrality
node_colors = ox.plot.get_node_colors_by_attr(G_drive, "bc", cmap="plasma")

fig, ax = ox.plot.plot_graph(
    G_drive,
    node_color=node_colors,
    node_size=8,
    node_zorder=3,
    edge_color="#444444",
    edge_linewidth=0.5,
    bgcolor=DARK_BG,
    figsize=(16, 16),
    show=False,
    close=False,
)
ax.set_title(
    f"Road Network Centrality — {STUDY_AREA}",
    fontsize=16, fontweight="bold", color="white", pad=20
)

fig_path = FIGURES_DIR / "ch4_network_centrality.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  Centrality map → {fig_path}")

# ── 4.7  Visualise: Road types with basemap ─────────────────────────────
print("\n🎨 Creating road type map ...")

road_palette = {
    "motorway":      "#ff1744",
    "motorway_link": "#ff5252",
    "trunk":         "#ff9100",
    "trunk_link":    "#ffab40",
    "primary":       "#ffc400",
    "primary_link":  "#ffd740",
    "secondary":     "#69f0ae",
    "secondary_link":"#b9f6ca",
    "tertiary":      "#40c4ff",
    "tertiary_link": "#80d8ff",
    "residential":   "#b0bec5",
    "unclassified":  "#78909c",
    "service":       "#546e7a",
}

edges["color"] = edges["road_type"].map(road_palette).fillna("#37474f")

boundary = ox.geocode_to_gdf(STUDY_AREA)

fig, ax = plt.subplots(1, 1, figsize=(16, 16))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)

edges.to_crs(CRS_WEB_MERCATOR).plot(
    ax=ax, color=edges["color"], linewidth=0.6, alpha=0.8
)

boundary.to_crs(CRS_WEB_MERCATOR).plot(
    ax=ax, facecolor="none", edgecolor="white", linewidth=2, zorder=10
)

cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
ax.set_axis_off()
ax.set_title(
    f"Road Types — {STUDY_AREA}",
    fontsize=16, fontweight="bold", color="white", pad=20,
)

import matplotlib.patches as mpatches
handles = [
    mpatches.Patch(color=c, label=t)
    for t, c in road_palette.items()
]
ax.legend(
    handles=handles, loc="lower left", fontsize=7,
    facecolor="#1a1a2e", edgecolor="white",
    labelcolor="white", framealpha=0.9, ncol=2
)

fig.tight_layout()
fig_path = FIGURES_DIR / "ch4_road_types.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  Road type map → {fig_path}")

# ── 4.8  Compare walk vs drive ───────────────────────────────────────────
print("\n🎨 Creating walk vs drive comparison ...")

fig, axes = plt.subplots(1, 2, figsize=(24, 12))
for i, (G, title) in enumerate([
    (G_drive, "Drivable Network"),
    (G_walk,  "Walkable Network"),
]):
    ax = axes[i]
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)

    edges_g = ox.graph_to_gdfs(G, nodes=False, edges=True)
    edges_g.to_crs(CRS_WEB_MERCATOR).plot(
        ax=ax, color="#00e5ff" if i == 1 else "#ff9100",
        linewidth=0.4, alpha=0.7
    )
    boundary.to_crs(CRS_WEB_MERCATOR).plot(
        ax=ax, facecolor="none", edgecolor="white", linewidth=2
    )
    cx.add_basemap(ax, source=cx.providers.CartoDB.DarkMatter, zoom=13)
    ax.set_axis_off()
    ax.set_title(title, fontsize=14, fontweight="bold", color="white")

fig.tight_layout()
fig_path = FIGURES_DIR / "ch4_walk_vs_drive.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close(fig)
print(f"🖼  Walk vs Drive → {fig_path}")

# Save network data
edges_path = DATA_DIR / "road_edges.gpkg"
edges.to_file(edges_path, driver="GPKG")
print(f"\n💾 Road edges saved → {edges_path}")

print("\n✅ Chapter 4 complete.")
print("   You analysed: network stats, centrality hubs, road types.")
print("   Next → Chapter 5: The urban profile")
