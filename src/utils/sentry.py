"""Sentry Error Tracking — Production error monitoring."""

from __future__ import annotations

import os
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy import to avoid crash if sentry not installed
_sentry_initialized = False


def init_sentry(dsn: Optional[str] = None) -> None:
    """Initialize Sentry SDK if DSN is configured."""
    global _sentry_initialized
    if _sentry_initialized:
        return
    
    dsn = dsn or os.environ.get("SENTRY_DSN")
    if not dsn:
        logger.info("Sentry not configured (no SENTRY_DSN)")
        return
    
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            enable_tracing=True,
        )
        _sentry_initialized = True
        logger.info("Sentry initialized")
    except ImportError:
        logger.warning("sentry_sdk not installed, skipping Sentry")


def capture_exception(error: Exception, context: Optional[dict] = None) -> None:
    """Capture an exception to Sentry."""
    if not _sentry_initialized:
        return
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            sentry_sdk.capture_exception(error)
    except Exception:
        pass