"""Telegram Webhook Handler — Vercel Serverless Function."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Dict

from http.server import BaseHTTPRequestHandler
from src.cache.redis_client import get_redis
from src.cache.video_cache import VideoCacheService
from src.common.constants import DEDUP_LOCK_TTL_SEC, REDIS_DEDUP_PREFIX
from src.config.settings import settings
from src.db.session import init_db
from src.utils.logger import get_logger
from src.utils.url_hasher import canonical_url, url_hash, get_dedup_key
from src.utils.url_detector import detect_source, is_supported_url
from telegram import Update
from telegram.ext import Application, ApplicationBuilder

logger = get_logger(__name__)
_app: Application | None = None


async def get_bot_app() -> Application:
    global _app
    if _app is None:
        _app = (
            ApplicationBuilder()
            .token(settings.telegram_bot_token)
            .concurrent_updates(True)
            .build()
        )
        await _app.initialize()
    return _app


async def handle_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming Telegram webhook update."""
    try:
        update = Update.de_json(payload, await get_bot_app().bot)
        if not update.message or not update.message.text:
            return {"ok": True, "handled": False}

        text = update.message.text.strip()
        chat_id = update.message.chat_id
        message_id = update.message.message_id

        if text.startswith("/start"):
            await update.message.reply_text(
                "🎬 yuklovchi_977 Bot\n\nSend a video URL to download.\n"
                "Supported: YouTube, Twitter, Facebook, TikTok, Instagram, Reddit, Vimeo"
            )
            return {"ok": True}

        if not text.startswith(("http://", "https://")):
            await update.message.reply_text("Please send a valid video URL.")
            return {"ok": True}

        canonical = canonical_url(text)
        h = url_hash(text)

        if not is_supported_url(canonical):
            await update.message.reply_text("❌ Unsupported URL.")
            return {"ok": True}

        # Check cache
        cache = VideoCacheService()
        cached = await cache.get_file_id(h)
        if cached:
            await update.message.reply_video(video=cached, supports_streaming=True)
            return {"ok": True, "cached": True}

        # Check dedup
        redis = get_redis()
        dedup_key = get_dedup_key(h)
        existing = await redis.get(dedup_key)
        if existing:
            await update.message.reply_text("⏳ Already being downloaded...")
            return {"ok": True, "dedup": True}

        # Enqueue
        job_id = str(uuid.uuid4())
        await redis.setex(dedup_key, DEDUP_LOCK_TTL_SEC, job_id)
        job = {"job_id": job_id, "url": text, "url_hash": h, "source": detect_source(canonical).value, "chat_id": chat_id, "message_id": message_id}
        await redis.lpush("queue:downloads", json.dumps(job, default=str))
        await update.message.reply_text("⏳ Queued for download. I'll send it shortly.")
        return {"ok": True, "queued": True}

    except Exception as e:
        logger.exception("Webhook error")
        return {"ok": False, "error": str(e)}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        payload = json.loads(body)
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(init_db())
            result = loop.run_until_complete(handle_webhook(payload))
            response = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response)
        finally:
            loop.close()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "service": "webhook"}).encode())