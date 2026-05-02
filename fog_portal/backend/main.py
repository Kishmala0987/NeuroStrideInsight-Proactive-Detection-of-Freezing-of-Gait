"""
FOG Analysis Portal — FastAPI Backend
Entry point: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .db.database import init_db
from .models.loader import registry
from .routers import upload, sessions, subjects, statistics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    print("[Startup] Initializing database...")
    init_db()
    print("[Startup] Database ready.")

    print("[Startup] Loading ML models...")
    try:
        registry.load()
    except FileNotFoundError as e:
        print(f"[Startup] WARNING: {e}")
        print("[Startup] Server will start but /api/upload will return 503 until models are placed.")

    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    print("[Shutdown] Bye.")


app = FastAPI(
    title="FOG Analysis Portal",
    description="Freezing of Gait clinical analysis portal — REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow React dev server on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(upload.router)
app.include_router(sessions.router)
app.include_router(subjects.router)
app.include_router(statistics.router)


@app.get("/api/health")
def health():
    return {
        "status":        "ok",
        "models_loaded": registry.is_ready(),
        "device":        str(registry.device) if registry.is_ready() else "not loaded",
    }
