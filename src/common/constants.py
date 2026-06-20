"""Shared constants for yuklovchi_977."""

from enum import Enum


class VideoSource(str, Enum):
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    VIMEO = "vimeo"
    UNKNOWN = "unknown"


REDIS_CACHE_PREFIX = "video:"
REDIS_FAILED_PREFIX = "failed:"
REDIS_DEDUP_PREFIX = "dedup:"
REDIS_QUEUE_DOWNLOAD = "queue:downloads"
REDIS_QUEUE_UPLOAD = "queue:uploads"
REDIS_QUEUE_DLQ = "queue:dead_letter"
CACHE_DEFAULT_TTL_SEC = 604800
FAILED_CACHE_TTL_SEC = 600
DEDUP_LOCK_TTL_SEC = 600