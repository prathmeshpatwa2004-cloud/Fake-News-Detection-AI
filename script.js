// =====================================
// TruthAI - Fake News Detection
// =====================================

// STEP 1: Add your Render backend URL here
// Example: https://your-service.onrender.com/analyze

const API_URL = "YOUR_BACKEND_URL/analyze";

// Get HTML elements
const newsInput = document.getElementById("news");
const languageInput = document.getElementById("language");
const checkButton = document.getElementById("checkButton");
const resultBox = document.getElementById("result");
const loading = document.getElementById("loading");
const charCount = document.getElementById("charCount");

// Character counter
newsInput.addEventListener("input", function () {
  charCount.textContent = newsInput.value.length;
});

// Analyze button
checkButton.addEventListener("click", analyzeNews);

// Main analysis function
async function analyzeNews() {
  const text = newsInput.value.trim();
  const language = languageInput.value;

  // Validate input
  if (text.length < 20) {
    showResult(
      "⚠️ More Text Required",
      "Please enter at least 20 characters of news."
    );
    return;
  }

  if (text.length > 10000) {
    showResult(
      "⚠️ Text Too Long",
      "Please enter no more than 10,000 characters."
    );
    return;
  }

  // Check backend URL
  if (API_URL.startsWith("YOUR_BACKEND_URL")) {
    showResult(
      "🔌 Backend Not Connected",
      "Your website is working, but the AI backend is not connected yet. Deploy backend.py on Render and update API_URL."
    );
    return;
  }

  // Show loading state
  checkButton.disabled = true;
  loading.hidden = false;
  resultBox.hidden = true;

  try {
    // Send article to Python backend
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: text,
        language: language
      })
    });

    // Read response
    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "The AI service could not analyze this article."
      );
    }

    // Display actual backend response
    showResult(
      data.label || "Analysis Completed",
      data.explanation || "The model returned a prediction.",
      data.confidence,
      data.model_label
    );

  } catch (error) {
    console.error("TruthAI error:", error);

    showResult(
      "❌ Connection Error",
      error.message ||
        "Could not connect to the backend. Check the URL and try again."
    );

  } finally {
    loading.hidden = true;
    checkButton.disabled = false;
  }
}

// Display results safely
function showResult(title, explanation, confidence, modelLabel) {
  resultBox.replaceChildren();

  const heading = document.createElement("h2");
  heading.textContent = title;
  resultBox.appendChild(heading);

  const message = document.createElement("p");
  message.textContent = explanation;
  resultBox.appendChild(message);

  // Show confidence only when supplied by the backend
  if (
    typeof confidence === "number" &&
    Number.isFinite(confidence) &&
    confidence >= 0 &&
    confidence <= 1
  ) {
    const score = document.createElement("p");
    score.textContent =
      "Model confidence: " +
      (confidence * 100).toFixed(1) +
      "%";

    resultBox.appendChild(score);
  }

  // Show raw model label for transparency
  if (modelLabel) {
    const label = document.createElement("p");
    label.textContent = "Model output: " + modelLabel;
    resultBox.appendChild(label);
  }

  const warning = document.createElement("p");
  warning.textContent =
    "⚠️ AI predictions are not independently verified facts. Check reliable sources.";

  resultBox.appendChild(warning);
  resultBox.hidden = false;
}
