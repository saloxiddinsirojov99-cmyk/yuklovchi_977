"""Download Worker for Railway — processes download queue from Redis."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

from src.cache.redis_client import get_redis
from src.cache.video_cache import VideoCacheService
from src.common.constants import REDIS_QUEUE_DOWNLOAD, REDIS_QUEUE_UPLOAD, DEDUP_LOCK_TTL_SEC
from src.config.settings import settings
from src.utils.logger import get_logger
from src.utils.url_hasher import url_hash
import yt_dlp

logger = get_logger(__name__)
DOWNLOAD_DIR = Path("downloads")


async def process_download_job(job_data: dict) -> None:
    """Download a video using yt-dlp, then enqueue upload job."""
    url = job_data["url"]
    url_hash_val = job_data["url_hash"]
    chat_id = job_data["chat_id"]
    message_id = job_data.get("message_id")
    job_id = job_data["job_id"]

    logger.info("Starting download", extra={"job_id": job_id, "url": url[:60]})
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    try:
        loop = asyncio.get_event_loop()
        output_template = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "max_filesize": settings.max_file_size_bytes,
            "retries": 3,
        }

        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        result = await loop.run_in_executor(None, download)
        ext = result.get("ext", "mp4")
        video_id = result.get("id", "unknown")
        file_path = DOWNLOAD_DIR / f"{video_id}.{ext}"
        if not file_path.exists():
            for f in DOWNLOAD_DIR.iterdir():
                if f.stem == video_id:
                    file_path = f
                    break

        file_size = file_path.stat().st_size
        upload_job = {
            "job_id": job_id,
            "url": url,
            "url_hash": url_hash_val,
            "file_path": str(file_path),
            "file_size": file_size,
            "chat_id": chat_id,
            "message_id": message_id,
            "source": job_data.get("source", "unknown"),
            "title": result.get("title"),
            "duration": result.get("duration"),
        }
        redis = get_redis()
        await redis.lpush(REDIS_QUEUE_UPLOAD, json.dumps(upload_job, default=str))
        logger.info("Download complete, upload queued", extra={"job_id": job_id})

    except Exception as e:
        logger.exception("Download failed", extra={"job_id": job_id, "url": url[:60]})
        redis = get_redis()
        failed_key = f"failed:{url_hash_val}"
        await redis.setex(failed_key, 600, json.dumps({"error": str(e)[:200]}))


async def run_worker() -> None:
    """Main loop: poll download queue, process jobs."""
    logger.info("Download worker started")
    redis = get_redis()
    while True:
        try:
            result = await redis.brpop(REDIS_QUEUE_DOWNLOAD, timeout=30)
            if result is None:
                continue
            _, payload = result
            job = json.loads(payload)
            await process_download_job(job)
        except Exception:
            logger.exception("Worker loop error")
            await asyncio.sleep(1)


if __name__ == "__main__":
    from src.cache.redis_client import init_redis
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_redis())
    loop.run_until_complete(run_worker())