from pathlib import Path
from tempfile import NamedTemporaryFile

import streamlit as st
import streamlit.components.v1 as components

from ml_pipeline import (
    CLASSIFIER_MODEL_PATH,
    DETECTOR_MODEL_PATH,
    cv2,
    detect_and_classify,
    draw_detections,
)


st.set_page_config(page_title="SLR Learning Platform", page_icon="SL", layout="wide")

MODULES = [
    {
        "title": "1. Camera and Hand Setup",
        "type": "Foundation",
        "goal": "Make the hand clear for both learners and the model.",
        "lesson": "Before learning signs, prepare your space. Use a plain background, keep your hand inside the frame, and avoid shadows.",
        "tasks": ["Use a plain background", "Keep the full hand visible", "Avoid blur and shadows"],
        "prompt": "Show your hand to the camera with fingers visible and wrist relaxed.",
    },
    {
        "title": "2. Classes 0-9",
        "type": "Alphabet Practice",
        "goal": "Build confidence with a small class group first.",
        "lesson": "Start with the first ten sign classes. Practice slowly so your fingers form a consistent shape each time.",
        "tasks": ["Practice each sign five times", "Capture a test image", "Repeat weak classes"],
        "prompt": "Choose one class from zero to nine and repeat it five times.",
    },
    {
        "title": "3. Classes 10-24",
        "type": "Recognition Practice",
        "goal": "Compare similar signs and improve precision.",
        "lesson": "The middle class group may contain signs that look similar. Compare finger spacing, palm angle, and wrist position.",
        "tasks": ["Check model confidence", "Adjust hand angle", "Record confusing classes"],
        "prompt": "Practice two similar classes back to back and note what changes.",
    },
    {
        "title": "4. Classes 25-48",
        "type": "Full Model Practice",
        "goal": "Use the complete XceptionNet class set.",
        "lesson": "Now use the full model range. Work in small batches so you can remember which signs need more practice.",
        "tasks": ["Practice in batches", "Retest low-confidence signs", "Aim for stable predictions"],
        "prompt": "Practice five advanced classes and retest the hardest one.",
    },
    {
        "title": "5. Review and Quiz",
        "type": "Retention",
        "goal": "Turn model feedback into learning progress.",
        "lesson": "Review turns practice into memory. Focus on weak signs, quiz yourself, then repeat the signs with lower confidence.",
        "tasks": ["Review missed signs", "Take the quiz", "Complete a daily 10-minute session"],
        "prompt": "Write down three signs that need review today.",
    },
]

QUIZ = [
    {
        "question": "What should you check before using camera practice?",
        "answer": "Hand visibility",
        "options": ["Hand visibility", "Background music", "Screen brightness"],
    },
    {
        "question": "What should you do with signs that get low confidence?",
        "answer": "Repeat and review them",
        "options": ["Skip them", "Repeat and review them", "Delete the module"],
    },
    {
        "question": "Why practice in small class groups?",
        "answer": "It improves memory and comparison",
        "options": ["It improves memory and comparison", "It makes the model smaller", "It removes the need for quizzes"],
    },
]

st.title("SLR Sign Language Learning Platform")
st.caption("Interactive lessons, vocal assistance, quizzes, review, and optional YOLO plus XceptionNet recognition.")

with st.sidebar:
    st.header("Learning Controls")
    st.write("Use the lesson voice buttons to hear guidance aloud.")
    confidence = st.slider("Detection confidence", 0.05, 0.95, 0.25, 0.05)
    with st.expander("Model paths"):
        st.write("YOLO detector")
        st.code(str(DETECTOR_MODEL_PATH))
        st.write("XceptionNet classifier")
        st.code(str(CLASSIFIER_MODEL_PATH))

tab_lessons, tab_assistant, tab_quiz, tab_upload, tab_camera, tab_review = st.tabs(
    ["Learning Modules", "Voice Assistant", "Quiz", "Image Recognition", "Camera Practice", "Review"]
)


def speak_button(text, key):
    safe_text = text.replace("\\", "\\\\").replace("`", "\\`")
    components.html(
        f"""
        <button id="speak-{key}" style="
            background:#126c75;color:white;border:0;border-radius:8px;
            padding:10px 14px;font-weight:700;cursor:pointer;">
            Speak guidance
        </button>
        <script>
        const button = document.getElementById("speak-{key}");
        button.onclick = () => {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(`{safe_text}`);
            utterance.rate = 0.92;
            window.speechSynthesis.speak(utterance);
        }};
        </script>
        """,
        height=48,
    )


def render_prediction(image_bytes, suffix=".jpg"):
    if cv2 is None:
        st.error(
            "The cloud demo is running without ML packages. Use the Learning Modules tab, "
            "or install requirements-ml.txt locally to enable recognition."
        )
        return

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
    for index, module in enumerate(MODULES):
        with st.container(border=True):
            done = st.checkbox(module["title"], key=module["title"])
            completed += int(done)
            st.caption(module["type"])
            st.write(module["goal"])
            st.write(module["lesson"])
            speak_button(f"{module['title']}. {module['lesson']} Practice prompt: {module['prompt']}", f"module-{index}")
            st.info(module["prompt"])
            for task in module["tasks"]:
                st.write(f"- {task}")

    st.progress(completed / len(MODULES))
    st.write(f"{completed} of {len(MODULES)} modules marked complete.")

with tab_assistant:
    st.subheader("Vocal Learning Assistant")
    topic = st.selectbox(
        "Choose what you need help with",
        ["Getting started", "Daily practice", "Camera setup", "Low confidence predictions", "Review plan"],
    )
    responses = {
        "Getting started": "Start with camera and hand setup. Then practice classes zero to nine before moving to harder groups.",
        "Daily practice": "Practice for ten minutes. Review two old signs, learn one new sign, then test yourself.",
        "Camera setup": "Use a plain background, bright front lighting, and keep your full hand in the frame.",
        "Low confidence predictions": "Slow down, center the hand, reduce blur, and repeat the sign three times.",
        "Review plan": "Write down weak signs, practice each one five times, and retest after a short break.",
    }
    assistant_text = responses[topic]
    st.write(assistant_text)
    speak_button(assistant_text, "assistant")

with tab_quiz:
    st.subheader("Learning Check")
    score = 0
    for index, item in enumerate(QUIZ):
        choice = st.radio(item["question"], item["options"], key=f"quiz-{index}")
        if choice == item["answer"]:
            score += 1
    if st.button("Check quiz"):
        st.success(f"Score: {score} of {len(QUIZ)}")
        if score < len(QUIZ):
            st.write("Review the module guidance, then try again.")

with tab_upload:
    st.subheader("Practice With Uploaded Images")
    st.write("Use this after a module to check whether the detector and classifier understand your sign.")
    if cv2 is None:
        st.info("Recognition is disabled in the lightweight cloud deployment. The learning modules still work.")
    uploaded = st.file_uploader("Upload a hand sign image", type=["jpg", "jpeg", "png", "webp"])
    if uploaded:
        render_prediction(uploaded.getvalue(), Path(uploaded.name).suffix)

with tab_camera:
    st.subheader("Camera Practice")
    st.write("Capture a sign, inspect the prediction, then adjust your hand shape or framing.")
    if cv2 is None:
        st.info("Camera classification needs the local ML environment from requirements-ml.txt.")
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
