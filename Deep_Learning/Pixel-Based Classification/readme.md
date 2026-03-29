
# 🌍 Pixel-Based Land Use Land Cover (LULC) Classification using Neural Networks
## Pixel-Based Classification
Referes to assigning a thematic label (such as "water," "forest," or "urban") to each individual pixel in a satellite image of a given place.

## ✨ Project Overview

This project provides an automated solution for classifying satellite images into different land cover types, such as Water, Vegetation, Bare Land, and Built-up areas. By leveraging the power of Artificial Intelligence (specifically, Neural Networks), we can quickly and accurately understand how land is being used across a given region. This information is crucial for urban planning, environmental monitoring, agriculture, and disaster management.

## 🎯 Project Goal

The primary goal of this project is to develop a neural network that will be used for pixel-based land cover classification. It aims to:

*   **Automate Classification**: Reduce the manual effort required to create LULC maps.
*   **Understand the use of the land within the area of interest.** 
<img width="950" height="645" alt="image" src="https://github.com/user-attachments/assets/8863f8fc-92e8-4dbf-b6a3-d15baa43a7de" />


## 🚀 How It Works (Simplified)

Imagine teaching a computer to recognize different objects in a picture. That's essentially what this project does, but for satellite images and land cover types.

1.  **Input Data**: We start with high-resolution satellite image of the area of interest that capture various details about the Earth's surface. We also use a small set of "training examples" – specific points on the map where we already know the land cover type (e.g., this spot is definitely water, that spot is vegetation).\
<img width="1193" height="686" alt="image" src="https://github.com/user-attachments/assets/5b71bf2f-00da-4409-85ad-4a81dcbbe53c" />


3.  **Learning Phase**: The computer (our Neural Network model) studies these training examples. It learns the unique patterns and characteristics (like color, brightness, and texture) associated with each land cover type.

4.  **Classification Phase**: Once trained, the model can then look at an entirely new satellite image, pixel by pixel, and classify each one based on the patterns it learned. It's like applying a digital label to every part of the map.

5.  **Output**: The result is a color-coded map where each color represents a different land cover type, making it easy to visualize the landscape. We also generate statistical reports showing the total area covered by each type.
  <img width="794" height="540" alt="image" src="https://github.com/user-attachments/assets/b35afcfd-0d6b-4518-aa29-9c10d57f81ba" />  


## 📊 Results and Visualizations

The project delivers clear, actionable insights through various outputs:

*   **Classified LULC Maps**: Visual representations of the land cover types across the analyzed area.
<img width="800" height="600" alt="image" src="https://github.com/user-attachments/assets/292a23c8-5031-4e51-91df-5e97572cfaf7" />



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
