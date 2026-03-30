
# Automated Aircraft Detection: Kotoka International Airport, Ghana
## Leveraging SamGeo & LangSAM for Visual Intelligence

## Project Overview
This project demonstrates the application of deep learning for **Object Detection** in high-resolution satellite imagery. By utilizing the **SamGeo** library and the **LangSAM** (Language-Segment Anything Model) framework, we successfully identified and segmented aircraft at the Kotoka International Airport in Accra, Ghana. 

Object detection at its core involves two distinct tasks:
1.  **Localization**: Identifying the spatial coordinates (position) of the object.
2.  **Classification**: Identifying what the object is (in this case, "Airplanes").

<p align="center">
  <img src="https://github.com/user-attachments/assets/0ddb8abc-c594-4b73-b6ed-f0e9c92dfc21" width="400" height="400" alt="Bounding Box Detection">
  <img src="https://github.com/user-attachments/assets/907a3c5f-c38f-4cd9-9f46-7203f5429f78" width="400" height="400" alt="Segmentation Mask">
  <br>
  <em>Figure 1: Comparison between Object Detection (left) and Instance Segmentation (right).</em>
</p>

---

## Technology Stack
*   **Segment Anything Model (SAM)**: A state-of-the-art foundation model for image segmentation.
*   **SamGeo**: A Python package designed to simplify the use of SAM for geospatial data.
*   **LangSAM**: A zero-shot object detection model that combines SAM with a language model (Grounding DINO), allowing for detection via natural language text prompts (e.g., "Airplanes").

---

## Methodology
The detection workflow followed an efficient 5-step pipeline:

1.  **Library Initialization**: Loading the SamGeo and LangSAM modules.
2.  **Imagery Acquisition**: Loading Google Satellite imagery of the Kotoka International Airport.
3.  **Model Configuration**: Initializing the LangSAM pre-trained weights.
4.  **Prompt Engineering**: Providing the text prompt `"Airplanes"` to the model.
5.  **Inferencing & Prediction**: The model scans the image, generates bounding boxes for potential matches, and applies a segmenting mask to refine the object boundaries.

---

## Real-World Applications
Automated aircraft detection from space has critical implications for aviation and logistics:
*   **Airport Security**: Monitoring unauthorized aircraft movement and ensuring perimeter integrity.
*   **Air Traffic Monitoring**: Providing real-time insights into airport ground operations and traffic density.
*   **Aircraft Analytics**: Tracking fleet composition and historical activity for market or strategic research.

---

## Technical Advisory
> [!IMPORTANT]
> **Model Generalization**: One limitation of using zero-shot pre-trained models like LangSAM is that their performance is heavily dependent on the quality and diversity of the original training data. While effective for general objects, specialized domains (e.g., rare aircraft models or low-resolution imagery) may require further **fine-tuning** on domain-specific datasets to maintain high precision.
