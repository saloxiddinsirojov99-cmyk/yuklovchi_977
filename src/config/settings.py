"""Application Configuration — Vercel + Railway compatible."""

from __future__ import annotations

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Telegram ---
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    # --- Redis (Cloud: Upstash) ---
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # --- PostgreSQL (Cloud: Neon/Supabase) ---
    database_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/video_downloader",
        alias="DATABASE_URL",
    )

    # --- Bot Settings ---
    max_file_size_bytes: int = Field(2_147_483_648, alias="MAX_FILE_SIZE_BYTES")
    cache_ttl_seconds: int = Field(604_800, alias="CACHE_TTL_SECONDS")
    worker_concurrency: int = Field(4, alias="WORKER_CONCURRENCY")

    # --- Webhook ---
    webhook_url: Optional[str] = Field(None, alias="WEBHOOK_URL")
    webhook_secret: Optional[str] = Field(None, alias="WEBHOOK_SECRET")

    # --- Rate Limit ---
    telegram_rate_limit_per_second: int = Field(30, alias="TELEGRAM_RATE_LIMIT_PER_SECOND")

    # --- Prometheus ---
    prometheus_port: int = Field(8000, alias="PROMETHEUS_PORT")

    # --- Sentry ---
    sentry_dsn: Optional[str] = Field(None, alias="SENTRY_DSN")

    @field_validator("telegram_bot_token", mode="before")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v or v == "YOUR_BOT_TOKEN_HERE":
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        return v.strip()


settings = AppSettings()