"""FastAPI service for processing prompts
and filtering PII (Personally Identifiable Information)."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api import proxy
from src.views import main_view

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="PII FILTER",
    description="",
    version="0.1.0",
)

app.include_router(proxy.router, prefix="/api")
app.include_router(main_view.router)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
