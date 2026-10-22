from fastapi import FastAPI
from app.routers import auth, notes

app = FastAPI(title="NotAI")
app.include_router(auth.router)
app.include_router(notes.router)