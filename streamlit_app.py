from pathlib import Path
from tempfile import NamedTemporaryFile

import streamlit as st

from ml_pipeline import (
    CLASSIFIER_MODEL_PATH,
    DETECTOR_MODEL_PATH,
    cv2,
    detect_and_classify,
    draw_detections,
)


st.set_page_config(page_title="SLR Sign Recognition", page_icon="SLR", layout="wide")

MODULES = [
    {
        "title": "1. Camera and Hand Setup",
        "type": "Foundation",
        "goal": "Make the hand clear for both learners and the model.",
        "tasks": ["Use a plain background", "Keep the full hand visible", "Avoid blur and shadows"],
    },
    {
        "title": "2. Classes 0-9",
        "type": "Alphabet Practice",
        "goal": "Build confidence with a small class group first.",
        "tasks": ["Practice each sign five times", "Capture a test image", "Repeat weak classes"],
    },
    {
        "title": "3. Classes 10-24",
        "type": "Recognition Practice",
        "goal": "Compare similar signs and improve precision.",
        "tasks": ["Check model confidence", "Adjust hand angle", "Record confusing classes"],
    },
    {
        "title": "4. Classes 25-48",
        "type": "Full Model Practice",
        "goal": "Use the complete XceptionNet class set.",
        "tasks": ["Practice in batches", "Retest low-confidence signs", "Aim for stable predictions"],
    },
    {
        "title": "5. Review and Quiz",
        "type": "Retention",
        "goal": "Turn model feedback into learning progress.",
        "tasks": ["Review missed signs", "Take the quiz", "Complete a daily 10-minute session"],
    },
]

st.title("SLR Sign Language Learning")
st.caption("A guided learning app with YOLO hand detection and XceptionNet sign classification.")

with st.sidebar:
    st.header("Models")
    st.write("YOLO detector")
    st.code(str(DETECTOR_MODEL_PATH))
    st.write("XceptionNet classifier")
    st.code(str(CLASSIFIER_MODEL_PATH))
    confidence = st.slider("Detection confidence", 0.05, 0.95, 0.25, 0.05)

tab_lessons, tab_upload, tab_camera, tab_review = st.tabs(
    ["Learning Modules", "Image Recognition", "Camera Practice", "Review"]
)


def render_prediction(image_bytes, suffix=".jpg"):
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(image_bytes)

    try:
        with st.spinner("Detecting hands and classifying signs..."):
            detections = detect_and_classify(temp_path, confidence=confidence)
            image = cv2.imread(str(temp_path))
            annotated = draw_detections(image, detections)
            annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        st.image(annotated, caption="Recognition result", use_container_width=True)

        if detections:
            for index, detection in enumerate(detections, start=1):
                classification = detection.get("classification")
                if classification:
                    st.success(
                        f"Hand {index}: sign {classification['label']} "
                        f"({classification['confidence']:.1%} classifier confidence)"
                    )
                else:
                    st.info(
                        f"Hand {index}: detected with {detection['confidence']:.1%} detector confidence"
                    )
        else:
            st.warning("No hand detected. Try a clearer image with the hand closer to the camera.")
    finally:
        temp_path.unlink(missing_ok=True)


with tab_lessons:
    st.subheader("Smart Module Path")
    completed = 0
    for module in MODULES:
        with st.container(border=True):
            done = st.checkbox(module["title"], key=module["title"])
            completed += int(done)
            st.caption(module["type"])
            st.write(module["goal"])
            for task in module["tasks"]:
                st.write(f"- {task}")

    st.progress(completed / len(MODULES))
    st.write(f"{completed} of {len(MODULES)} modules marked complete.")

with tab_upload:
    st.subheader("Practice With Uploaded Images")
    st.write("Use this after a module to check whether the detector and classifier understand your sign.")
    uploaded = st.file_uploader("Upload a hand sign image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        render_prediction(uploaded.getvalue(), Path(uploaded.name).suffix)

with tab_camera:
    st.subheader("Camera Practice")
    st.write("Capture a sign, inspect the prediction, then adjust your hand shape or framing.")
    captured = st.camera_input("Capture a sign image")
    if captured:
        render_prediction(captured.getvalue(), ".jpg")

with tab_review:
    st.subheader("Daily Review")
    weak_signs = st.text_area("Signs/classes to review", placeholder="Example: 3, 12, 28")
    st.write("Suggested routine")
    st.write("- Warm up with camera setup.")
    st.write("- Practice each weak class five times.")
    st.write("- Run recognition after the fifth attempt.")
    st.write("- Move a class out of review only after stable predictions.")
    if weak_signs:
        st.info(f"Today's focus: {weak_signs}")
