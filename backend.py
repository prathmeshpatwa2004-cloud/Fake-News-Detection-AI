import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="TruthAI API")

HF_TOKEN = os.getenv("HF_TOKEN", "")
MODEL_ID = os.getenv("MODEL_ID", "")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN else [],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class NewsRequest(BaseModel):
    text: str = Field(min_length=20, max_length=10000)
    language: str = Field(pattern="^(en|hi|mr)$")


@app.get("/")
def home():
    return {"app": "TruthAI", "status": "online"}


@app.post("/analyze")
def analyze_news(request: NewsRequest):
    if not HF_TOKEN or not MODEL_ID:
        raise HTTPException(
            status_code=503,
            detail="AI model is not configured yet."
        )

    url = (
        "https://router.huggingface.co/hf-inference/models/"
        + MODEL_ID
    )

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"inputs": request.text},
            timeout=60,
        )
        response.raise_for_status()
        predictions = response.json()

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="AI provider request failed."
        )
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Invalid AI provider response."
        )

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
            detail="Unexpected model output."
        )

    try:
        best = max(
            predictions,
            key=lambda item: float(item.get("score", 0))
        )
        raw_label = str(best.get("label", "unknown"))
        confidence = float(best.get("score", 0))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Invalid model prediction."
        )

    label_normalized = raw_label.lower().replace("_", " ")

    if label_normalized in {"fake", "false", "misinformation"}:
        label = "Potential misinformation"
        explanation = (
            "The model classified this article as fake-related. "
            "Verify its claims using reliable sources."
        )
    elif label_normalized in {"real", "true", "reliable", "genuine"}:
        label = "Model predicts likely authentic"
        explanation = (
            "The model classified this article as real-related. "
            "This does not independently verify the news."
        )
    else:
        label = "Uncertain classification"
        explanation = (
            "The model returned a label whose meaning has not "
            "been configured. No truth verdict can be given."
        )

    return {
        "label": label,
        "explanation": explanation,
        "confidence": confidence,
        "model_label": raw_label,
        "language": request.language,
        "verified": False,
    }
