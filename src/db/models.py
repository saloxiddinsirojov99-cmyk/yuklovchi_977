"""SQLAlchemy ORM Models for PostgreSQL."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, String, Text, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc), nullable=True,
    )


class VideoMetadata(Base):
    __tablename__ = "video_metadata"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    telegram_file_unique_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    access_count: Mapped[int] = mapped_column(BigInteger, default=1)
    download_count: Mapped[int] = mapped_column(BigInteger, default=1)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    __table_args__ = (
        Index("idx_video_last_accessed", "last_accessed_at", "access_count"),
        Index("idx_video_created", "created_at"),
    )


class DownloadJob(Base):
    __tablename__ = "download_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    download_time_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    upload_time_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)