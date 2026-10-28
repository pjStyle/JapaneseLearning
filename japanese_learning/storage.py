import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4
from .config import DB_PATH, MODEL_REVISION, PROMPT_VERSION


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path=DB_PATH):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS exercises (
                id TEXT PRIMARY KEY, created_at TEXT NOT NULL, words TEXT NOT NULL,
                level TEXT NOT NULL, english TEXT NOT NULL,
                model_revision TEXT NOT NULL, prompt_version TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY, exercise_id TEXT NOT NULL REFERENCES exercises(id),
                created_at TEXT NOT NULL, answer TEXT NOT NULL, status TEXT NOT NULL,
                feedback TEXT, error TEXT, model_revision TEXT NOT NULL, prompt_version TEXT NOT NULL);
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(exercises)")}
            if "input_language" not in columns:
                db.execute("ALTER TABLE exercises ADD COLUMN input_language TEXT NOT NULL DEFAULT 'en'")
            if "targets" not in columns:
                db.execute("ALTER TABLE exercises ADD COLUMN targets TEXT NOT NULL DEFAULT '[]'")
            # A single app process owns the database; recover interrupted requests after restart.
            db.execute("UPDATE attempts SET status='failed', error='Assessment was interrupted. Reopen the exercise and submit again.' WHERE status='pending'")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_exercise(self, words, level, english, targets=None):
        key = uuid4().hex
        with self.connect() as db:
            db.execute("""INSERT INTO exercises
                       (id,created_at,words,level,english,model_revision,prompt_version,input_language,targets)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                       (key, now(), json.dumps(words, ensure_ascii=False), level, english, MODEL_REVISION,
                        PROMPT_VERSION, "ja" if targets is not None else "en",
                        json.dumps(targets or [], ensure_ascii=False)))
        return self.exercise(key)

    def exercise(self, key):
        with self.connect() as db:
            row = db.execute("SELECT * FROM exercises WHERE id=?", (key,)).fetchone()
        if row is None:
            raise ValueError("Exercise not found. Generate a new exercise.")
        return dict(row)

    def start_attempt(self, exercise_id, answer):
        key = uuid4().hex
        with self.connect() as db:
            db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?)",
                       (key, exercise_id, now(), answer, "pending", None, None, MODEL_REVISION, PROMPT_VERSION))
        return key

    def finish(self, key, feedback=None, error=None):
        with self.connect() as db:
            db.execute("UPDATE attempts SET status=?,feedback=?,error=? WHERE id=?",
                       ("failed" if error else "complete", feedback.model_dump_json() if feedback else None, error, key))

    def history(self):
        with self.connect() as db:
            rows = db.execute("""SELECT e.id AS exercise_id,e.created_at AS exercise_created_at,
                e.level,e.english,e.words,e.input_language,e.targets,a.id AS attempt_id,a.created_at,a.answer,a.status,a.feedback,a.error
                FROM exercises e LEFT JOIN attempts a ON e.id=a.exercise_id
                ORDER BY COALESCE(a.created_at,e.created_at) DESC""").fetchall()
        return [dict(row) for row in rows]
