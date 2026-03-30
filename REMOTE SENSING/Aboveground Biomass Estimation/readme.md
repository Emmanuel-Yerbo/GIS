
# Aboveground Biomass Density (AGBD) Estimation: Kakum National Forest (2024)

## Project Overview
This project focuses on quantifying the **Aboveground Biomass Density (AGBD)** of the **Kakum National Forest**, a critical tropical ecosystem in Ghana. By integrating **NASA GEDI LiDAR** data with **ESA Sentinel satellite imagery**, we trained a regression model to estimate the total weight of vegetation (trees, branches, and leaves) across the forest landscape. 
<p align="center">
  <img src="https://github.com/user-attachments/assets/588849ce-bf7a-4794-a92c-5046dbbed22d" width="500" height = "400"alt="AGBD Estimation Map: Kakum National Forest">
  <br>
  <em>Figure 1: Predicted AGBD (Mg/ha) for Kakum National Forest (2024 Analysis)</em>
</p>


---

## What is Aboveground Biomass Density (AGBD)?
AGBD is a fundamental metric in ecology and climate science. It represents the total dry weight of all plant material above the soil, usually expressed in tons or megagrams per hectare (**Mg/ha**). Understanding AGBD is essential for:
*   **Carbon Stock Assessment**: Estimating how much atmospheric CO2 is stored in the forest.
*   **Ecosystem Productivity**: Monitoring the growth and health of mature tropical trees.
*   **Wildlife Conservation**: Identifying biomass-rich corridors that serve as vital habitats for local biodiversity.

---

## Data Sources & Technology
The study utilizes a multi-sensor fusion approach:
1.  **GEDI (Global Ecosystem Dynamics Investigation)**: A NASA spaceborne LiDAR mission that provides 3D forest structure data. We utilized the **GEDI L4A** product for direct biomass labels.
2.  **Sentinel-2 Imagery**: High-resolution optical data from the European Space Agency used to derive multispectral vegetation indices.

---

## Machine Learning Workflow
To predict AGBD accurately across the entire study area, a quantitative regression workflow was implemented:
1.  **Data Preparation**: Extracted biomass labels from GEDI points and multispectral features from Sentinel indices.
2.  **Feature Engineering**: Processing and normalizing satellite bands for model input.
3.  **Data Splitting**: Partitioning data into training and testing sets to ensure robust validation.
4.  **Model Training**: Implementing a regression algorithm to learn the relationship between spectral signatures and biomass.
5.  **Performance Evaluation**: Statistically validating the model's accuracy.
6.  **Spatial Prediction**: Applying the trained model to generate the final AGBD map for the entire 2024 study area.

---

## Results & Interpretation
The resulting map illustrates a highly productive forest environment:
*   **Peak Biomass (~585.84 Mg/ha):** Concentrated in the dark green areas, these values indicate healthy, mature tropical forest cores with high carbon storage capacity.
*   **Lower Biomass (~19.25 Mg/ha):** Found in light green or peripheral areas, these values represent young regrowth, grassland transitions, or zones affected by recent deforestation.

> [!NOTE]
> **Technical Advisory:** While GEDI is a powerful tool for global estimation, localized biases can occur when applied to smaller urban or regional reserves like Kakum. Accuracy was maintained through rigorous ground-truthing and spectral index correlation.
