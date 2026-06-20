"""Queue Status Endpoint — Shows pending download/upload counts."""

from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler
from src.cache.redis_client import get_redis, init_redis
from src.common.constants import REDIS_QUEUE_DOWNLOAD, REDIS_QUEUE_UPLOAD, REDIS_QUEUE_DLQ


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(init_redis())
            redis = get_redis()
            dl = loop.run_until_complete(redis.llen(REDIS_QUEUE_DOWNLOAD))
            ul = loop.run_until_complete(redis.llen(REDIS_QUEUE_UPLOAD))
            dlq = loop.run_until_complete(redis.llen(REDIS_QUEUE_DLQ))
            body = json.dumps({
                "download_queue": dl,
                "upload_queue": ul,
                "dead_letter_queue": dlq,
                "total_pending": dl + ul,
            }).encode()
            self.send_response(200)
        except Exception as e:
            body = json.dumps({"error": str(e)}).encode()
            self.send_response(500)
        finally:
            loop.close()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)