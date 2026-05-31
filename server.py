from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ml_pipeline import detect_and_classify


APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="SLR Sign Recognition Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return FileResponse(APP_DIR / "index.html")


@app.post("/api/detect")
async def detect(image: UploadFile = File(...)):
    suffix = Path(image.filename or "image.jpg").suffix or ".jpg"

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await image.read())

    try:
        return {"detections": detect_and_classify(temp_path)}
    finally:
        temp_path.unlink(missing_ok=True)


app.mount("/", StaticFiles(directory=APP_DIR, html=True), name="static")
