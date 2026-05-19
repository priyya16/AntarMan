import re
from typing import Dict


class ModerationService:
    def __init__(self) -> None:
        self.blocked_words = {
            "abuseword1",
            "abuseword2",
            "fuck",
            "bitch",
            "bastard",
            "slut",
        }
        self.toxic_phrases = {
            "go die",
            "you should die",
            "worthless person",
            "nobody wants you",
        }

    def evaluate(self, text: str) -> Dict[str, str | bool]:
        clean = (text or "").strip()
        lower = clean.lower()

        has_toxic_phrase = any(phrase in lower for phrase in self.toxic_phrases)
        words = re.findall(r"[a-zA-Z']+", lower)
        blocked_count = sum(1 for word in words if word in self.blocked_words)

        blocked = has_toxic_phrase or blocked_count >= 2
        sanitized = self._mask_blocked_words(clean)
        reason = ""
        if blocked:
            reason = "Message blocked due to unsafe/profane language."
        elif blocked_count == 1:
            reason = "One profane word was masked."

        return {
            "blocked": blocked,
            "sanitized_text": sanitized,
            "reason": reason,
        }

    def _mask_blocked_words(self, text: str) -> str:
        masked = text
        for word in self.blocked_words:
            pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            masked = pattern.sub("*" * len(word), masked)
        return masked
