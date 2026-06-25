import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.db import init_db, seed_prompts
from app.routers import register_routers

def check_ffmpeg():
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("ffmpeg not found! Please install ffmpeg before running the server.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    check_ffmpeg()
    init_db()
    seed_prompts()
    yield

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Technosprint 2026", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_routers(app)