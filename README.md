# yuklovchi_977 — Telegram Video Downloader Bot

Production-ready Telegram bot for downloading videos from YouTube, Twitter/X, Facebook, TikTok, Instagram, Reddit, and Vimeo.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Vercel    │────▶│  Redis Queue  │────▶│  Railway Worker  │
│  API Layer  │     │ download/    │     │                  │
│             │     │ upload/DLQ   │     │  yt-dlp → Telegram│
└─────────────┘     └──────────────┘     └─────────────────┘
       │                    │                       │
       ▼                    ▼                       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  PostgreSQL  │     │   Redis      │     │  Telegram Bot   │
│  Metadata   │     │  video:hash  │     │                  │
└─────────────┘     └──────────────┘     └─────────────────┘
```

## Deployment

### 1. Vercel (Webhook API)

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd yuklovchi_977
vercel --prod

# Set environment variables
vercel secrets add TELEGRAM_BOT_TOKEN your_token
vercel secrets add REDIS_URL redis://...
vercel secrets add DATABASE_URL postgresql+asyncpg://...

# Register webhook
curl https://your-app.vercel.app/start-bot
```

### 2. Railway (Download + Upload Workers)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy workers
railway up

# Set env vars in Railway dashboard:
# TELEGRAM_BOT_TOKEN, REDIS_URL, DATABASE_URL
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | From @BotFather |
| `REDIS_URL` | ✅ | Upstash Redis URL |
| `DATABASE_URL` | ✅ | Neon/Supabase PostgreSQL URL |
| `MAX_FILE_SIZE_BYTES` | ❌ | Default: 2GB |
| `CACHE_TTL_SECONDS` | ❌ | Default: 7 days |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook` | POST | Telegram update handler |
| `/health` | GET | Health check (Redis + DB) |
| `/start-bot` | GET | Register webhook with Telegram |
| `/queue-status` | GET | Queue lengths |

## Features

- ✅ Webhook architecture (Vercel-compatible)
- ✅ Cloud Redis (Upstash) — no localhost
- ✅ Cloud PostgreSQL (Neon/Supabase)
- ✅ URL normalization + SHA256 hashing
- ✅ Redis caching (7-day TTL)
- ✅ In-flight deduplication
- ✅ Failure cache (10-min TTL)
- ✅ Async workers (Railway)
- ✅ Per-user rate limiting
- ✅ Health check endpoints
- ✅ Prometheus metrics
- ✅ Structured JSON logging
- ✅ yt-dlp video download
- ✅ Streaming upload to Telegram

## Flow

1. User sends video URL to Telegram bot
2. Vercel webhook receives update
3. URL normalized + hashed → Redis cache check
4. Cache hit → instant reply with `send_video(file_id)`
5. Cache miss → dedup check → enqueue download job
6. Railway worker downloads via yt-dlp → enqueue upload job
7. Railway worker uploads to Telegram → saves file_id to cache
8. Same URL next time → instant cache hit (50-300ms)