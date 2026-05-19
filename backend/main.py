import uuid
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .config import UPLOAD_DIR
from .db import init_db, save_message, create_peer_post, get_connection
from .schemas import TextInputRequest, ProcessResponse, PeerPostRequest, PeerReplyRequest, PeerPost, PeerReply
from .services.emotion_service import EmotionService
from .services.response_service import ResponseService
from .services.emergency_service import EmergencyService
from .services.modality_service import ModalityService

# Initialize app
app = FastAPI(title="AntarMan - Anonymous Mental Health Support")
APP_VERSION = "1.0.0"
APP_STARTED_AT = datetime.now(timezone.utc)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend (so the UI works from http://127.0.0.1:8000)
FRONTEND_DIR = (Path(__file__).resolve().parent.parent / "frontend").resolve()
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=False), name="frontend")

# Initialize services
emotion_service = EmotionService()
response_service = ResponseService()
emergency_service = EmergencyService()
modality_service = ModalityService()

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()


def generate_anon_id() -> str:
    """Generate anonymous user ID."""
    return f"anon-{uuid.uuid4().hex[:8]}"


@app.post("/api/process/text", response_model=ProcessResponse)
async def process_text(request: TextInputRequest):
    """Process text input and return emotion analysis with AI response."""
    try:
        # Generate anon_id if not provided
        anon_id = request.anon_id or generate_anon_id()

        # Detect emotion
        emotion_data = emotion_service.detect(request.text)

        # Generate response
        ai_response = response_service.generate(emotion_data, request.text)

        # Check for emergency
        is_emergency = emergency_service.detect(
            request.text,
            emotion_data["emotion_label"],
            emotion_data["intensity"]
        )

        emergency_info = None
        if is_emergency:
            emergency_info = emergency_service.build_message(request.country)

        # Save to database
        payload = {
            "anon_id": anon_id,
            "input_type": "text",
            "content_text": request.text,
            "emotion_label": emotion_data["emotion_label"],
            "intensity": emotion_data["intensity"],
            "ai_response": ai_response,
            "emergency_flag": is_emergency,
        }
        message_id = save_message(payload)

        return ProcessResponse(
            message_id=message_id,
            anon_id=anon_id,
            input_type="text",
            interpreted_text=request.text,
            emotion_label=emotion_data["emotion_label"],
            intensity=emotion_data["intensity"],
            ai_response=ai_response,
            emergency=is_emergency,
            emergency_info=emergency_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process/upload")
async def upload_file(
    file: UploadFile = File(...),
    country: str = "india",
    anon_id: Optional[str] = None
):
    """Upload and process audio, image, or video file."""
    import traceback
    print(f"Upload request: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    try:
        anon_id = anon_id or generate_anon_id()

        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Get file extension
        file_ext = Path(file.filename).suffix.lower()
        print(f"File extension: {file_ext}")
        
        # Validate file type
        audio_exts = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".flv"}

        all_valid_exts = audio_exts | image_exts | video_exts

        if file_ext not in all_valid_exts:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(sorted(all_valid_exts))}"
            )

        # Save file
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_path = UPLOAD_DIR / f"{anon_id}_{file.filename}"
        content = await file.read()
        file_path.write_bytes(content)
        print(f"File saved to: {file_path}")

        # Process based on type
        interpreted_text = ""
        input_type = "unknown"

        try:
            if file_ext in audio_exts:
                interpreted_text = modality_service.extract_text_from_audio(str(file_path))
                input_type = "audio"
            elif file_ext in image_exts:
                interpreted_text = modality_service.describe_image(str(file_path))
                input_type = "image"
            elif file_ext in video_exts:
                interpreted_text = modality_service.process_video(str(file_path))
                input_type = "video"
        except Exception as e:
            print(f"Error processing file: {e}")
            traceback.print_exc()
            interpreted_text = f"File received ({input_type}). Processing failed: {str(e)}"

        # Detect emotion from interpreted text
        emotion_data = emotion_service.detect(interpreted_text)
        print(f"Emotion detected: {emotion_data}")

        # Generate response
        ai_response = response_service.generate(emotion_data, interpreted_text)

        # Check for emergency
        is_emergency = emergency_service.detect(
            interpreted_text,
            emotion_data["emotion_label"],
            emotion_data["intensity"]
        )

        emergency_info = None
        if is_emergency:
            emergency_info = emergency_service.build_message(country)

        # Save to database
        payload = {
            "anon_id": anon_id,
            "input_type": input_type,
            "content_text": interpreted_text,
            "file_path": str(file_path),
            "emotion_label": emotion_data["emotion_label"],
            "intensity": emotion_data["intensity"],
            "ai_response": ai_response,
            "emergency_flag": is_emergency,
        }
        message_id = save_message(payload)
        print(f"Message saved with ID: {message_id}")

        return {
            "message_id": message_id,
            "anon_id": anon_id,
            "input_type": input_type,
            "interpreted_text": interpreted_text,
            "emotion_label": emotion_data["emotion_label"],
            "intensity": emotion_data["intensity"],
            "ai_response": ai_response,
            "emergency": is_emergency,
            "emergency_info": emergency_info
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception in upload_file: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload processing error: {str(e)}")


@app.post("/api/peer/posts")
async def create_post(request: PeerPostRequest):
    """Create a new peer support post."""
    try:
        anon_id = request.anon_id or generate_anon_id()
        post_id = create_peer_post(anon_id, request.message)
        return {
            "id": post_id,
            "anon_id": anon_id,
            "message": request.message,
            "created_at": "",
            "replies": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/peer/posts")
@app.get("/api/peer/feed")
async def get_posts():
    """Get all peer support posts with replies."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, anon_id, message, created_at FROM peer_posts ORDER BY id DESC")
        posts = cursor.fetchall()

        result = []
        for post in posts:
            post_id = post["id"]
            cursor.execute(
                "SELECT id, post_id, anon_id, message, created_at FROM peer_replies WHERE post_id = ? ORDER BY id DESC",
                (post_id,)
            )
            replies = [
                {
                    "id": r["id"],
                    "post_id": r["post_id"],
                    "anon_id": r["anon_id"],
                    "message": r["message"],
                    "created_at": r["created_at"]
                }
                for r in cursor.fetchall()
            ]

            result.append({
                "id": post["id"],
                "anon_id": post["anon_id"],
                "message": post["message"],
                "created_at": post["created_at"],
                "replies": replies
            })

        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/peer/posts/{post_id}/replies")
async def create_reply(post_id: int, request: PeerReplyRequest):
    """Reply to a peer support post."""
    try:
        anon_id = request.anon_id or generate_anon_id()
        conn = get_connection()
        cursor = conn.cursor()

        from datetime import datetime
        cursor.execute(
            "INSERT INTO peer_replies (post_id, anon_id, message, created_at) VALUES (?, ?, ?, ?)",
            (post_id, anon_id, request.message, datetime.utcnow().isoformat())
        )
        conn.commit()
        reply_id = cursor.lastrowid
        conn.close()

        return {
            "id": reply_id,
            "post_id": post_id,
            "anon_id": anon_id,
            "message": request.message,
            "created_at": ""
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", include_in_schema=False)
async def root():
    """Serve the frontend app."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse({"message": "AntarMan API is running"})


@app.get("/style.css", include_in_schema=False)
async def frontend_style():
    """Serve frontend stylesheet from project frontend directory."""
    css_path = FRONTEND_DIR / "style.css"
    if css_path.exists():
        return FileResponse(str(css_path))
    raise HTTPException(status_code=404, detail="style.css not found")


@app.get("/app.js", include_in_schema=False)
async def frontend_script():
    """Serve frontend script from project frontend directory."""
    js_path = FRONTEND_DIR / "app.js"
    if js_path.exists():
        return FileResponse(str(js_path))
    raise HTTPException(status_code=404, detail="app.js not found")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/meta")
async def app_meta():
    """Minimal launch metadata for status display and monitoring."""
    model_mode = "transformer" if getattr(emotion_service, "_classifier", None) is not None else "fallback"
    return {
        "name": "AntarMan",
        "version": APP_VERSION,
        "started_at_utc": APP_STARTED_AT.isoformat(),
        "model_mode": model_mode,
    }


@app.get("/api/stats/daily-mood")
async def get_daily_mood_stats(days: int = 7):
    """Get daily mood statistics for the past N days."""
    try:
        from datetime import datetime, timedelta
        conn = get_connection()
        cursor = conn.cursor()

        # Calculate the date from N days ago
        date_from = (datetime.utcnow() - timedelta(days=days)).date()

        cursor.execute(
            """
            SELECT 
                DATE(created_at) as day,
                emotion_label,
                COUNT(*) as total
            FROM messages
            WHERE DATE(created_at) >= ?
            GROUP BY DATE(created_at), emotion_label
            ORDER BY day, emotion_label
            """,
            (str(date_from),)
        )
        stats = [
            {
                "day": row["day"],
                "emotion_label": row["emotion_label"],
                "total": row["total"]
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
