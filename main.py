import os
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel, Field

load_dotenv()
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 30
DB_PATH = "notes.db"

app = FastAPI(title="NotAI")
password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------- Veritabanı ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


init_db()


# ---------- Şemalar ----------
class UserIn(BaseModel):
    email: str
    password: str = Field(min_length=8)


class NoteIn(BaseModel):
    title: str
    content: str


# ---------- Kimlik doğrulama ----------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn: sqlite3.Connection = Depends(get_conn),
):
    error = HTTPException(
        status_code=401,
        detail="Geçersiz veya süresi dolmuş token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise error
    row = conn.execute(
        "SELECT id, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        raise error
    return dict(row)


@app.post("/auth/register", status_code=201)
def register(user: UserIn, conn: sqlite3.Connection = Depends(get_conn)):
    email = user.email.strip().lower()
    try:
        cur = conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash.hash(user.password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")
    return {"id": cur.lastrowid, "email": email}


@app.post("/auth/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    conn: sqlite3.Connection = Depends(get_conn),
):
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (form.username.strip().lower(),)
    ).fetchone()
    if row is None or not password_hash.verify(form.password, row["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="E-posta veya parola hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    token = jwt.encode(
        {"sub": str(row["id"]), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


# ---------- Notlar (artık kullanıcıya bağlı) ----------
@app.post("/notes", status_code=201)
def create_note(
    note: NoteIn,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_conn),
):
    cur = conn.execute(
        "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
        (user["id"], note.title, note.content),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.get("/notes")
def list_notes(
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_conn),
):
    rows = conn.execute(
        "SELECT * FROM notes WHERE user_id = ? ORDER BY id DESC", (user["id"],)
    ).fetchall()
    return [dict(r) for r in rows]


@app.get("/notes/{note_id}")
def get_note(
    note_id: int,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_conn),
):
    row = conn.execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, user["id"])
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    return dict(row)


@app.put("/notes/{note_id}")
def update_note(
    note_id: int,
    note: NoteIn,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_conn),
):
    cur = conn.execute(
        "UPDATE notes SET title = ?, content = ? WHERE id = ? AND user_id = ?",
        (note.title, note.content, note_id, user["id"]),
    )
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(row)


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_conn),
):
    cur = conn.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user["id"])
    )
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not bulunamadı")