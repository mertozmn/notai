import sqlite3
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = "notes.db"
app = FastAPI(title="NotAI")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


class NoteIn(BaseModel):
    title: str
    content: str


@app.post("/notes", status_code=201)
def create_note(note: NoteIn, conn: sqlite3.Connection = Depends(get_conn)):
    cur = conn.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (note.title, note.content),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.get("/notes")
def list_notes(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


@app.get("/notes/{note_id}")
def get_note(note_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    return dict(row)


@app.put("/notes/{note_id}")
def update_note(note_id: int, note: NoteIn, conn: sqlite3.Connection = Depends(get_conn)):
    cur = conn.execute(
        "UPDATE notes SET title = ?, content = ? WHERE id = ?",
        (note.title, note.content, note_id),
    )
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(row)


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, conn: sqlite3.Connection = Depends(get_conn)):
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not bulunamadı")