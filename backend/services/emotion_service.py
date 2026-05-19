from typing import Dict, List

try:
    from transformers import pipeline  # type: ignore
except Exception:
    pipeline = None

from ..config import TRANSFORMERS_MODEL


class EmotionService:
    def __init__(self) -> None:
        self._classifier = None
        self._load_error = None
        if pipeline is not None:
            try:
                self._classifier = pipeline(
                    "text-classification", model=TRANSFORMERS_MODEL, top_k=None
                )
            except Exception as exc:  # pragma: no cover
                self._load_error = str(exc)

    def detect(self, text: str) -> Dict[str, str]:
        text = (text or "").strip()
        if not text:
            return {"emotion_label": "neutral", "intensity": "Low", "score": "0.00"}

        if self._classifier is not None:
            labels = self._classifier(text)
            if labels and isinstance(labels, list):
                scores: List[Dict] = labels[0] if isinstance(labels[0], list) else labels
                best = sorted(scores, key=lambda item: item["score"], reverse=True)[0]
                mapped_label = self._normalize_label(best["label"])
                intensity = self._score_to_intensity(float(best["score"]))
                return {
                    "emotion_label": mapped_label,
                    "intensity": intensity,
                    "score": f"{float(best['score']):.2f}",
                }

        # Fallback keyword classifier when model is unavailable.
        lower_text = text.lower()
        keyword_map = {
            "stress": ["stressed", "pressure", "overwhelmed", "deadline"],
            "anxiety": ["anxious", "anxiety", "panic", "nervous", "fear"],
            "sadness": ["sad", "alone", "empty", "hopeless", "cry"],
            "happiness": ["happy", "joy", "grateful", "excited", "great"],
            "anger": ["angry", "mad", "frustrated", "hate", "annoyed"],
        }
        for emotion, words in keyword_map.items():
            if any(word in lower_text for word in words):
                return {
                    "emotion_label": emotion,
                    "intensity": "Medium" if len(text) < 120 else "High",
                    "score": "0.70",
                }

        return {"emotion_label": "neutral", "intensity": "Low", "score": "0.50"}

    @staticmethod
    def _score_to_intensity(score: float) -> str:
        if score >= 0.8:
            return "High"
        if score >= 0.55:
            return "Medium"
        return "Low"

    @staticmethod
    def _normalize_label(raw: str) -> str:
        text = raw.lower()
        if "fear" in text or "anx" in text:
            return "anxiety"
        if "sad" in text or "grief" in text:
            return "sadness"
        if "joy" in text or "happy" in text:
            return "happiness"
        if "ang" in text:
            return "anger"
        if "stress" in text:
            return "stress"
        return text
