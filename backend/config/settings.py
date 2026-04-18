"""
Application configuration — loaded from environment variables.
All secrets must live in .env; never hardcode.
"""

import json
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[
            str(PROJECT_ROOT / ".env.local"),  # Load .env.local first (dev)
            str(PROJECT_ROOT / ".env"),        # Then .env (fallback)
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://safeguard.ai"]

    # ── MongoDB ──────────────────────────────────────────────────
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "safeguard_ai"

    # ── Cloudinary ───────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── Redis / Celery ───────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── HuggingFace ──────────────────────────────────────────────
    HF_MODEL_NAME: str = "unitary/toxic-bert"
    HF_CACHE_DIR: str = "/tmp/hf_cache"
    HF_DEVICE: str = "cpu"   # "cuda" if GPU available

    # ── Grooming model ───────────────────────────────────────────
    GROOMING_MODEL: str = "models/grooming_classifier"

    # ── File upload ──────────────────────────────────────────────
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # ── FIR PDF output dir ───────────────────────────────────────
    FIR_OUTPUT_DIR: str = "/tmp/fir_pdfs"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value


settings = Settings()
