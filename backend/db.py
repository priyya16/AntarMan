import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import DATABASE_PATH, UPLOAD_DIR


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anon_id TEXT NOT NULL,
            input_type TEXT NOT NULL,
            content_text TEXT,
            file_path TEXT,
            emotion_label TEXT,
            intensity TEXT,
            ai_response TEXT,
            emergency_flag INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anon_id TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            anon_id TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(post_id) REFERENCES peer_posts(id)
        )
        """
    )
    conn.commit()
    conn.close()


def save_message(payload: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (
            anon_id, input_type, content_text, file_path, emotion_label, intensity,
            ai_response, emergency_flag, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["anon_id"],
            payload["input_type"],
            payload.get("content_text"),
            payload.get("file_path"),
            payload.get("emotion_label"),
            payload.get("intensity"),
            payload.get("ai_response"),
            int(payload.get("emergency_flag", False)),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return int(row_id)


def create_peer_post(anon_id: str, message: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO peer_posts (anon_id, message, created_at) VALUES (?, ?, ?)",
        (anon_id, message, datetime.utcnow().isoformat()),
    )
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return int(post_id)


def create_peer_reply(post_id: int, anon_id: str, message: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO peer_replies (post_id, anon_id, message, created_at) VALUES (?, ?, ?, ?)",
        (post_id, anon_id, message, datetime.utcnow().isoformat()),
    )
    conn.commit()
    reply_id = cursor.lastrowid
    conn.close()
    return int(reply_id)


def get_peer_feed() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    posts = cursor.execute(
        "SELECT id, anon_id, message, created_at FROM peer_posts ORDER BY id DESC LIMIT 30"
    ).fetchall()

    feed: List[Dict[str, Any]] = []
    for post in posts:
        replies = cursor.execute(
            """
            SELECT id, post_id, anon_id, message, created_at
            FROM peer_replies WHERE post_id = ? ORDER BY id ASC
            """,
            (post["id"],),
        ).fetchall()
        feed.append(
            {
                "id": post["id"],
                "anon_id": post["anon_id"],
                "message": post["message"],
                "created_at": post["created_at"],
                "replies": [dict(reply) for reply in replies],
            }
        )
    conn.close()
    return feed


def get_message(message_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_daily_mood_stats(days: int = 7) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT date(created_at) AS day, emotion_label, COUNT(*) AS total
        FROM messages
        WHERE created_at >= datetime('now', ?)
        GROUP BY day, emotion_label
        ORDER BY day ASC
        """,
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
