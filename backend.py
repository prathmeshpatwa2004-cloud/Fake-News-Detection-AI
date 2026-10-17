import os

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="TruthAI API")

# Configure these environment variables on your backend host.
HF_TOKEN = os.getenv("HF_TOKEN", "")
MODEL_ID = os.getenv("MODEL_ID", "")

# Replace with your deployed GitHub Pages origin.
# Example: https://yourusername.github.io
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN else [],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


class NewsRequest(BaseModel):
    text: str = Field(min_length=20, max_length=10000)
    language: str = Field(pattern="^(en|hi|mr)$")


@app.get("/")
def home():
    return {
        "app": "TruthAI",
        "status": "online"
    }


@app.post("/analyze")
def analyze_news(request: NewsRequest):
    if not HF_TOKEN or not MODEL_ID:
        raise HTTPException(
            status_code=503,
            detail="AI model is not configured on the server."
        )

    api_url = (
        "https://router.huggingface.co/hf-inference/models/"
        + MODEL_ID
    )

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": request.text
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=60
        )
    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the AI provider."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="The AI provider could not analyze this article."
        )

    try:
        predictions = response.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Invalid response from the AI provider."
        )

    # Hugging Face classification responses commonly contain
    # label/score objects. Normalize common response shapes.
    if (
        isinstance(predictions, list)
        and predictions
        and isinstance(predictions[0], list)
    ):
        predictions = predictions[0]

    if (
        not isinstance(predictions, list)
        or not predictions
        or not isinstance(predictions[0], dict)
    ):
        raise HTTPException(
            status_code=502,
            detail="The model returned an unexpected result."
        )

    best = max(
        predictions,
        key=lambda item: float(item.get("score", 0))
    )

    raw_label = str(best.get("label", "unknown"))
    confidence = float(best.get("score", 0))

    # Do not invent truth/falsity labels for unknown model classes.
    normalized = raw_label.lower().replace("_", " ").replace("-", " ")

    fake_labels = {"fake", "false", "misinformation"}
    real_labels = {"real", "true", "reliable", "genuine"}

    if normalized in fake_labels:
        label = "Potential misinformation"
        explanation = (
            "The configured model classified this text as fake-related. "
            "Verify the claims using trusted sources."
        )
    elif normalized in real_labels:
        label = "Model predicts likely authentic"
        explanation = (
            "The configured model classified this text as real-related. "
            "This does not independently confirm its accuracy."
        )
    else:
        label = "Uncertain classification"
        explanation = (
            "The model returned a label that is not mapped to "
            "a validated fake-news category."
        )

    return {
        "label": label,
        "explanation": explanation,
        "confidence": confidence,
        "model_label": raw_label,
        "language": request.language,
        "verified": False
  }
