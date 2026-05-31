# SLR Sign Language Learning App

This app combines a sign language learning platform, a voice-supported help chatbot, YOLO hand detection, and XceptionNet sign classification for uploaded or captured images.

## Files

- `index.html`, `styles.css`, `app.js`: frontend learning app
- `server.py`: local FastAPI backend for `yolo.pt` and `xceptionnet.keras`
- `streamlit_app.py`: Streamlit ML demo for upload/camera recognition
- `ml_pipeline.py`: shared YOLO plus XceptionNet inference code
- `requirements.txt`: Python packages needed by the backend

## Models

By default, the app first looks for model files in:

```text
models\yolo.pt
models\xceptionnet.keras
```

If those files are not present, it falls back to your local Windows model paths.

Your current YOLO hand detector path is:

```text
D:\Major Project\S1 - YOLO Object Detection\yolo.pt
```

It also loads the XceptionNet sign classifier:

```text
D:\Major Project\CNN Classification Pipeline\xceptionnet.keras
```

Your current XceptionNet sign classifier path is:

```text
D:\Major Project\CNN Classification Pipeline\xceptionnet.keras
```

You can also set paths with environment variables:

```powershell
$env:SLR_DETECTOR_MODEL="D:\Major Project\S1 - YOLO Object Detection\yolo.pt"
$env:SLR_CLASSIFIER_MODEL="D:\Major Project\CNN Classification Pipeline\xceptionnet.keras"
```

## Run FastAPI Web App

Install Python 3.11 first if it is not available on your PATH. TensorFlow and Ultralytics may fail on newer Python versions. Then run:

```powershell
pip install -r requirements.txt
uvicorn server:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

The Recognition section sends images to `/api/detect`. The backend detects hand boxes with YOLO, crops each hand region, classifies each crop with XceptionNet, and returns both the hand box and predicted class label.

## Run Streamlit App

Streamlit is the easiest local demo for the ML part. Use Python 3.11:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Use the Image Recognition tab for uploaded pictures or the Camera tab for a live capture.

## GitHub

This folder is ready to put on GitHub. Do not commit the large `.pt` or `.keras` model files unless your repository is configured for Git LFS.

Basic GitHub setup:

```powershell
git init
git add .
git commit -m "Build SLR Streamlit learning app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

For Streamlit Community Cloud, select:

```text
streamlit_app.py
```

as the app entry file. The included `runtime.txt` asks Streamlit to use Python 3.11.9.
