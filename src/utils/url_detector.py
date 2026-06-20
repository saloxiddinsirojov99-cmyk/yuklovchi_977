"""URL Detection — identify video source platform."""

from __future__ import annotations

import re
from src.common.constants import VideoSource

PATTERNS: dict[VideoSource, list[re.Pattern[str]]] = {
    VideoSource.YOUTUBE: [
        re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+"),
        re.compile(r"(?:https?://)?(?:www\.)?youtu\.be/[\w-]+"),
        re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+"),
    ],
    VideoSource.TWITTER: [
        re.compile(r"(?:https?://)?(?:www\.)?(?:twitter|x)\.com/\w+/status/\d+"),
    ],
    VideoSource.FACEBOOK: [
        re.compile(r"(?:https?://)?(?:www\.)?facebook\.com/.+/videos/.+"),
        re.compile(r"(?:https?://)?(?:www\.)?fb\.watch/.+"),
    ],
    VideoSource.TIKTOK: [
        re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@[\w.]+/video/\d+"),
        re.compile(r"(?:https?://)?vm\.tiktok\.com/[\w]+"),
    ],
    VideoSource.INSTAGRAM: [
        re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|tv)/[\w-]+"),
    ],
    VideoSource.REDDIT: [
        re.compile(r"(?:https?://)?(?:www\.)?reddit\.com/r/\w+/comments/[\w-]+"),
    ],
    VideoSource.VIMEO: [
        re.compile(r"(?:https?://)?(?:www\.)?vimeo\.com/\d+"),
    ],
}


def detect_source(url: str) -> VideoSource:
    url = url.strip()
    for source, patterns in PATTERNS.items():
        for pattern in patterns:
            if pattern.fullmatch(url):
                return source
    return VideoSource.UNKNOWN


def is_supported_url(url: str) -> bool:
    return detect_source(url) != VideoSource.UNKNOWN