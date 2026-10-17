const newsInput = document.getElementById("news");
const languageInput = document.getElementById("language");
const checkButton = document.getElementById("checkButton");
const resultBox = document.getElementById("result");
const loading = document.getElementById("loading");
const charCount = document.getElementById("charCount");

// Change this after deploying your Python backend.
const API_URL = "YOUR_BACKEND_URL/analyze";

newsInput.addEventListener("input", () => {
  charCount.textContent = newsInput.value.length;
});

checkButton.addEventListener("click", analyzeNews);

async function analyzeNews() {
  const text = newsInput.value.trim();

  if (text.length < 20) {
    showResult(
      "More text required",
      "Please enter at least 20 characters of news."
    );
    return;
  }

  if (text.length > 10000) {
    showResult(
      "Text too long",
      "Please limit your article to 10,000 characters."
    );
    return;
  }

  if (API_URL.startsWith("YOUR_BACKEND_URL")) {
    showResult(
      "Backend not connected",
      "Deploy the Python backend and update API_URL in script.js."
    );
    return;
  }

  checkButton.disabled = true;
  loading.hidden = false;
  resultBox.hidden = true;

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: text,
        language: languageInput.value
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Analysis failed.");
    }

    showResult(
      data.label || "Analysis completed",
      data.explanation || "The model returned a prediction.",
      data.confidence
    );

  } catch (error) {
    showResult(
      "Unable to analyze",
      error.message || "Check your internet connection and backend."
    );
  } finally {
    loading.hidden = true;
    checkButton.disabled = false;
  }
}

function showResult(title, explanation, confidence) {
  resultBox.replaceChildren();

  const heading = document.createElement("h2");
  heading.textContent = title;

  const message = document.createElement("p");
  message.textContent = explanation;

  resultBox.append(heading, message);

  if (typeof confidence === "number" &&
      Number.isFinite(confidence)) {
    const score = document.createElement("p");
    score.textContent =
      "Model confidence: " + (confidence * 100).toFixed(1) + "%";
    resultBox.appendChild(score);
  }

  const disclaimer = document.createElement("p");
  disclaimer.textContent =
    "This is an AI prediction, not independently verified fact.";

  resultBox.appendChild(disclaimer);
  resultBox.hidden = false;
    }
