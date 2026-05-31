const lessons = [
  {
    id: "orientation",
    type: "Foundation",
    level: "Beginner",
    title: "Hand Visibility and Camera Setup",
    sign: "01",
    description: "Learn how to position your hand so both people and the ML model can read the sign clearly.",
    goal: "Set up lighting, background, and framing before practice.",
    checkpoint: "Your hand is fully visible inside the camera frame.",
    action: "Open Recognition"
  },
  {
    id: "alphabet-core",
    type: "Alphabet",
    level: "Beginner",
    title: "Core Sign Classes 0-9",
    sign: "0-9",
    description: "Start with a small group of classes from your 49-class XceptionNet model.",
    goal: "Practice each class slowly, then test it with image recognition.",
    checkpoint: "Recognizer returns the expected class three times.",
    action: "Practice with Model"
  },
  {
    id: "alphabet-next",
    type: "Alphabet",
    level: "Beginner",
    title: "Sign Classes 10-24",
    sign: "10",
    description: "Expand recognition practice after the first class group feels stable.",
    goal: "Compare similar-looking signs and focus on finger shape.",
    checkpoint: "You can explain the difference between two confusing signs.",
    action: "Review Examples"
  },
  {
    id: "alphabet-advanced",
    type: "Alphabet",
    level: "Intermediate",
    title: "Sign Classes 25-48",
    sign: "25",
    description: "Complete the full classification set supported by your trained model.",
    goal: "Practice in short sessions and use recognition feedback.",
    checkpoint: "Reach at least 80% confidence on five recent attempts.",
    action: "Run Recognition"
  },
  {
    id: "guided-recognition",
    type: "AI Practice",
    level: "Guided",
    title: "Detector to Classifier Workflow",
    sign: "AI",
    description: "Understand how YOLO finds the hand and XceptionNet predicts the sign class.",
    goal: "Use upload or camera mode to test real practice images.",
    checkpoint: "The app shows a hand box and a sign prediction.",
    action: "Try Camera"
  },
  {
    id: "review-routine",
    type: "Review",
    level: "Daily",
    title: "Spaced Review Routine",
    sign: "10m",
    description: "Use short daily practice blocks to improve recall and model-facing consistency.",
    goal: "Review weak signs, quiz yourself, then re-test with the recognizer.",
    checkpoint: "Complete one lesson, one quiz, and one recognition attempt.",
    action: "Take Quiz"
  }
];

const quizQuestions = [
  { sign: "A", answer: "Alphabet A", options: ["Alphabet A", "Hello", "Thank You", "No"] },
  { sign: "B", answer: "Alphabet B", options: ["Yes", "Alphabet B", "Goodbye", "Please"] },
  { sign: "Hi", answer: "Hello", options: ["Sorry", "Help", "Hello", "Name"] },
  { sign: "TY", answer: "Thank You", options: ["Thank You", "Where", "Learn", "Friend"] }
];

const lessonGrid = document.querySelector("#lessonGrid");
const completedCount = document.querySelector("#completedCount");
const quizScore = document.querySelector("#quizScore");
const quizSign = document.querySelector("#quizSign");
const quizOptions = document.querySelector("#quizOptions");
const quizFeedback = document.querySelector("#quizFeedback");
const nextQuestion = document.querySelector("#nextQuestion");
const chatMessages = document.querySelector("#chatMessages");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const voiceButton = document.querySelector("#voiceButton");
const speakReplies = document.querySelector("#speakReplies");
const imageUpload = document.querySelector("#imageUpload");
const startCamera = document.querySelector("#startCamera");
const captureFrame = document.querySelector("#captureFrame");
const cameraFeed = document.querySelector("#cameraFeed");
const detectorCanvas = document.querySelector("#detectorCanvas");
const detectorStatus = document.querySelector("#detectorStatus");
const detectionsList = document.querySelector("#detectionsList");
const detectorContext = detectorCanvas.getContext("2d");

let completedLessons = JSON.parse(localStorage.getItem("completedLessons") || "[]");
let currentQuestion = 0;
let quizAttempts = 0;
let quizCorrect = 0;
let cameraStream = null;

function saveProgress() {
  localStorage.setItem("completedLessons", JSON.stringify(completedLessons));
  completedCount.textContent = completedLessons.length;
}

function renderLessons() {
  lessonGrid.innerHTML = lessons
    .map((lesson) => {
      const done = completedLessons.includes(lesson.id);
      return `
        <article class="lesson-card">
          <div class="sign-preview">${lesson.sign}</div>
          <div class="lesson-meta">
            <span>${lesson.type}</span>
            <span>${lesson.level}</span>
          </div>
          <h3>${lesson.title}</h3>
          <p>${lesson.description}</p>
          <p><strong>Goal:</strong> ${lesson.goal}</p>
          <p><strong>Checkpoint:</strong> ${lesson.checkpoint}</p>
          <a class="module-link" href="${lesson.action.includes("Quiz") ? "#practice" : "#recognition"}">${lesson.action}</a>
          <button class="button complete-btn ${done ? "done" : "primary"}" data-lesson="${lesson.id}" type="button">
            ${done ? "Completed" : "Mark Complete"}
          </button>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll("[data-lesson]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.lesson;
      if (completedLessons.includes(id)) {
        completedLessons = completedLessons.filter((lessonId) => lessonId !== id);
      } else {
        completedLessons.push(id);
      }
      saveProgress();
      renderLessons();
    });
  });
}

function renderQuestion() {
  const question = quizQuestions[currentQuestion];
  quizSign.textContent = question.sign;
  quizFeedback.textContent = "";
  quizOptions.innerHTML = question.options
    .map((option) => `<button class="option-btn" type="button">${option}</button>`)
    .join("");

  document.querySelectorAll(".option-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const correct = button.textContent === question.answer;
      quizAttempts += 1;
      quizCorrect += correct ? 1 : 0;
      quizFeedback.textContent = correct ? "Correct. Nice work." : `Not quite. The answer is ${question.answer}.`;
      quizFeedback.style.color = correct ? "#176331" : "#b54708";
      quizScore.textContent = `${Math.round((quizCorrect / quizAttempts) * 100)}%`;
    });
  });
}

function addMessage(text, sender = "bot") {
  const message = document.createElement("div");
  message.className = `message ${sender}`;
  message.textContent = text;
  chatMessages.appendChild(message);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function speak(text) {
  if (!speakReplies.checked || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

function botReply(message) {
  const lower = message.toLowerCase();
  let reply = "I can help with lessons, quiz practice, progress, and beginner sign language tips. Try asking: how do I practice daily?";

  if (lower.includes("hello") || lower.includes("hi")) {
    reply = "Hello. Start with the greeting lesson, then practice it slowly in front of a mirror.";
  } else if (lower.includes("module") || lower.includes("lesson") || lower.includes("path")) {
    reply = "Follow the modules in order: prepare your camera, learn class groups, test with recognition, then review weak signs.";
  } else if (lower.includes("practice") || lower.includes("daily")) {
    reply = "A good routine is ten minutes daily: review two signs, repeat each five times, then quiz yourself without looking.";
  } else if (lower.includes("quiz") || lower.includes("test")) {
    reply = "Use the quick sign quiz to match each sign with its meaning. Your latest score appears at the top.";
  } else if (lower.includes("progress") || lower.includes("complete")) {
    reply = `You have completed ${completedLessons.length} lesson${completedLessons.length === 1 ? "" : "s"}.`;
  } else if (lower.includes("thank")) {
    reply = "For Thank You, move your hand forward from your chin. Keep the motion smooth and clear.";
  } else if (lower.includes("voice")) {
    reply = "Use the microphone button to ask by voice. Turn off the checkbox if you do not want spoken replies.";
  } else if (lower.includes("detect") || lower.includes("hand") || lower.includes("model")) {
    reply = "Use the recognition panel to upload or capture a picture. The local YOLO model detects hands and draws boxes on the image.";
  }

  addMessage(reply, "bot");
  speak(reply);
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  addMessage(text, "user");
  chatInput.value = "";
  window.setTimeout(() => botReply(text), 250);
});

voiceButton.addEventListener("click", () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    const message = "Voice input is not supported in this browser. You can still type your question.";
    addMessage(message, "bot");
    speak(message);
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.start();
  voiceButton.textContent = "Rec";

  recognition.addEventListener("result", (event) => {
    chatInput.value = event.results[0][0].transcript;
    voiceButton.textContent = "Mic";
    chatForm.requestSubmit();
  });

  recognition.addEventListener("end", () => {
    voiceButton.textContent = "Mic";
  });
});

nextQuestion.addEventListener("click", () => {
  currentQuestion = (currentQuestion + 1) % quizQuestions.length;
  renderQuestion();
});

function drawPlaceholder() {
  detectorContext.fillStyle = "#101820";
  detectorContext.fillRect(0, 0, detectorCanvas.width, detectorCanvas.height);
  detectorContext.fillStyle = "#ffffff";
  detectorContext.font = "22px sans-serif";
  detectorContext.textAlign = "center";
  detectorContext.fillText("Upload or capture an image", detectorCanvas.width / 2, detectorCanvas.height / 2);
}

function drawDetections(image, detections) {
  detectorCanvas.width = image.naturalWidth || image.videoWidth || 640;
  detectorCanvas.height = image.naturalHeight || image.videoHeight || 420;
  detectorContext.drawImage(image, 0, 0, detectorCanvas.width, detectorCanvas.height);
  detectorContext.lineWidth = Math.max(3, detectorCanvas.width / 180);
  detectorContext.font = `${Math.max(16, detectorCanvas.width / 42)}px sans-serif`;

  detections.forEach((detection) => {
    const [x1, y1, x2, y2] = detection.box;
    const classText = detection.classification
      ? `Sign ${detection.classification.label} ${Math.round(detection.classification.confidence * 100)}%`
      : `${detection.label} ${Math.round(detection.confidence * 100)}%`;
    const label = classText;
    detectorContext.strokeStyle = "#f4b942";
    detectorContext.fillStyle = "#f4b942";
    detectorContext.strokeRect(x1, y1, x2 - x1, y2 - y1);
    detectorContext.fillRect(x1, Math.max(0, y1 - 30), detectorContext.measureText(label).width + 14, 28);
    detectorContext.fillStyle = "#17202a";
    detectorContext.fillText(label, x1 + 7, Math.max(20, y1 - 9));
  });

  detectionsList.innerHTML = detections.length
    ? detections.map((item, index) => {
        const classifierText = item.classification
          ? `, classified as sign ${item.classification.label} with ${Math.round(item.classification.confidence * 100)}% confidence`
          : "";
        return `<div>${index + 1}. ${item.label} detected with ${Math.round(item.confidence * 100)}% confidence${classifierText}</div>`;
      }).join("")
    : "<div>No hands detected. Try a clearer image with the hand closer to the camera.</div>";
}

async function detectImageFromBlob(blob, imageSource) {
  detectorStatus.textContent = "Detecting hands...";
  const formData = new FormData();
  formData.append("image", blob, "hand-image.jpg");

  try {
    const response = await fetch("/api/detect", { method: "POST", body: formData });
    if (!response.ok) {
      throw new Error(`Detector returned ${response.status}`);
    }
    const result = await response.json();
    drawDetections(imageSource, result.detections || []);
    detectorStatus.textContent = `Detected ${(result.detections || []).length} hand region(s).`;
  } catch (error) {
    detectorContext.drawImage(imageSource, 0, 0, detectorCanvas.width, detectorCanvas.height);
    detectorStatus.textContent = "Backend is not running yet. Start server.py to use yolo.pt detection.";
    detectionsList.innerHTML = "<div>Run the local Python backend, then try again.</div>";
  }
}

imageUpload.addEventListener("change", () => {
  const file = imageUpload.files[0];
  if (!file) return;
  const image = new Image();
  image.addEventListener("load", () => {
    detectorCanvas.width = image.naturalWidth;
    detectorCanvas.height = image.naturalHeight;
    detectorContext.drawImage(image, 0, 0);
    detectImageFromBlob(file, image);
  });
  image.src = URL.createObjectURL(file);
});

startCamera.addEventListener("click", async () => {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    cameraFeed.srcObject = cameraStream;
    cameraFeed.style.display = "block";
    detectorStatus.textContent = "Camera started. Capture a frame to detect hands.";
  } catch (error) {
    detectorStatus.textContent = "Camera permission was blocked or is not available.";
  }
});

captureFrame.addEventListener("click", () => {
  if (!cameraStream) {
    detectorStatus.textContent = "Start the camera before capturing.";
    return;
  }
  detectorCanvas.width = cameraFeed.videoWidth || 640;
  detectorCanvas.height = cameraFeed.videoHeight || 420;
  detectorContext.drawImage(cameraFeed, 0, 0, detectorCanvas.width, detectorCanvas.height);
  detectorCanvas.toBlob((blob) => {
    if (blob) detectImageFromBlob(blob, cameraFeed);
  }, "image/jpeg", 0.9);
});

renderLessons();
renderQuestion();
saveProgress();
drawPlaceholder();
addMessage("Hi, I am your SLR help assistant. Ask me about lessons, practice, quizzes, or voice support.");
