"""Health Check Endpoint — Vercel Serverless Function."""

from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from src.cache.redis_client import health_check as redis_health
            from src.db.session import health_check as db_health
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            redis_ok = loop.run_until_complete(redis_health())
            db_ok = loop.run_until_complete(db_health())
            loop.close()
            status = 200 if (redis_ok and db_ok) else 503
            body = json.dumps({
                "status": "ok" if status == 200 else "degraded",
                "redis": redis_ok,
                "database": db_ok,
                "service": "yuklovchi_977",
            }).encode()
        except Exception as e:
            status = 503
            body = json.dumps({"status": "error", "error": str(e)}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()