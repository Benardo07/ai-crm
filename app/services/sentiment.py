"""Sentiment analysis helper powered by Hugging Face transformers."""

import logging
from functools import lru_cache

from transformers import pipeline

from .tasks import submit

LOGGER = logging.getLogger(__name__)
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


@lru_cache(maxsize=1)
def _sentiment_pipeline():
    """Lazily instantiates the Hugging Face sentiment pipeline."""
    return pipeline("sentiment-analysis", model=MODEL_NAME)


def _normalize_label(raw_label: str | None) -> str | None:
    if raw_label is None:
        return None

    mapping = {
        "POSITIVE": "Positive",
        "NEGATIVE": "Negative",
        "NEUTRAL": "Neutral",
        "LABEL_1": "Positive",
        "LABEL_0": "Negative",
    }

    upper_label = raw_label.upper()
    return mapping.get(upper_label, upper_label.title())


def analyze_sentiment(text: str | None) -> dict[str, float | str | None]:
    """Analyze sentiment of the supplied text and return label/score."""
    if not text or not text.strip():
        return {"label": None, "score": None}

    try:
        classifier = _sentiment_pipeline()
        result = classifier(text[:512])[0]
        LOGGER.info("Sentiment raw result: %s", result)
        label = _normalize_label(result.get("label"))
        score = float(result.get("score")) if result.get("score") is not None else None
        return {"label": label, "score": score}
    except Exception as exc:
        LOGGER.exception("Sentiment analysis failed: %s", exc)
        return {"label": None, "score": None}


def enqueue_sentiment_refresh(lead_id: int) -> None:
    """Schedule asynchronous sentiment evaluation for the given lead."""
    submit(_refresh_lead_sentiment, lead_id)


def _refresh_lead_sentiment(lead_id: int) -> None:
    """Background update of a lead's sentiment fields."""
    from ..extensions import db
    from ..models import Lead

    lead = Lead.query.get(lead_id)
    if lead is None:
        LOGGER.warning("Sentiment refresh skipped - lead %s missing.", lead_id)
        return

    if not lead.notes or not lead.notes.strip():
        lead.sentiment = None
        lead.sentiment_score = None
        db.session.commit()
        return

    result = analyze_sentiment(lead.notes)
    lead.sentiment = result["label"] or "Not Analyzed"
    lead.sentiment_score = result["score"]
    db.session.commit()
