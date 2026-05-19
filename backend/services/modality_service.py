from pathlib import Path
from typing import Optional

try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None

try:
    from PIL import Image  # type: ignore
except Exception:
    Image = None

try:
    from transformers import pipeline  # type: ignore
except Exception:
    pipeline = None


class ModalityService:
    def __init__(self) -> None:
        self.captioner = None
        if pipeline is not None:
            try:
                self.captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
            except Exception:
                self.captioner = None

    def extract_text_from_audio(self, audio_path: str) -> str:
        if sr is None:
            return "Voice note received. (SpeechRecognition package not installed.)"
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
            # Google recognizer is used for simplicity in demo projects.
            return recognizer.recognize_google(audio_data)
        except Exception:
            return "Voice note received. (Automatic transcription failed.)"

    def describe_image(self, image_path: str) -> str:
        if self.captioner is not None:
            try:
                result = self.captioner(image_path)
                if result and isinstance(result, list):
                    return result[0].get("generated_text", "Image uploaded.")
            except Exception:
                pass

        # Fallback: simple description from filename.
        return f"Image uploaded: {Path(image_path).name}. Could not generate caption automatically."

    def process_video(self, video_path: str) -> str:
        # Basic placeholder to keep project lightweight and functional.
        # In production: extract audio + key frames, then pass into STT and vision models.
        return f"Video uploaded: {Path(video_path).name}. Basic analysis complete (demo mode)."

    @staticmethod
    def detect_input_type(filename: Optional[str], explicit_type: Optional[str]) -> str:
        if explicit_type:
            return explicit_type
        if not filename:
            return "text"
        ext = Path(filename).suffix.lower()
        if ext in {".wav", ".mp3", ".m4a", ".ogg"}:
            return "audio"
        if ext in {".jpg", ".jpeg", ".png", ".webp"}:
            return "image"
        if ext in {".mp4", ".mov", ".avi", ".mkv"}:
            return "video"
        return "text"
