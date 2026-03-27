
# 🌍 Land Use Land Cover (LULC) Classification using Neural Networks

## ✨ Project Overview

This project provides an automated solution for classifying satellite images into different land cover types, such as Water, Vegetation, Bare Land, and Built-up areas. By leveraging the power of Artificial Intelligence (specifically, Neural Networks), we can quickly and accurately understand how land is being used across a given region. This information is crucial for urban planning, environmental monitoring, agriculture, and disaster management.

## 🎯 Project Goal

The primary goal of this project is to develop and demonstrate a robust system for Land Use Land Cover (LULC) mapping from satellite imagery. It aims to:

*   **Automate Classification**: Reduce the manual effort required to create LULC maps.
*   **Provide Insights**: Generate clear, understandable maps and statistics about land cover distribution.
*   **Support Decision-Making**: Offer valuable data for various applications, from environmental protection to urban development.
*   Study Area
<img width="950" height="645" alt="image" src="https://github.com/user-attachments/assets/8863f8fc-92e8-4dbf-b6a3-d15baa43a7de" />


## 🚀 How It Works (Simplified)

Imagine teaching a computer to recognize different objects in a picture. That's essentially what this project does, but for satellite images and land cover types.

1.  **Input Data**: We start with high-resolution satellite images that capture various details about the Earth's surface. We also use a small set of "training examples" – specific points on the map where we already know the land cover type (e.g., this spot is definitely water, that spot is vegetation).\
<img width="1193" height="686" alt="image" src="https://github.com/user-attachments/assets/5b71bf2f-00da-4409-85ad-4a81dcbbe53c" />


3.  **Learning Phase**: The computer (our Neural Network model) studies these training examples. It learns the unique patterns and characteristics (like color, brightness, and texture) associated with each land cover type.

4.  **Classification Phase**: Once trained, the model can then look at an entirely new satellite image, pixel by pixel, and classify each one based on the patterns it learned. It's like applying a digital label to every part of the map.

5.  **Output**: The result is a color-coded map where each color represents a different land cover type, making it easy to visualize the landscape. We also generate statistical reports showing the total area covered by each type.
6.  Trained Model
   
   <img width="794" height="540" alt="image" src="https://github.com/user-attachments/assets/b35afcfd-0d6b-4518-aa29-9c10d57f81ba" />  

## 🌟 Key Features

*   **Automated LULC Mapping**: Generate detailed land cover maps with minimal human intervention.
*   **Neural Network Powered**: Utilizes a Multi-layer Perceptron (MLP) for accurate classification.
*   **Visual Output**: Produces intuitive, color-coded land cover maps.
*   **Area Statistics**: Calculates and reports the area (in square kilometers) for each land cover class.
*   **Geospatial Compatibility**: Integrates with standard geographic data formats (GeoTIFF, Shapefiles).
*   **Flexible Application**: The trained model can be easily applied to new satellite images of different regions.

## 📊 Results and Visualizations

The project delivers clear, actionable insights through various outputs:

*   **Classified LULC Maps**: Visual representations of the land cover types across the analyzed area.
<img width="800" height="600" alt="image" src="https://github.com/user-attachments/assets/292a23c8-5031-4e51-91df-5e97572cfaf7" />


*   **Clipped LULC Maps**: Focused views of the classification within specific areas of interest (e.g., administrative boundaries).
<img width="800" height="600" alt="image" src="https://github.com/user-attachments/assets/d1591a31-1a12-42ef-85a7-8a8a7cb6d927" />


*   **Land Cover Area Distribution**: Bar charts and tables summarizing the total area occupied by each land cover class, providing quantitative insights into the landscape.
    <img width="800" height="600" alt="image" src="https://github.com/user-attachments/assets/ea7e1451-c359-4931-a274-6b4df2a37d70" />


## 🛠️ Technologies Used

This project is built using popular Python libraries for data science and geospatial analysis:

*   **Python**: The core programming language.
*   **`rasterio`**: For reading, writing, and manipulating raster (satellite) data.
*   **`numpy`**: For numerical operations, especially with large datasets.
*   **`pandas`**: For data manipulation and analysis.
*   **`scikit-learn`**: Provides the Neural Network model for classification.
*   **`geopandas`**: For working with vector (shapefile) data and integrating it with raster data.
*   **`matplotlib` & `seaborn`**: For creating visualizations and plots.

---
