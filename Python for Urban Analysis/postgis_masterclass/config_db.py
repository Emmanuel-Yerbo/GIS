"""
=============================================================================
CENTRAL DATABASE CONFIGURATION & HELPER — PostGIS for Urban Analysis (Ghana)
=============================================================================
Central configuration and database connection engine for all PostGIS masterclass
chapters. Provides utility functions for executing Spatial SQL, retrieving
GeoPandas DataFrames, and rendering interactive Leaflet / Folium maps directly
inside Jupyter Notebooks.

Author  : Prof. Geospatial Data Science & Spatial Database Administration
Focus   : Greater Accra Metropolitan Area (GAMA), Ghana
=============================================================================
"""

import os
from pathlib import Path
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text

# ── 1. Database Connection Parameters ──────────────────────────────────────
# Default local PostgreSQL / PostGIS connection parameters.
# Modify these environment variables or defaults to match your local pgAdmin setup.
DB_USER     = os.getenv("POSTGIS_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGIS_PASSWORD", "postgres")
DB_HOST     = os.getenv("POSTGIS_HOST", "localhost")
DB_PORT     = os.getenv("POSTGIS_PORT", "5432")
DB_NAME     = os.getenv("POSTGIS_DB", "urban_analytics_ghana")

# SQLAlchemy Connection URI
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── 2. Coordinate Reference Systems (Ghana Standards) ──────────────────────
CRS_WGS84            = "EPSG:4326"   # Global Geodetic GPS
CRS_UTM_ACCRA        = "EPSG:32630"  # National Metric Standard (UTM Zone 30N)
CRS_GHANA_GRID       = "EPSG:2136"   # Historical Cadastral (Ghana War Office / Leigon)
CRS_WEB_MERCATOR     = "EPSG:3857"   # Web Tile Mapping

# ── 3. Study Area Bounding Envelopes (UTM Zone 30N in Meters) ──────────────
ACCRA_METRO_CENTER = {"lat": 5.6037, "lon": -0.1870} # WGS84 Center
ACCRA_UTM_ENVELOPE = {
    "xmin": 790000,
    "ymin": 605000,
    "xmax": 840000,
    "ymax": 635000
}

# ── 4. Database Helper Functions ───────────────────────────────────────────
_engine = None

def get_engine():
    """Returns a singleton SQLAlchemy engine instance."""
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine

def execute_sql(sql_query, params=None):
    """
    Executes a DDL or DML SQL query (CREATE, UPDATE, INSERT, ALTER)
    and commits changes.
    """
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(sql_query), params or {})
    return result

def query_df(sql_query, params=None):
    """
    Executes a standard SELECT query and returns a pandas DataFrame.
    """
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text(sql_query), conn, params=params)
    return df

def query_gdf(sql_query, geom_col="geom", crs=32630, params=None):
    """
    Executes a Spatial SELECT query and returns a GeoPandas GeoDataFrame.
    Automatically formats the geometry column.
    """
    engine = get_engine()
    with engine.connect() as conn:
        gdf = gpd.read_postgis(text(sql_query), conn, geom_col=geom_col, crs=crs, params=params)
    return gdf

def preview_map(gdf, tooltip_cols=None, popup_cols=None, tiles="OpenStreetMap", zoom_start=12):
    """
    Generates an interactive Folium / Leaflet map preview for a GeoDataFrame.
    Automatically reprojects to EPSG:4326 for web viewing.
    """
    if gdf.empty:
        print("[WARNING] GeoDataFrame is empty. Nothing to map.")
        return None
    
    # Reproject to WGS84 for Folium
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    
    return gdf_wgs84.explore(
        column=tooltip_cols[0] if tooltip_cols and tooltip_cols[0] in gdf_wgs84.columns else None,
        tooltip=tooltip_cols,
        popup=popup_cols,
        tiles=tiles,
        zoom_start=zoom_start,
        style_kwds={"fillOpacity": 0.6, "weight": 2}
    )

if __name__ == "__main__":
    print("=" * 65)
    print("  PostGIS Masterclass Database Configuration")
    print(f"  Target URI: postgresql://{DB_USER}:****@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"  Default Metric CRS: {CRS_UTM_ACCRA}")
    print("=" * 65)
