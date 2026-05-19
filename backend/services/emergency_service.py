from typing import Dict, List


HELPLINES = {
    "india": ["Kiran Mental Health Helpline: 1800-599-0019"],
    "usa": ["988 Suicide & Crisis Lifeline: Call or text 988"],
    "uk": ["Samaritans: 116 123"],
    "default": ["Emergency services: 112 or your local emergency number"],
}


class EmergencyService:
    def detect(self, text: str, emotion_label: str, intensity: str) -> bool:
        danger_words = [
            "suicide",
            "kill myself",
            "self harm",
            "end my life",
            "hurt myself",
            "don't want to live",
        ]
        lower = (text or "").lower()
        if any(word in lower for word in danger_words):
            return True
        return emotion_label in {"stress", "anxiety", "sadness", "anger"} and intensity == "High"

    def build_message(self, country: str) -> Dict[str, List[str] | str]:
        country_key = (country or "default").strip().lower()
        lines = HELPLINES.get(country_key, HELPLINES["default"])
        return {
            "title": "You may need urgent support",
            "message": "Your safety matters. Please contact immediate support and talk to someone you trust.",
            "helplines": lines,
        }
