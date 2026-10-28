# 🌱 Precision Agriculture & Crop Health Classification (1D-CNN)

> **Official Research Project Live Location:**  
> This project has graduated into the core **GEOAI Research Suite**:  
> 👉 [**01_VegHealthCNN: 1D-CNN for Spectral-Temporal Crop Health Mapping**](https://github.com/Emmanuel-Yerbo/GEOAI/tree/main/01_VegHealthCNN)

### Summary
A custom 57,091-parameter 1D-Convolutional Neural Network in PyTorch trained on multi-temporal Sentinel-2 spectral-temporal signatures, strictly evaluated using spatial block cross-validation (GroupKFold across 0.01° spatial blocks) to eliminate spatial autocorrelation data leakage. Achieved **98.7% test accuracy** and formulated variable-rate nitrogen prescriptions saving **19.5% fertilizer** across 172,334 hectares in Ghana.
