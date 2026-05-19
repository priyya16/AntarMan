from typing import Dict


class ResponseService:
    def __init__(self) -> None:
        self.templates = {
            "stress": "It sounds like you're carrying a lot right now. Taking one small step and one deep breath at a time can help.",
            "anxiety": "I'm really sorry you're feeling anxious. You're not weak for feeling this way, and grounding yourself gently can help.",
            "sadness": "I'm really sorry you're feeling this way. You're not alone, and it's okay to feel like this sometimes.",
            "happiness": "I'm glad you shared this positive feeling. Hold on to this moment and celebrate your progress.",
            "anger": "Your feelings are valid. If possible, take a short pause before reacting so your mind gets some space.",
            "neutral": "Thank you for sharing how you feel. I'm here to listen and support you.",
        }

    def generate(self, emotion_data: Dict[str, str], user_text: str) -> str:
        emotion = emotion_data.get("emotion_label", "neutral")
        intensity = emotion_data.get("intensity", "Low")
        base = self.templates.get(emotion, self.templates["neutral"])

        if intensity == "High":
            return (
                f"{base} Since this feels intense, consider reaching out to someone you trust right now."
            )
        if intensity == "Medium":
            return f"{base} You are taking a meaningful step by expressing it."
        return base
