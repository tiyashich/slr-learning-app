# Model Files

Place model files here for local Streamlit/GitHub demos:

- `models/yolo.pt`
- `models/xceptionnet.keras`

These model files are intentionally ignored by Git because they are large. For GitHub deployment, use one of these options:

1. Use Git LFS for the model files.
2. Download the model files at app startup from a release asset or cloud storage.
3. Keep the app local and set environment variables:

```powershell
$env:SLR_DETECTOR_MODEL="D:\Major Project\S1 - YOLO Object Detection\yolo.pt"
$env:SLR_CLASSIFIER_MODEL="D:\Major Project\CNN Classification Pipeline\xceptionnet.keras"
```
