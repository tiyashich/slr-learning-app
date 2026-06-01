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


st.set_page_config(page_title="SLR Learning Platform", page_icon="SL", layout="wide")

MODULES = [
    {
        "title": "1. Camera and Hand Setup",
        "type": "Foundation",
        "target_class": None,
        "goal": "Make the hand clear for both learners and the model.",
        "lesson": "Before learning signs, prepare your space. Use a plain background, keep your hand inside the frame, and avoid shadows.",
        "concepts": [
            "Signs are visual, so clarity matters as much as memory.",
            "A plain background helps learners focus on hand shape.",
            "Good lighting helps the recognition model find the hand boundary.",
        ],
        "tasks": ["Use a plain background", "Keep the full hand visible", "Avoid blur and shadows"],
        "mistakes": ["Hand partly outside frame", "Backlight behind the hand", "Fast movement causing blur"],
        "prompt": "Show your hand to the camera with fingers visible and wrist relaxed.",
    },
    {
        "title": "2. Classes 0-9",
        "type": "Alphabet Practice",
        "target_class": "0",
        "goal": "Build confidence with a small class group first.",
        "lesson": "Start with the first ten sign classes. Practice slowly so your fingers form a consistent shape each time.",
        "concepts": [
            "Learn signs in small groups instead of trying all 49 at once.",
            "Hold each sign for two seconds before changing.",
            "Use the same camera distance while practicing one group.",
        ],
        "tasks": ["Practice each sign five times", "Capture a test image", "Repeat weak classes"],
        "mistakes": ["Changing signs too quickly", "Not checking palm direction", "Practicing too many signs in one sitting"],
        "prompt": "Choose one class from zero to nine and repeat it five times.",
    },
    {
        "title": "3. Classes 10-24",
        "type": "Recognition Practice",
        "target_class": "10",
        "goal": "Compare similar signs and improve precision.",
        "lesson": "The middle class group may contain signs that look similar. Compare finger spacing, palm angle, and wrist position.",
        "concepts": [
            "Similar signs should be practiced side by side.",
            "Small finger differences can change the class prediction.",
            "Confidence improves when your hand shape is consistent.",
        ],
        "tasks": ["Check model confidence", "Adjust hand angle", "Record confusing classes"],
        "mistakes": ["Ignoring low-confidence predictions", "Only practicing easy signs", "Not recording confusing pairs"],
        "prompt": "Practice two similar classes back to back and note what changes.",
    },
    {
        "title": "4. Classes 25-48",
        "type": "Full Model Practice",
        "target_class": "25",
        "goal": "Use the complete XceptionNet class set.",
        "lesson": "Now use the full model range. Work in small batches so you can remember which signs need more practice.",
        "concepts": [
            "Full-set practice is best after smaller groups feel stable.",
            "Batch practice prevents fatigue and sloppy hand shapes.",
            "A weak class list helps you personalize review.",
        ],
        "tasks": ["Practice in batches", "Retest low-confidence signs", "Aim for stable predictions"],
        "mistakes": ["Rushing through all classes", "Skipping rest breaks", "Treating one correct prediction as mastery"],
        "prompt": "Practice five advanced classes and retest the hardest one.",
    },
    {
        "title": "5. Review and Quiz",
        "type": "Retention",
        "target_class": None,
        "goal": "Turn model feedback into learning progress.",
        "lesson": "Review turns practice into memory. Focus on weak signs, quiz yourself, then repeat the signs with lower confidence.",
        "concepts": [
            "Review should focus on signs you miss, not only signs you like.",
            "Short daily practice is stronger than one long weekly session.",
            "A quiz checks memory without depending on the camera.",
        ],
        "tasks": ["Review missed signs", "Take the quiz", "Complete a daily 10-minute session"],
        "mistakes": ["No review list", "Only using recognition without recall", "Practicing without a goal"],
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

GLOSSARY = {
    "Handshape": "The shape made by the fingers and palm. It is one of the most important parts of a sign.",
    "Palm orientation": "The direction your palm faces, such as forward, inward, up, or down.",
    "Movement": "The path or motion used while signing. Some signs are static, while others move.",
    "Location": "Where the sign is made relative to the body or camera frame.",
    "Confidence": "The model's estimated certainty for a prediction. Low confidence means the sign needs another look.",
    "Review set": "A personal list of signs that need more practice.",
}

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

tab_lessons, tab_library, tab_practice, tab_assistant, tab_quiz, tab_upload, tab_review = st.tabs(
    ["Learning Modules", "Content Library", "ML Practice Lab", "Voice Assistant", "Quiz", "Image Recognition", "Review"]
)


def speak_button(text, key):
    safe_text = text.replace("\\", "\\\\").replace("`", "\\`")
    st.iframe(
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


def evaluate_gesture(image_bytes, expected_class, suffix=".jpg"):
    if cv2 is None:
        st.warning("Gesture checking needs the local ML environment. The cloud version keeps the lessons active without recognition.")
        return

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(image_bytes)

    try:
        try:
            with st.spinner("Checking your gesture..."):
                detections = detect_and_classify(temp_path, confidence=confidence)
                image = cv2.imread(str(temp_path))
                annotated = draw_detections(image, detections)
                annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        except Exception as exc:
            st.error("The ML check failed before it could score the gesture.")
            st.exception(exc)
            return

        st.image(annotated, caption="Gesture check", use_container_width=True)

        classifications = [
            detection.get("classification")
            for detection in detections
            if detection.get("classification")
        ]

        if not detections:
            st.error("I could not detect a hand. Move closer, improve lighting, and keep the full hand inside the frame.")
            return

        if not classifications:
            st.error("I found a hand, but could not classify the sign. Try holding the gesture more steadily.")
            return

        best = max(classifications, key=lambda item: item["confidence"])
        if best["label"] == expected_class:
            st.success(
                f"Correct gesture. The model predicted class {best['label']} "
                f"with {best['confidence']:.1%} confidence."
            )
        else:
            st.error(
                f"Not yet. Expected class {expected_class}, but the model predicted "
                f"class {best['label']} with {best['confidence']:.1%} confidence."
            )
            st.write("Adjust finger shape, palm direction, and camera framing, then try again.")
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
            left, middle, right = st.columns(3)
            with left:
                st.markdown("**Key Concepts**")
                for concept in module["concepts"]:
                    st.write(f"- {concept}")
            with middle:
                st.markdown("**Practice Steps**")
                for task in module["tasks"]:
                    st.write(f"- {task}")
            with right:
                st.markdown("**Avoid**")
                for mistake in module["mistakes"]:
                    st.write(f"- {mistake}")

            if module["target_class"] is not None:
                st.markdown("**ML Practice**")
                st.write(
                    f"Go to **ML Practice Lab**, choose class {module['target_class']}, "
                    "capture your gesture, and the model will check it."
                )
            else:
                st.markdown("**Readiness Check**")
                st.write("This module prepares you for ML-based gesture checking in the next lessons.")

    st.progress(completed / len(MODULES))
    st.write(f"{completed} of {len(MODULES)} modules marked complete.")

with tab_library:
    st.subheader("Learning Content Library")
    st.write("Use this section as a reference while practicing signs.")
    selected_module = st.selectbox("Choose a lesson topic", [module["title"] for module in MODULES])
    module = next(item for item in MODULES if item["title"] == selected_module)
    st.markdown(f"**Lesson:** {module['lesson']}")
    st.markdown(f"**Goal:** {module['goal']}")
    st.markdown("**Drill:**")
    st.write(module["prompt"])
    speak_button(f"{module['lesson']} Drill: {module['prompt']}", "library")

    st.divider()
    st.subheader("Glossary")
    for term, definition in GLOSSARY.items():
        with st.expander(term):
            st.write(definition)

with tab_practice:
    st.subheader("ML Practice Lab")
    st.write("Pick the sign class you want to practice, capture your gesture, and let the model check it.")
    target_class = st.selectbox("Target sign class", [str(value) for value in range(49)], key="practice-target")
    st.info(
        f"Make sign class {target_class}. Keep the full hand visible, hold still, then capture."
    )
    speak_button(
        f"Practice sign class {target_class}. Keep your full hand visible, hold still, then capture the image.",
        "practice-lab",
    )
    captured = st.camera_input("Capture your gesture", key="practice-camera")
    if captured:
        evaluate_gesture(captured.getvalue(), target_class, ".jpg")

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
