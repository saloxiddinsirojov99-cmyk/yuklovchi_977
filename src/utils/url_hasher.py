"""URL Canonicalization & Hashing — SHA256 of normalized URL."""

from __future__ import annotations

import hashlib
import re
import urllib.parse
from src.common.constants import VideoSource
from src.utils.url_detector import detect_source


def canonical_url(url: str) -> str:
    url = url.strip().rstrip("/")
    source = detect_source(url)
    if source == VideoSource.YOUTUBE:
        parsed = urllib.parse.urlparse(url)
        if "youtu.be" in parsed.netloc:
            vid = parsed.path.strip("/").split("/")[0]
            return f"https://youtube.com/watch?v={vid}"
        q = urllib.parse.parse_qs(parsed.query)
        vid = q.get("v", [None])[0]
        if vid:
            return f"https://youtube.com/watch?v={vid}"
        return url
    if source == VideoSource.INSTAGRAM:
        m = re.search(r"instagram\.com/(?:p|reel|tv)/([\w-]+)", url)
        if m:
            return f"https://instagram.com/{'reel' if '/reel/' in url else 'p'}/{m.group(1)}"
    if source == VideoSource.TWITTER:
        m = re.search(r"(?:twitter|x)\.com/\w+/status/(\d+)", url)
        if m:
            username = re.search(r"(?:twitter|x)\.com/(\w+)", url).group(1)
            return f"https://twitter.com/{username}/status/{m.group(1)}"
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")


def url_hash(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()


def get_dedup_key(url_hash_val: str) -> str:
    return f"dedup:{url_hash_val}"