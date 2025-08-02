# Flood Prediction Using U-Net Model: Akosombo Dam Spillage 2023

This project aims to leverage deep learning for accurate flood area prediction by applying a U-Net convolutional neural network to satellite or aerial flood imagery. The case study focuses on the **Akosombo Dam spillage event in Ghana (2023)**, demonstrating how AI can support disaster management and response efforts.

---

## Project Overview

Floods are among the most devastating natural disasters worldwide, causing significant loss of life and property. Accurate and timely mapping of flooded areas is critical for effective emergency response and resource allocation. This project uses a deep learning approach to automatically segment flooded regions from images, which can significantly speed up flood assessment compared to manual methods.

---

## Dataset and Preprocessing

### Dataset Source
- The project uses the **Flood Segmentation Dataset** available on Kaggle, which contains labeled flood images and corresponding ground truth masks indicating flooded vs. non-flooded areas.
- This dataset provides diverse flood scenarios crucial for training a robust model capable of generalizing to new flood events.

### Data Preprocessing
- Images were normalized and resized to a consistent dimension to ensure uniformity during training.
- Data augmentation techniques such as rotations, flips, and brightness adjustments were applied to increase dataset variability and reduce overfitting.
- The dataset was split into **training (70%)** and **testing (30%)** sets to evaluate model performance on unseen data.

---

## Model Architecture: U-Net

### What is U-Net?
- The **U-Net** model is a powerful convolutional neural network architecture specifically designed for image segmentation tasks.
- It follows an **encoder-decoder framework**:
  - **Encoder (Contracting Path):** Successive convolutional layers and max-pooling operations downsample the image, extracting hierarchical features that capture the context and semantics of the input.
  - **Decoder (Expanding Path):** Upsampling layers gradually restore the spatial resolution to generate a pixel-wise classification output (segmentation map).

### Key Features in This Implementation
- **Skip Connections:** U-Net’s hallmark feature, skip connections transfer feature maps from the encoder layers directly to the corresponding decoder layers. This preserves spatial information and helps in reconstructing fine details such as flood boundaries.
- **Dropout Layers:** Incorporated to randomly deactivate neurons during training, reducing overfitting and improving the model’s ability to generalize to new images.
- **Loss Function and Metrics:**
  - The model was trained using a binary segmentation loss function.
  - **Intersection Over Union (IoU)** was used as the primary evaluation metric, measuring the overlap between predicted and actual flooded regions.
  - IoU is particularly effective for segmentation tasks as it penalizes both false positives and false negatives.

---

## Model Training and Performance

After extensive training on the Kaggle flood segmentation dataset:

- **Test Accuracy: 87%**  
  This indicates that 87% of the pixels predicted as flooded or non-flooded matched the ground truth in the test set.

- **Intersection Over Union (IoU): 72%**  
  A 72% IoU score reflects a strong agreement between predicted flood masks and actual flood extents, confirming the model’s accuracy in delineating flood boundaries.

- **Test Loss: 30%**  
  The loss value indicates some prediction error but is within an acceptable range for this type of task, especially considering the variability and complexity of flood images.

---

## Testing on Akosombo Dam Spillage 2023 Images

To evaluate the model’s real-world applicability, three satellite images of the **Akosombo Dam spillage in Ghana (2023)** were sourced from public repositories.

- The images were preprocessed similarly to the training data.
- The trained U-Net model was used to generate flood segmentation masks for each image.
- The results demonstrated the model’s ability to generalize beyond the original dataset and accurately identify flooded zones in new, unseen images.

---

## Explainability with Grad-CAM

Deep learning models, especially convolutional neural networks, are often considered “black boxes” because their decision-making process is not easily interpretable.

To enhance trust and interpretability:

- **Gradient-weighted Class Activation Mapping (Grad-CAM)** was applied.
- Grad-CAM produces **heatmaps** that highlight regions of the input image most influential in the model’s prediction.
- In the heatmaps, **red areas signify the regions the model focused on** to identify flooded zones.
- This explainable AI (XAI) technique helps validate that the model is using relevant flood features rather than irrelevant background information, increasing confidence in predictions.

---
## Output: Model Training
<img width="1166" height="1190" alt="akosombo" src="https://github.com/user-attachments/assets/a1e41021-1510-4386-932f-7758f3b13e57" />

## Output: Akosombo Spillage
<img width="1166" height="1190" alt="akosomb" src="https://github.com/user-attachments/assets/07d24c7b-013f-4850-946a-31f0789650a7" />


## Tools and Frameworks Used

- **TensorFlow:** For building and training the U-Net deep learning model.
- **Keras API:** Simplified model construction and experimentation.
- **OpenCV & NumPy:** For image preprocessing and manipulation.
- **Matplotlib:** Visualization of results and Grad-CAM heatmaps.

---

## Acknowledgements

Special thanks to **Courage Kamusoko** for invaluable guidance and support throughout this project.

---

## Useful Resources

- [Flood Segmentation Dataset Tutorial](https://lnkd.in/ePB972CT) — Comprehensive guide on dataset acquisition and preparation.
- [Flood Mapping Tutorial](https://lnkd.in/eSeKixjX) — Detailed walkthrough on flood segmentation using U-Net.

---

## Future Work

- Improve model accuracy by experimenting with advanced architectures like Attention U-Net or transformers.
- Incorporate multi-spectral satellite imagery to enhance flood detection in challenging conditions.
- Develop a web interface or API for real-time flood segmentation and visualization.
- Collaborate with disaster management agencies to deploy this tool in operational settings.

---
