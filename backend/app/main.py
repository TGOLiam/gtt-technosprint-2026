from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db, seed_prompts
from app.routers import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_prompts()
    yield


app = FastAPI(title="Technosprint 2026", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routers(app)
