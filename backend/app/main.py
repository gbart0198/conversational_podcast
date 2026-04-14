import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routes import interact as interact_router
from .routes import talks as talks_router

AUDIO_DIR = os.getenv("AUDIO_DIR", "./data/audio")

app = FastAPI(
    title="Conversational Podcast API",
    description="Generate and interact with AI-powered podcast episodes.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    os.makedirs(AUDIO_DIR, exist_ok=True)
    init_db()


# Mount audio files for static serving
os.makedirs(AUDIO_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

# Register routes
app.include_router(talks_router.router, prefix="/api/talks", tags=["talks"])
app.include_router(interact_router.router, prefix="/api/talks", tags=["interact"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
