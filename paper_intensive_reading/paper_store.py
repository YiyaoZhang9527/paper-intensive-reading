"""阅读清单 / 进度 / 元数据 存储。"""
import sqlite3
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    arxiv_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    affiliations TEXT,
    abstract TEXT,
    published TEXT,
    pdf_path TEXT,
    note_path TEXT,
    status TEXT DEFAULT '待读',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sections_progress (
    arxiv_id TEXT,
    section_number TEXT,
    done INTEGER DEFAULT 0,
    PRIMARY KEY (arxiv_id, section_number)
);

CREATE TABLE IF NOT EXISTS formula_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT,
    formula_number TEXT,
    attempt INTEGER,
    passed INTEGER,
    feedback TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_state (
    arxiv_id TEXT PRIMARY KEY,
    depth_pref TEXT DEFAULT 'elementary',
    skipped_formulas TEXT,
    pending_questions TEXT
);
"""


def init_db(db_path: str | Path) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def add_paper(db_path: str | Path, meta: dict[str, Any]) -> None:
    init_db(db_path)  # 确保表存在
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO papers
            (arxiv_id, title, authors, affiliations, abstract, published, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                meta["arxiv_id"], meta["title"],
                json.dumps(meta.get("authors", [])),
                json.dumps(meta.get("affiliations", [])),
                meta.get("abstract", ""),
                meta["published"].isoformat() if isinstance(meta.get("published"), date) else str(meta.get("published", "")),
                meta.get("pdf_path", ""),
            ),
        )
        conn.commit()


def get_paper(db_path: str | Path, arxiv_id: str) -> dict | None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM papers WHERE arxiv_id = ?", (arxiv_id,)).fetchone()
    if not row:
        return None
    return {
        "arxiv_id": row["arxiv_id"], "title": row["title"],
        "authors": json.loads(row["authors"] or "[]"),
        "affiliations": json.loads(row["affiliations"] or "[]"),
        "abstract": row["abstract"], "published": row["published"],
        "pdf_path": row["pdf_path"], "note_path": row["note_path"],
        "status": row["status"], "added_at": row["added_at"],
        "finished_at": row["finished_at"],
    }


def list_papers(db_path: str | Path, status: str | None = None) -> list[dict]:
    with sqlite3.connect(str(db_path)) as conn:
        if status:
            rows = conn.execute("SELECT arxiv_id FROM papers WHERE status = ?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT arxiv_id FROM papers").fetchall()
    return [r[0] for r in rows]


def update_status(db_path: str | Path, arxiv_id: str, status: str) -> None:
    finished = datetime.now().isoformat() if status == "已读完" else None
    with sqlite3.connect(str(db_path)) as conn:
        if finished:
            conn.execute(
                "UPDATE papers SET status = ?, finished_at = ? WHERE arxiv_id = ?",
                (status, finished, arxiv_id),
            )
        else:
            conn.execute(
                "UPDATE papers SET status = ? WHERE arxiv_id = ?", (status, arxiv_id)
            )
        conn.commit()


def mark_section_done(db_path: str | Path, arxiv_id: str, section_number: str) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sections_progress (arxiv_id, section_number, done) VALUES (?, ?, 1)",
            (arxiv_id, section_number),
        )
        conn.commit()


def get_progress(db_path: str | Path, arxiv_id: str) -> dict:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT section_number FROM sections_progress WHERE arxiv_id = ? AND done = 1 ORDER BY section_number",
            (arxiv_id,),
        ).fetchall()
    sections = [r[0] for r in rows]
    return {
        "sections_done": sections,
        "count": len(sections),
        "percent": min(100, len(sections) * 10),  # 粗估：每节 10%
    }


def save_note_path(db_path: str | Path, arxiv_id: str, note_path: str) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("UPDATE papers SET note_path = ? WHERE arxiv_id = ?", (note_path, arxiv_id))
        conn.commit()
