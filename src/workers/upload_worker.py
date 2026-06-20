"""Upload Worker for Railway — uploads videos to Telegram via Bot API."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from src.cache.redis_client import get_redis
from src.cache.video_cache import VideoCacheService
from src.common.constants import REDIS_QUEUE_UPLOAD
from src.config.settings import settings
from src.utils.logger import get_logger
from telegram import InputFile
from telegram.ext import Application, ApplicationBuilder

logger = get_logger(__name__)
_app: Application | None = None


async def get_app() -> Application:
    global _app
    if _app is None:
        _app = ApplicationBuilder().token(settings.telegram_bot_token).concurrent_updates(True).build()
        await _app.initialize()
    return _app


async def process_upload_job(job_data: dict) -> None:
    """Upload a video file to Telegram, save file_id to cache."""
    file_path = Path(job_data["file_path"])
    url_hash_val = job_data["url_hash"]
    chat_id = job_data["chat_id"]
    message_id = job_data.get("message_id")
    url = job_data["url"]

    if not file_path.exists():
        logger.error("File not found", extra={"path": str(file_path)})
        return

    try:
        app = await get_app()
        bot = app.bot
        file_size = file_path.stat().st_size

        # Rate limit: simple 30 req/sec throttle
        await asyncio.sleep(0.034)  # ~30 req/sec

        with open(file_path, "rb") as f:
            msg = await bot.send_video(
                chat_id=chat_id,
                video=InputFile(f, filename=file_path.name),
                supports_streaming=True,
                read_timeout=300,
                write_timeout=300,
            )

        if msg and msg.video:
            file_id = msg.video.file_id
            cache = VideoCacheService()
            await cache.set(url_hash_val, file_id, file_size=file_size)
            await cache._redis.delete(f"dedup:{url_hash_val}")
            logger.info("Upload done", extra={"hash": url_hash_val[:12], "file_id": file_id[:20]})
        else:
            logger.error("Upload failed: no file_id")

        file_path.unlink(missing_ok=True)

    except Exception as e:
        logger.exception("Upload error", extra={"hash": url_hash_val[:12]})


async def run_worker() -> None:
    """Main loop: poll upload queue, process jobs."""
    logger.info("Upload worker started")
    redis = get_redis()
    while True:
        try:
            result = await redis.brpop(REDIS_QUEUE_UPLOAD, timeout=30)
            if result is None:
                continue
            _, payload = result
            job = json.loads(payload)
            await process_upload_job(job)
        except Exception:
            logger.exception("Upload worker error")
            await asyncio.sleep(1)


if __name__ == "__main__":
    from src.cache.redis_client import init_redis
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_redis())
    loop.run_until_complete(run_worker())