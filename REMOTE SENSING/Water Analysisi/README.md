# Ghana’s River System – HydroRIVERS Analysis

This project explores Ghana’s river networks using the HydroRIVERS dataset
, which is derived from the HydroSHEDS database. HydroSHEDS provides high-resolution hydrographic data globally, based on the SRTM (Shuttle Radar Topography Mission) digital elevation model (DEM).

The main objective is to visualize Ghana’s river systems with a visual hierarchy of streams and rivers, highlighting the dominance of the Volta River system and its catchment.

## Dataset Overview

Source: HydroRIVERS (part of HydroSHEDS)

Format: Vector line layer (river reaches)

Extraction Method: Based on flow accumulation & discharge thresholds

## Key Attribute Used

UPLAND_SKM (Upland in square kilometers):
Represents the cumulative watershed area draining into each river segment (reach).

Larger values = river segments with large upstream catchments (main rivers).

Smaller values = tributaries and streams with localized catchments.

## Methodology

1. Data Acquisition: Downloaded HydroRIVERS data for Africa.

2. Extracted Ghana subset by clipping country boundaries.

3. Attribute Mapping

4. Created a width attribute from UPLAND_SKM.

Mapped UPLAND_SKM → river line width to represent catchment influence.

Wide lines = major rivers (large catchments).

Thin lines = tributaries (small catchments).

## Visualization

The final map illustrates the hierarchical river system of Ghana.
Clearly shows the Volta River system as the largest and most dominant catchment in the country.

## Results
![1751914948717](https://github.com/user-attachments/assets/98a0467f-d917-4418-885f-264731c58d26)


The Volta River Basin emerges as the largest catchment area in Ghana.

Smaller river systems (e.g., Pra, Ankobra, Tano, Densu, White Volta tributaries) are visualized with thinner streamlines.
