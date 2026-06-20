"""Start Bot — Vercel Serverless Function. Sets Telegram webhook."""

from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler
from src.config.settings import settings
from src.utils.logger import get_logger
from telegram.ext import Application, ApplicationBuilder

logger = get_logger(__name__)


async def set_webhook(webhook_url: str) -> dict:
    app = ApplicationBuilder().token(settings.telegram_bot_token).build()
    async with app:
        success = await app.bot.set_webhook(url=webhook_url)
        webhook_info = await app.bot.get_webhook_info()
        return {
            "ok": success,
            "webhook_url": webhook_info.url,
            "pending_update_count": webhook_info.pending_update_count,
        }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            vercel_url = self.headers.get("X-Forwarded-Host", "localhost")
            webhook_url = f"https://{vercel_url}/webhook"
            result = loop.run_until_complete(set_webhook(webhook_url))
            body = json.dumps(result).encode()
            self.send_response(200)
        except Exception as e:
            body = json.dumps({"ok": False, "error": str(e)}).encode()
            self.send_response(500)
        finally:
            loop.close()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)