
# IMAGE SEGMENTATION with SAMGeo (GeoAI)

## Project Goal

The goal of this project is to segment an image showing the Sam Jonah Library, G-Block, and Lecture Theater (LT) at the University of Cape Coast, Ghana. Using advanced image segmentation techniques, we aim to accurately identify and separate these key landmarks from the satellite or aerial imagery.

---

## What is Image Segmentation?

Image segmentation is a powerful computer vision technique that divides satellite or aerial images into meaningful groups of pixels, called image segments. This process simplifies the image, making it easier to identify and analyze specific objects or features within the scene. Segmentation typically relies on characteristics such as size, texture, and shape to distinguish between different regions in an image.

---

## About SAMGeo

SAMGeo is a Python library designed to adapt Meta AI’s **Segment Anything Model (SAM)** specifically for remote sensing image segmentation and object detection. It is built on the architecture of **Vision Transformers (ViTs)**, which differ from traditional convolutional neural networks (CNNs) by using an attention mechanism.

This attention mechanism allows SAMGeo to concentrate on the most relevant parts of the image — such as buildings or landmarks — while effectively ignoring less important background details. This improves the quality and precision of the segmentation output.

---

## Key Feature: Zero-Shot Learning

One of the most impressive features of SAMGeo is its ability to perform segmentation on remote sensing images **without any additional training**. This zero-shot learning capability comes from leveraging pre-trained SAM models such as `vit_h`, `vit_l`, and `vit_b`.

These models are already familiar with segmenting a wide variety of images, enabling SAMGeo to achieve accurate segmentation results immediately, even on new, unseen remote sensing data.

---

## How This Project Works

1. A satellite or aerial image of the University of Cape Coast campus is provided as input.
2. The SAMGeo library is initialized with one of the available pre-trained SAM models.
3. The image is processed by SAMGeo, which segments it into meaningful regions that correspond to the Sam Jonah Library, G-Block, and Lecture Theater.
4. The resulting segmented image highlights these landmarks, making it easier for further analysis or visualization.

## Outpout
### Oringinal Satellit Image
![raw image](https://github.com/user-attachments/assets/9a721048-0a90-44fd-a5e2-8273ee73c4f7)

### Segmented Image
![segmented](https://github.com/user-attachments/assets/32aaf4d0-b315-4df0-ab91-298e0b976bbf)

