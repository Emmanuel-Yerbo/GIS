"""
=============================================================================
CONFIGURATION — Python for Urban Analysis (Ghana Edition)
=============================================================================
Central config for every chapter. Change STUDY_AREA to point the entire
pipeline at a different city, district, or region on Earth.

Author  : Prof. Geospatial Data Science (Mentorship Framework)
Focus   : Greater Accra Metropolitan Area, Ghana
=============================================================================
"""

import os
from pathlib import Path

# ── Project paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
DATA_DIR     = PROJECT_ROOT / "data"
OUTPUT_DIR   = PROJECT_ROOT / "outputs"
FIGURES_DIR  = OUTPUT_DIR / "figures"

for d in [DATA_DIR, OUTPUT_DIR, FIGURES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Study area ─────────────────────────────────────────────────────────────
# The *single* variable you change to re-target the whole pipeline.
# For OSMnx, this must match an OpenStreetMap Nominatim place name.

STUDY_AREA = "Accra, Ghana"                       # City-level study
STUDY_REGION = "Greater Accra Region, Ghana"       # Region-level (Ch 6)

# ── Greater Accra MMDAs (29 districts — analogous to Vienna's 23 Bezirke) ─
GREATER_ACCRA_DISTRICTS = [
    "Accra Metropolitan District, Greater Accra, Ghana",
    "Tema Metropolitan District, Greater Accra, Ghana",
    "Ablekuma Central Municipal District, Greater Accra, Ghana",
    "Ablekuma North Municipal District, Greater Accra, Ghana",
    "Ablekuma West Municipal District, Greater Accra, Ghana",
    "Adenta Municipal District, Greater Accra, Ghana",
    "Ashaiman Municipal District, Greater Accra, Ghana",
    "Ayawaso Central Municipal District, Greater Accra, Ghana",
    "Ayawaso East Municipal District, Greater Accra, Ghana",
    "Ayawaso North Municipal District, Greater Accra, Ghana",
    "Ayawaso West Municipal District, Greater Accra, Ghana",
    "Ga South Municipal District, Greater Accra, Ghana",
    "Ga Central Municipal District, Greater Accra, Ghana",
    "Ga East Municipal District, Greater Accra, Ghana",
    "Ga North Municipal District, Greater Accra, Ghana",
    "Ga West Municipal District, Greater Accra, Ghana",
    "Korle Klottey Municipal District, Greater Accra, Ghana",
    "Kpone Katamanso Municipal District, Greater Accra, Ghana",
    "Krowor Municipal District, Greater Accra, Ghana",
    "La Dade-Kotopon Municipal District, Greater Accra, Ghana",
    "La-Nkwantanang-Madina Municipal District, Greater Accra, Ghana",
    "Ledzokuku Municipal District, Greater Accra, Ghana",
    "Okaikwei North Municipal District, Greater Accra, Ghana",
    "Tema West Municipal District, Greater Accra, Ghana",
    "Weija-Gbawe Municipal District, Greater Accra, Ghana",
    "Ada East District, Greater Accra, Ghana",
    "Ada West District, Greater Accra, Ghana",
    "Ningo-Prampram District, Greater Accra, Ghana",
    "Shai-Osudoku District, Greater Accra, Ghana",
]

# ── CRS (Coordinate Reference Systems) ────────────────────────────────────
CRS_WGS84       = "EPSG:4326"   # Lat/lon — storage & OSM default
CRS_WEB_MERCATOR = "EPSG:3857"  # Web tiles (contextily)
CRS_GHANA_METRE  = "EPSG:25000" # Ghana National Grid (metre-based)
# Fallback UTM zone for Accra (Zone 30N)
CRS_UTM_ACCRA    = "EPSG:32630"

# ── Visualisation defaults ─────────────────────────────────────────────────
FIGURE_DPI     = 150
DARK_BG        = "#0e1117"
EDGE_COLOR     = "#2a2a2a"
ACCENT_CMAP    = "YlOrRd"        # Yellow-Orange-Red  (buildings, density)
ROAD_CMAP      = "viridis"       # Road betweenness
AMENITY_COLOR  = "#00e5ff"       # Cyan accent for POI markers

# ── OSM tag dictionaries ──────────────────────────────────────────────────
AMENITY_TAGS = {
    "amenity": [
        "hospital", "clinic", "pharmacy",
        "school", "university", "library",
        "marketplace", "bank", "atm",
        "police", "fire_station",
        "place_of_worship", "restaurant", "fuel",
    ]
}

BUILDING_TAGS = {"building": True}

LEISURE_TAGS = {
    "leisure": ["park", "playground", "sports_centre", "garden", "stadium"]
}

print(f"[config] Study area  → {STUDY_AREA}")
print(f"[config] Data dir    → {DATA_DIR}")
print(f"[config] Output dir  → {OUTPUT_DIR}")
