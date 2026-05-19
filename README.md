## Anonymous AI-Based Mental Health Support Platform

A privacy-focused full-stack project where users can anonymously share feelings using text, audio, image, or video.  
The app detects emotion + intensity, generates empathetic support, raises emergency guidance when needed, and includes an anonymous peer support board.

## Project Structure

```text
backend/
  main.py
  db.py
  config.py
  schemas.py
  services/
frontend/
  index.html
  style.css
  app.js
models/
utils/
database/
requirements.txt
README.md
```

## Core Features Implemented

1. Multi-modal input support:
   - Text input
   - Audio upload + speech-to-text (using `SpeechRecognition`, fallback message if unavailable)
   - Image upload + captioning (`transformers` BLIP pipeline when available)
   - Video upload + basic demo analysis hook (extensible)

2. AI emotion detection:
   - Pretrained transformer classifier (`j-hartmann/emotion-english-distilroberta-base`) when available
   - Fallback keyword-based classifier if model loading fails
   - Emotions: stress, anxiety, sadness, happiness, anger, neutral
   - Intensity: Low / Medium / High

3. AI response system:
   - Rule-based empathetic response templates
   - Intensity-aware response adjustments

4. Emergency detection:
   - Harmful intent keyword detection
   - High-intensity distress detection
   - Helpline suggestions by country (India/USA/UK/default)

5. Anonymity system:
   - Random anonymous ID generation (`anon-xxxxxxxx`)
   - No login required
   - No personal identity fields stored

6. Peer support board:
   - Anonymous posts
   - Anonymous replies
   - Recent feed API

8. Moderation and profanity safety:
   - Unsafe/toxic text blocking for peer board and text input
   - Profanity masking for mild cases

9. Daily mood trend chart:
   - Line chart of emotion counts (last 7 days)
   - Backend stats endpoint + frontend Chart.js visualization

7. Database (SQLite):
   - Stores messages, emotion labels, anonymous IDs
   - Stores peer posts and replies

## API Endpoints

- `POST /api/process/text` - Analyze text input
- `POST /api/process/upload` - Analyze audio/image/video upload
- `POST /api/peer/posts` - Create peer post
- `POST /api/peer/posts/{post_id}/replies` - Reply to post
- `GET /api/peer/feed` - Fetch feed
- `GET /api/stats/daily-mood?days=7` - Daily emotion trend data

## Setup & Run (Step by Step)

1. Open terminal in project root.
2. Create virtual environment:
   - Windows: `python -m venv .venv`
3. Activate virtual environment:
   - PowerShell: `.venv\\Scripts\\Activate.ps1`
4. Install dependencies:
   - `pip install -r requirements.txt`
5. Start backend server:
   - Stable mode: `uvicorn backend.main:app --host 127.0.0.1 --port 8000`
   - Dev auto-reload mode: `uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`
6. Open in browser:
   - [http://127.0.0.1:8000](http://127.0.0.1:8000)

### One-command Windows launch

- Run: `.\run.ps1`
- The script creates/uses `venv`, installs dependencies, opens the browser, and starts the backend.

## How Modules Work

- `backend/main.py`:
  - FastAPI app and routes
  - Handles input submission and upload APIs
  - Integrates all services (emotion, response, emergency, modality)
- `backend/services/emotion_service.py`:
  - Runs transformer emotion model (or fallback classifier)
  - Maps score to emotion + intensity
- `backend/services/response_service.py`:
  - Creates empathetic response text using templates + intensity
- `backend/services/emergency_service.py`:
  - Detects crisis signals and returns country-specific helplines
- `backend/services/modality_service.py`:
  - Audio transcription
  - Image captioning
  - Video placeholder pipeline
- `backend/db.py`:
  - SQLite table setup and CRUD helpers
- `frontend/*`:
  - User UI for text/upload + peer board actions

## Sample Inputs and Outputs

### 1) Text Analysis
- Input: `I feel very alone and anxious these days`
- Example Output:
  - Emotion: `sadness` or `anxiety`
  - Intensity: `Medium`
  - AI message: `I'm really sorry you're feeling this way...`

### 2) Emergency Case
- Input: `I want to hurt myself`
- Example Output:
  - Emergency: `true`
  - Emergency message + helplines displayed

### 3) Peer Support
- Input post: `Today was difficult, I feel stressed`
- Reply from another anonymous user: `You are not alone. Take it one step at a time.`

## Notes

- This is an educational demo project, not a replacement for professional mental health care.
- For production, add stronger moderation, rate limiting, abuse prevention, and secure media processing.

