
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
## CODE SECTION
! pip install rasterio

from google.colab import drive
drive.mount('/content/drive')

import rasterio
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
import cv2
from matplotlib import cm
import pandas as pd
import geopandas as gpd
from rasterio.plot import show
import seaborn as sns

# Path to image
path = (r'/content/drive/MyDrive/NEURAL NETWORK/data/DL_24.tif')

src  = rasterio.open(path)
im = src.read()

print(im.shape) # Channel, Row and Column

print(src.indexes)

src.count

# RGB PLOT

# 1. Slice by Band (Rasterio is Band-first: [Band, Row, Col])
# Note: Python is 0-indexed, so Band 4 is im[3], Band 3 is im[2], etc.
R = im[3, :, :]
G = im[2, :, :]
B = im[1, :, :]

rgb = np.dstack((R,G, B))

# 3. Plotting
plt.figure(figsize=(12, 10))
plt.imshow(rgb)
plt.axis('off')
plt.show()

# Training Samples
samples = gpd.read_file(r'/content/drive/MyDrive/NEURAL NETWORK/data/training_sampless/Dl_training.shp')
samples

print(samples.crs)

# New column to add class names
samples['label'] = samples['class'].replace({0:'Water', 1:'Bare', 2:'Vegetation', 3:'BuiltUp'})
samples

samples['label'].unique()

# Force the vector samples to match the raster's CRS
samples = samples.to_crs(src.crs)

cmap = ListedColormap(['brown', 'yellow', 'green', 'blue'])
fig, ax = plt.subplots(figsize=(12, 10))

# 1. Plot Vector Layer (Bottom Layer)
samples.plot(
    ax=ax,
    column='label',
    categorical=True,
    cmap=cmap,
    legend=True,
    legend_kwds={
        'bbox_to_anchor': (1.05, 1), # Places legend just outside the right edge
        'loc': 'upper left',
        'title': 'Land Cover'
    },

)

show(
    rgb.transpose(2, 0, 1),
    transform=src.transform,
    ax=ax,

)

ax.axis('off')
plt.tight_layout() # Adjusts layout to make room for the legend
plt.show()

# Value Extraction
samples['geometry']

array_samples = []
for point in samples['geometry']:
    x = point.xy[0][0]
    y = point.xy[1][0]

    row, col = src.index(x, y)

    band_values = []
    for i in range(src.count):
        band_values.append(src.read(i+1)[row, col])
    array_samples.append(band_values)

# List to array
X = np.array(array_samples)
X.shape

label_map = {
    1: 'B1', 2: 'B2', 3: 'B3', 4: 'B4',
    5: 'B5', 6: 'B6', 7: 'B7', 8: 'B8',
    9: 'B9', 10: 'B10', 11: 'B11', 12: 'B12'
}

dataset = pd.DataFrame(data=X, columns=[1,2,3,4,5,6,7,8,9,10,11,12])
dataset = dataset.rename(columns=label_map)

dataset['label'] = samples['class']
dataset

# Separating Spectral Data from the target
X = dataset.iloc[:, 0:-1].values
Y = dataset.iloc[:, -1].values

# Sklearn Function Importation
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.preprocessing import OneHotEncoder
from sklearn.neural_network import MLPClassifier

new_y = Y[:, np.newaxis]
new_y.shape

enc = OneHotEncoder()
enc.fit(new_y)
oneHotLabels = enc.transform(new_y).toarray()

oneHotLabels.shape

oneHotLabels

# Training Testing
x_train, x_test, y_train, y_test = train_test_split(X, oneHotLabels, test_size=0.2, random_state=42)

classifier = MLPClassifier(
    hidden_layer_sizes=(16, 32, 8),
    max_iter=300,
    activation='relu',
    verbose=10
)

classifier.fit(x_train,y_train)

# Prediction
y_pred = classifier.predict(x_test)

# Accuracy
accuracy_score(y_test, y_pred)

print(classification_report(y_test, y_pred))

# Predicting usage and Coverage map using the trained model
with rasterio.open(path) as src:
    im = src.read()

out_meta = src.meta.copy()

im = im.transpose([1,2,0])
X = np.nan_to_num(im)

"""Displaying Images: If you try to use plt.imshow(im) in Matplotlib with a (C, H, W) array, it will throw an error. Matplotlib requires the shape to be (H, W, C).
Saving Images: Libraries like OpenCV or Pillow also expect the color channels to be the last dimension.
Preprocessing: If you've just converted a PyTorch tensor back into a NumPy array, it will be in (C, H, W) format, and you must transpose it to view it or save it
"""

flatten_x = X.reshape(X.shape[0] * X.shape[1], X.shape[2])

pred = classifier.predict(flatten_x)
pred

classify = np.argmax(pred, axis=1)
classify = classify + 1
classify = classify.reshape(X.shape[0], X.shape[1])

cmap = ListedColormap(['blue', 'yellow', 'green', 'red'])

plt.figure(figsize=(10, 10))
plt.imshow(classify, cmap = cmap)
plt.axis('off')

export_image = classify[np.newaxis, :, :]

# export_image shape: (1, Rows, Cols)
out_meta.update({
    'driver': 'GTiff',             # REMOVE THE 'S' - MUST BE SINGULAR
    'height': export_image.shape[1],
    'width':  export_image.shape[2],
    'count':  1,
    'dtype':  export_image.dtype,  # Matches your classification array
    'compress': 'lzw',
    'crs': src.crs,                # Crucial for GIS alignment
    'transform': src.transform      # Crucial for GIS alignment
})

# Now save it
with rasterio.open('/content/drive/MyDrive/NEURAL NETWORK/LULC.tiff', "w", **out_meta) as dest:
    dest.write(export_image)

import joblib

# Define your save path
model_path = '/content/drive/MyDrive/NEURAL NETWORK/LULC_MODEL_SEN.pkl'

# Save the model
joblib.dump(classifier, model_path)
print(f"Model saved to {model_path}")

# =============================================================================
# LAND COVER CLASSIFICATION — APPLY SAVED MODEL TO A NEW IMAGE
# =============================================================================

import rasterio
import joblib
import numpy as np

# ----- FILE PATHS (edit these) -----
NEW_IMAGE_PATH = '/content/drive/MyDrive/NEURAL NETWORK/data/DL_WEIJA_20.tif'
MODEL_PATH     = '/content/drive/MyDrive/NEURAL NETWORK/LULC_MODEL_SEN.pkl'
OUTPUT_PATH    = '/content/drive/MyDrive/NEURAL NETWORK/data/LULC_PREDICTION.tif'

# STEP 1: Load the trained model
print("Loading model...")
classifier = joblib.load(MODEL_PATH)
print("Model loaded.\n")

# STEP 2: Open and read the new satellite image
with rasterio.open(NEW_IMAGE_PATH) as src:
    img = src.read()                          # shape: (bands, rows, cols)
    meta = src.meta.copy()
    bands, rows, cols = img.shape
    print(f"Image: {bands} bands, {rows} rows, {cols} cols")

    # Safety check: training used 12 bands
    assert bands == 12, f"Expected 12 bands, got {bands}. The new image must match the training image."

    # STEP 3: Reshape to (pixels, bands) — same as training
    img_2d = img.reshape(bands, -1).T         # shape: (n_pixels, 12)
    img_2d = np.nan_to_num(img_2d)            # replace NaN with 0 (as done during training)
    print(f"Pixels to classify: {img_2d.shape[0]:,}\n")

    # STEP 4: Predict — model returns ONE-HOT vectors (n_pixels, 4)
    print("Running prediction...")
    pred_onehot = classifier.predict(img_2d)  # shape: (n_pixels, 4)

    # STEP 5: Convert one-hot back to class integers
    # np.argmax gives 0-based index → add 1 to match your original classes (1,2,3,4)
    classified = np.argmax(pred_onehot, axis=1) + 1
    classified_map = classified.reshape(rows, cols)
    print(f"Unique classes: {np.unique(classified_map)}\n")

# STEP 6: Save as GeoTIFF
meta.update({
    'driver': 'GTiff',
    'dtype': 'int16',
    'count': 1,
    'compress': 'lzw'
})

with rasterio.open(OUTPUT_PATH, 'w', **meta) as dst:
    dst.write(classified_map.astype('int16')[np.newaxis, :, :])

print(f"Saved classified map → {OUTPUT_PATH}")

from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

# Define class colors and labels (must match your training classes)
cmap = ListedColormap(['blue', 'yellow', 'green', 'red'])
class_labels = ['Water', 'Bare', 'Vegetation', 'BuiltUp']

plt.figure(figsize=(12, 10))
img = plt.imshow(classified_map, cmap=cmap, vmin=1, vmax=4)

# Add legend
cbar = plt.colorbar(img, ticks=[1, 2, 3, 4], shrink=0.6)
cbar.ax.set_yticklabels(class_labels)
cbar.ax.set_ylabel('Land Cover Class')

plt.title('LULC Classification — New Image')
plt.axis('off')
plt.tight_layout()
plt.show()

import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

# Fix missing .shx file
os.environ['SHAPE_RESTORE_SHX'] = 'YES'

# ----- FILE PATHS -----
CLASSIFIED_PATH = '/content/drive/MyDrive/NEURAL NETWORK/data/LULC_PREDICTION.tif'
SHAPEFILE_PATH  = '/content/drive/MyDrive/NEURAL NETWORK/data/WEIJA_GWAWE.shp'

# 1. Load shapefile and reproject to match raster CRS
gdf = gpd.read_file(SHAPEFILE_PATH)

with rasterio.open(CLASSIFIED_PATH) as src:
    gdf = gdf.to_crs(src.crs)

    # 2. Clip raster to shapefile boundary
    clipped, clipped_transform = mask(src, gdf.geometry, crop=True, nodata=0)
    clipped = clipped[0]  # from (1, rows, cols) → (rows, cols)

# 3. Mask nodata pixels so they appear transparent
clipped_masked = np.ma.masked_where(clipped == 0, clipped)

# 4. Visualize
cmap = ListedColormap(['blue', 'yellow', 'green', 'red'])
class_labels = ['Water', 'Bare', 'Vegetation', 'BuiltUp']

fig, ax = plt.subplots(figsize=(12, 10), dpi=150)
img = ax.imshow(clipped_masked, cmap=cmap, vmin=1, vmax=4)

cbar = plt.colorbar(img, ax=ax, ticks=[1, 2, 3, 4], shrink=0.6)
cbar.ax.set_yticklabels(class_labels)
cbar.ax.set_ylabel('Land Cover Class')

ax.set_title('Clipped LULC Classification')
ax.axis('off')
plt.tight_layout()
plt.show()

import rasterio
import numpy as np

CLASSIFIED_PATH = '/content/drive/MyDrive/NEURAL NETWORK/data/LULC_PREDICTION.tif'

class_values = [1, 2, 3, 4]
class_labels = ['Water', 'Bare', 'Vegetation', 'BuiltUp']

with rasterio.open(CLASSIFIED_PATH) as src:
    classified_map = src.read(1)
    pixel_area_m2 = abs(src.transform[0]) * abs(src.transform[4])
    pixel_area_ha = pixel_area_m2 / 10_000

pixel_counts = [np.sum(classified_map == v) for v in class_values]
areas_ha = [count * pixel_area_ha for count in pixel_counts]

print(f"{'Class':<15} {'Pixels':>10} {'Area (ha)':>12}")
print("-" * 40)
for label, count, area in zip(class_labels, pixel_counts, areas_ha):
    print(f"{label:<15} {count:>10,} {area:>12,.2f}")
print("-" * 40)

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

CLASSIFIED_PATH = '/content/drive/MyDrive/NEURAL NETWORK/data/LULC_PREDICTION.tif'
REPROJECTED_PATH = '/content/drive/MyDrive/NEURAL NETWORK/data/LULC_PREDICTION_UTM30N.tif'

dst_crs = 'EPSG:32630'  # UTM Zone 30N

with rasterio.open(CLASSIFIED_PATH) as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )

    meta = src.meta.copy()
    meta.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height,
        'compress': 'lzw'
    })

    with rasterio.open(REPROJECTED_PATH, 'w', **meta) as dst:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest  # nearest for classification data
        )

print(f"Reprojected to UTM 30N → {REPROJECTED_PATH}")

# Verify
with rasterio.open(REPROJECTED_PATH) as src:
    print("CRS:", src.crs)
    print("Units: metres")
    print("Pixel size X:", abs(src.transform[0]), "m")
    print("Pixel size Y:", abs(src.transform[4]), "m")
print(f"{'TOTAL':<15} {sum(pixel_counts):>10,} {sum(areas_ha):>12,.2f}")

import rasterio

CLASSIFIED_PATH = '/content/drive/MyDrive/NEURAL NETWORK/data/LULC_PREDICTION.tif'

with rasterio.open(CLASSIFIED_PATH) as src:
    print("CRS:", src.crs)
    print("Units:", src.crs.linear_units if not src.crs.is_geographic else "degrees")
    print("Pixel size X:", abs(src.transform[0]))
    print("Pixel size Y:", abs(src.transform[4]))
    print("Bounds:", src.bounds)

import rasterio
import numpy as np

CLASSIFIED_PATH = '/content/drive/MyDrive/NEURAL NETWORK/data/LULC_PREDICTION_UTM30N.tif'

class_values = [1, 2, 3, 4]
class_labels = ['Water', 'Bare', 'Vegetation', 'BuiltUp']

with rasterio.open(CLASSIFIED_PATH) as src:
    classified_map = src.read(1)
    pixel_area_m2 = abs(src.transform[0]) * abs(src.transform[4])

pixel_area_km2 = pixel_area_m2 / 1_000_000

pixel_counts = [np.sum(classified_map == v) for v in class_values]
areas_km2 = [count * pixel_area_km2 for count in pixel_counts]

print(f"Pixel size: {pixel_area_m2**0.5:.2f} m  |  Pixel area: {pixel_area_m2:.2f} m²\n")
print(f"{'Class':<15} {'Pixels':>10} {'Area (km²)':>12}")
print("-" * 40)
for label, count, area in zip(class_labels, pixel_counts, areas_km2):
    print(f"{label:<15} {count:>10,} {area:>12,.4f}")
print("-" * 40)
print(f"{'TOTAL':<15} {sum(pixel_counts):>10,} {sum(areas_km2):>12,.4f}")

from matplotlib import pyplot as plt

class_colors = ['blue', 'yellow', 'green', 'red']

fig, ax = plt.subplots(figsize=(5, 3), dpi=150)
bars = ax.bar(class_labels, areas_km2, color=class_colors, edgecolor='black')


ax.set_xlabel('Land Cover Class', fontsize=13)
ax.set_ylabel('Area (km²)', fontsize=13)
ax.set_title('Land Cover Area Distribution', fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()
