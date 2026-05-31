import os
from pathlib import Path

LOCAL_DETECTOR_MODEL_PATH = Path(r"D:\Major Project\S1 - YOLO Object Detection\yolo.pt")
LOCAL_CLASSIFIER_MODEL_PATH = Path(r"D:\Major Project\CNN Classification Pipeline\xceptionnet.keras")
REPO_MODEL_DIR = Path(__file__).resolve().parent / "models"

DETECTOR_MODEL_PATH = Path(
    os.getenv("SLR_DETECTOR_MODEL", str(REPO_MODEL_DIR / "yolo.pt"))
)
CLASSIFIER_MODEL_PATH = Path(
    os.getenv("SLR_CLASSIFIER_MODEL", str(REPO_MODEL_DIR / "xceptionnet.keras"))
)

if not DETECTOR_MODEL_PATH.exists() and LOCAL_DETECTOR_MODEL_PATH.exists():
    DETECTOR_MODEL_PATH = LOCAL_DETECTOR_MODEL_PATH

if not CLASSIFIER_MODEL_PATH.exists() and LOCAL_CLASSIFIER_MODEL_PATH.exists():
    CLASSIFIER_MODEL_PATH = LOCAL_CLASSIFIER_MODEL_PATH
CLASS_NAMES = [str(index) for index in range(49)]
IMG_SIZE = 299

try:
    from ultralytics import YOLO
except ImportError as exc:
    YOLO = None
    YOLO_IMPORT_ERROR = exc
else:
    YOLO_IMPORT_ERROR = None

try:
    import cv2
    import numpy as np
    import tensorflow as tf
    from tensorflow.keras.applications.xception import preprocess_input
except ImportError as exc:
    cv2 = None
    np = None
    tf = None
    preprocess_input = None
    CLASSIFIER_IMPORT_ERROR = exc
else:
    CLASSIFIER_IMPORT_ERROR = None


detector_model = None
classifier_model = None


def get_detector_model():
    global detector_model
    if YOLO is None:
        raise RuntimeError(
            "The ultralytics package is not installed. Install requirements.txt first."
        ) from YOLO_IMPORT_ERROR
    if not DETECTOR_MODEL_PATH.exists():
        raise RuntimeError(f"Detector model file not found: {DETECTOR_MODEL_PATH}")
    if detector_model is None:
        detector_model = YOLO(str(DETECTOR_MODEL_PATH))
    return detector_model


def get_classifier_model():
    global classifier_model
    if tf is None:
        raise RuntimeError(
            "TensorFlow, OpenCV, or NumPy is not installed. Install requirements.txt first."
        ) from CLASSIFIER_IMPORT_ERROR
    if not CLASSIFIER_MODEL_PATH.exists():
        raise RuntimeError(f"Classifier model file not found: {CLASSIFIER_MODEL_PATH}")
    if classifier_model is None:
        classifier_model = tf.keras.models.load_model(str(CLASSIFIER_MODEL_PATH))
    return classifier_model


def letterbox_image(image, size):
    height, width = image.shape[:2]
    target_width, target_height = size
    scale = min(target_width / width, target_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    resized = cv2.resize(image, (new_width, new_height))
    canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    top = (target_height - new_height) // 2
    left = (target_width - new_width) // 2
    canvas[top : top + new_height, left : left + new_width] = resized
    return canvas


def classify_crop(crop):
    classifier = get_classifier_model()
    prepared = letterbox_image(crop, (IMG_SIZE, IMG_SIZE))
    prepared = preprocess_input(prepared.astype(np.float32))
    prediction = classifier.predict(np.expand_dims(prepared, axis=0), verbose=0)[0]
    class_index = int(np.argmax(prediction))
    return {
        "class_id": class_index,
        "label": CLASS_NAMES[class_index],
        "confidence": float(prediction[class_index]),
    }


def detect_and_classify(image_path, confidence=0.25):
    detector = get_detector_model()
    source_image = cv2.imread(str(image_path))
    if source_image is None:
        raise RuntimeError("Could not read the uploaded image.")

    result = detector.predict(str(image_path), conf=confidence, verbose=False)[0]
    names = result.names
    detections = []

    for box in result.boxes:
        class_id = int(box.cls[0])
        xyxy = [float(value) for value in box.xyxy[0].tolist()]
        height, width = source_image.shape[:2]
        x1, y1, x2, y2 = xyxy
        left = max(0, int(x1))
        top = max(0, int(y1))
        right = min(width, int(x2))
        bottom = min(height, int(y2))
        crop = source_image[top:bottom, left:right]
        classification = classify_crop(crop) if crop.size else None

        detections.append(
            {
                "label": names.get(class_id, "hand"),
                "confidence": float(box.conf[0]),
                "box": xyxy,
                "classification": classification,
            }
        )

    return detections


def draw_detections(image, detections):
    if cv2 is None:
        raise RuntimeError("OpenCV is not installed. Install requirements.txt first.")

    output = image.copy()
    for detection in detections:
        x1, y1, x2, y2 = [int(value) for value in detection["box"]]
        classification = detection.get("classification")
        label = detection["label"]
        if classification:
            label = f"Sign {classification['label']} {classification['confidence']:.0%}"

        cv2.rectangle(output, (x1, y1), (x2, y2), (244, 185, 66), 3)
        cv2.putText(
            output,
            label,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (244, 185, 66),
            2,
            cv2.LINE_AA,
        )

    return output
