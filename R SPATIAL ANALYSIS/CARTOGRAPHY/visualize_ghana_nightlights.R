# ==============================================================================
# Programmatic & Styled VIIRS Nighttime Lights Map of Ghana
# ==============================================================================
# This script downloads Ghana's boundaries, retrieves the NASA Black Marble VIIRS
# annual nighttime lights dataset programmatically, and styles it into a premium map.
# 
# Prerequisites: 
# Fix Windows PROJ database conflict (e.g. from PostgreSQL/PostGIS) 
# by forcing PROJ to use sf package's bundled database path
Sys.setenv(PROJ_LIB = system.file("proj", package = "sf"))

library(sf)
library(terra)
library(tidyverse)
library(tidyterra)
library(geodata)
library(blackmarbler)

# Set working directory to the project directory to resolve relative paths
if (dir.exists("c:/YERBO/Desktop/CODING/R BASICS")) {
  setwd("c:/YERBO/Desktop/CODING/R BASICS")
}

# ------------------------------------------------------------------------------
# 1. Configuration & Folders
# ------------------------------------------------------------------------------
dir.create("data", showWarnings = FALSE)
dir.create("output", showWarnings = FALSE)

# ------------------------------------------------------------------------------
# 2. Get Administrative Boundary for Ghana
# ------------------------------------------------------------------------------
message("1. Fetching Ghana administrative boundary...")
ghana_vector <- gadm(country = "GHA", level = 0, path = "data", version = "latest") %>%
  st_as_sf()

# ------------------------------------------------------------------------------
# 3. Retrieve VIIRS Nightlight Data (Programmatic vs Local)
# ------------------------------------------------------------------------------
# Choose your download method: TRUE = download programmatically, FALSE = load local file
DOWNLOAD_PROGRAMMATICALLY <- FALSE 

if (DOWNLOAD_PROGRAMMATICALLY) {
  # FIX: Bypasses Windows SSL verification issues when communicating with NASA servers
  library(httr)
  set_config(config(ssl_verifypeer = 0L))
  
  # Pre-filled NASA Earthdata Bearer Token (generated on 2026-06-27)
  bearer_token <- "eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImVtbWFudWVseWVyYm8iLCJleHAiOjE3ODc3MTE3MjksImlhdCI6MTc4MjUyNzcyOSwiaXNzIjoiaHR0cHM6Ly91cnMuZWFydGhkYXRhLm5hc2EuZ292IiwiaWRlbnRpdHlfcHJvdmlkZXIiOiJlZGxfb3BzIiwiYWNyIjoiZWRsIiwiYXNzdXJhbmNlX2xldmVsIjozfQ.mVHbkgcm9Nmpt58OvWQ0qbeVAYJ4kT74097J4L2HCAkgJZi93-k_ZbVx4MHjfgHUOhCTR36kkjvLk_jSVBS-ZODrw_yn4qj8s-syMV7VC-NN-Ympmumd2vNFm6osVO8ZPLgo53CHt7W4z2C4F6UZJ8717Vx6QmtsuIE3Rf7JmFxeAxSM79KYTG-msZeFrhyiRTcJwNlCZkgbzWolu42GRUKLGQTFRm2mUM_iJmERJpyPQJzs7brYPVf9HAx5SMIcNlAX8rk9RrXJnTDTwcraAT2bycdYF8ENF8PVePztxHB6b6X2vMJsLNPbfmnE8ErIA3-GxdXxueNjwGeJHvVLNA"
  
  if (nchar(bearer_token) == 0 || grepl("YOUR_TOKEN", bearer_token)) {
    stop("Error: A valid NASA Bearer Token is required for programmatic download.")
  }
  
  message("\nDownloading & processing VIIRS VNP46A4 Annual Composite for 2023...")
  # bm_raster handles tile checking, downloading, mosaicing, and cropping to Ghana
  viirs_raw <- bm_raster(
    roi_sf = ghana_vector,
    product_id = "VNP46A4",
    date = 2023,
    bearer = bearer_token
  )
  
  # Save the downloaded crop locally to avoid redownloading next time
  writeRaster(viirs_raw, "data/ghana_viirs_2023.tif", overwrite = TRUE)
  message("Downloaded raster saved to 'data/ghana_viirs_2023.tif'")
  
} else {
  # Local fallback (using the GEE-downloaded raster)
  viirs_raster_path <- "data/ghana_viirs_2023.tif"
  if (!file.exists(viirs_raster_path)) {
    stop(paste("File not found at:", viirs_raster_path, "\nPlease save your GEE-downloaded TIFF to this path."))
  }
  message("Loading local VIIRS raster from Google Earth Engine...")
  viirs_raw <- rast(viirs_raster_path)
}

# ------------------------------------------------------------------------------
# 4. Processing & Transform
# ------------------------------------------------------------------------------
message("\n2. Processing data...")
# Align Coordinate Reference Systems
ghana_projected <- st_transform(ghana_vector, crs(viirs_raw))

# Mask the cropped raster to the exact boundaries of Ghana
viirs_masked <- mask(viirs_raw, vect(ghana_projected))

# Clamp negative radiance values (background sensor noise) to 0
viirs_clamped <- clamp(viirs_masked, lower = 0)

# Apply log1p transformation to bring out subtle rural networks and small towns
viirs_log <- log1p(viirs_clamped)

# ------------------------------------------------------------------------------
# 5. Styling and Plotting (ggplot2)
# ------------------------------------------------------------------------------
message("3. Generating the map layout...")

# Premium NASA-style night-glow palette
nightlights_palette <- c(
  "#06060c", # Dark space background (no light)
  "#140e2d", # Faint purple-blue halo (very low light)
  "#391b6f", # Deep violet (low-medium light)
  "#a84200", # Copper orange (medium light)
  "#d87e00", # Warm amber (medium-high light)
  "#f1c40f", # Golden yellow (high light)
  "#ffffff"  # Electric white (intense urban centers)
)

p <- ggplot() +
  # Draw a subtle background for the entire landmass of Ghana to anchor the map
  geom_sf(
    data = ghana_projected,
    fill = "#0d0d18",
    color = "#1d1d2f",
    linewidth = 0.25
  ) +
  
  # Plot the VIIRS raster using tidyterra
  geom_spatraster(data = viirs_log) +
  
  # Apply gradient scale
  scale_fill_gradientn(
    colors = nightlights_palette,
    na.value = "transparent",
    name = "Luminosity Index (Log Scale)"
  ) +
  
  coord_sf(expand = FALSE) +
  
  # Theme Overrides for dark background styling
  theme_void() +
  theme(
    panel.background = element_rect(fill = "#06060c", color = NA),
    plot.background = element_rect(fill = "#06060c", color = NA),
    legend.position = "bottom",
    legend.title = element_text(color = "gray80", size = 8.5, face = "bold"),
    legend.text = element_text(color = "gray60", size = 7.5),
    legend.key.width = unit(1.8, "cm"),
    legend.key.height = unit(0.25, "cm"),
    plot.title = element_text(
      color = "#ffffff", 
      size = 18, 
      face = "bold", 
      hjust = 0.5, 
      margin = margin(t = 25, b = 5)
    ),
    plot.subtitle = element_text(
      color = "gray75", 
      size = 10, 
      hjust = 0.5, 
      margin = margin(b = 20)
    ),
    plot.caption = element_text(
      color = "gray45", 
      size = 7, 
      hjust = 0.5, 
      margin = margin(t = 15, b = 20)
    )
  ) +
  
  # Titles & Captions
  labs(
    title = "GHANA AT NIGHT",
    subtitle = "Infrastructure corridors & urban settlement patterns observed via VIIRS satellite sensors",
    caption = "Data: NASA Black Marble VIIRS DNB (2023) | Cartography: R + ggplot2 + terra + blackmarbler"
  )

# ------------------------------------------------------------------------------
# 6. Save Visualization (High Resolution)
# ------------------------------------------------------------------------------
output_file <- "output/ghana_nightlights_map.png"
message(paste("\n4. Saving final map to", output_file))

ggsave(
  filename = output_file,
  plot = p,
  width = 8.5,
  height = 11,
  dpi = 400,
  bg = "#06060c"
)

# Print the plot to the interactive RStudio Plots pane
print(p)

# ------------------------------------------------------------------------------
# 7. Interactive Leaflet OSM Map Overlay (Viewer Pane)
# ------------------------------------------------------------------------------
message("\n5. Building interactive Leaflet map with OSM/Dark Matter basemaps...")
library(leaflet)
library(raster)

# Reproject raster to WGS84 for Leaflet compatibility
# If standard projection fails due to system PROJ conflicts, fallback to assigning WGS84 manually (GEE default)
viirs_wgs84 <- tryCatch({
  project(viirs_log, "EPSG:4326")
}, error = function(e) {
  warning("Projection failed due to PROJ database conflict. Falling back to manual CRS assignment.")
  r_temp <- viirs_log
  crs(r_temp) <- "EPSG:4326"
  r_temp
})

# Convert to standard Raster class for universal Leaflet compatibility
viirs_legacy <- raster::raster(viirs_wgs84)

# Create a matching color palette (violet-to-gold-to-white)
pal <- colorNumeric(
  palette = c("#140e2d", "#5b2c6f", "#d35400", "#f1c40f", "#ffffff"),
  domain = values(viirs_legacy),
  na.color = "transparent"
)

# Build the interactive leaflet map
interactive_map <- leaflet() %>%
  # Base Map Layers
  addProviderTiles(providers$CartoDB.DarkMatter, group = "Dark Matter (OSM)") %>%
  addTiles(group = "OpenStreetMap (Standard)") %>%
  addProviderTiles(providers$Esri.WorldImagery, group = "Satellite Imagery") %>%
  
  # Nightlights Layer
  addRasterImage(
    viirs_legacy,
    colors = pal,
    opacity = 0.7,
    group = "VIIRS Nightlights 2023",
    project = FALSE
  ) %>%
  
  # Legend
  addLegend(
    pal = pal,
    values = values(viirs_legacy),
    title = "Luminosity (Log)",
    position = "bottomright",
    group = "VIIRS Nightlights 2023"
  ) %>%
  
  # Interactive layer controllers
  addLayersControl(
    baseGroups = c("Dark Matter (OSM)", "OpenStreetMap (Standard)", "Satellite Imagery"),
    overlayGroups = c("VIIRS Nightlights 2023"),
    options = layersControlOptions(collapsed = FALSE)
  )

# Display the interactive map in the RStudio Viewer pane
print(interactive_map)

message("\nSuccess! Both the static map (Plots pane) and interactive OSM map (Viewer pane) are ready.")
