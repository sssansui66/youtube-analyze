import os
import sys
import argparse
import json
from urllib.parse import urlparse, parse_qs
import requests
import isodate


def parse_video_id(url: str) -> str | None:
    u = urlparse(url)
    host = u.netloc.replace("www.", "")
    if host in ("youtube.com", "m.youtube.com"):
        if u.path == "/watch":
            return parse_qs(u.query).get("v", [None])[0]
        if u.path.startswith("/shorts/"):
            return u.path.split("/shorts/")[1].split("/")[0]
        if u.path.startswith("/live/"):
            return u.path.split("/live/")[1].split("/")[0]
    if host == "youtu.be":
        return u.path.strip("/").split("/")[0] or None
    return None


def fmt_hms(total_seconds: int | None) -> str | None:
    if total_seconds is None:
        return None
    s = int(total_seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"


def fetch_api(video_id: str, api_key: str) -> dict:
    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=snippet,contentDetails,statistics&id={video_id}&key={api_key}"
    )
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    if not items:
        raise SystemExit("No video found or not accessible")
    item = items[0]
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})
    dur_iso = details.get("duration")
    dur_seconds = None
    if dur_iso:
        try:
            dur_seconds = int(isodate.parse_duration(dur_iso).total_seconds())
        except Exception:
            dur_seconds = None
    published_at = snippet.get("publishedAt")
    return {
        "videoId": video_id,
        "url": f"https://youtu.be/{video_id}",
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "publishedAt": published_at,
        "publishedDate": (published_at.split('T')[0] if isinstance(published_at, str) and 'T' in published_at else published_at),
        "durationSeconds": dur_seconds,
        "durationText": fmt_hms(dur_seconds),
        "viewCount": int(stats.get("viewCount")) if stats.get("viewCount") is not None else None,
        "likeCount": int(stats.get("likeCount")) if stats.get("likeCount") is not None else None,
        "channelTitle": snippet.get("channelTitle"),
        "source": "youtube_api",
    }


def render_clip_text(meta: dict) -> str:
    fields = [
        ("链接", meta.get("url")),
        ("发布时间", meta.get("publishedDate") or meta.get("publishedAt")),
        ("标题", meta.get("title")),
        ("描述", meta.get("description")),
        ("点赞数", meta.get("likeCount")),
        ("观看次数", meta.get("viewCount")),
        ("时长", meta.get("durationText") or meta.get("durationSeconds")),
    ]
    return "\n".join(f"{k}: {'' if v is None else v}" for k, v in fields)


def main():
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass
    p = argparse.ArgumentParser(description="YouTube Data API v3 single-video fetcher")
    p.add_argument("url", help="YouTube video URL")
    p.add_argument("--key", help="YouTube API Key (fallback to YOUTUBE_API_KEY)")
    p.add_argument("--json", action="store_true", help="Print JSON instead of copy text")
    args = p.parse_args()

    video_id = parse_video_id(args.url)
    if not video_id:
        raise SystemExit("Unable to parse video ID from URL")

    api_key = args.key or os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise SystemExit("Missing API key. Provide --key or set YOUTUBE_API_KEY")

    meta = fetch_api(video_id, api_key)
    if args.json:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        print(render_clip_text(meta))


if __name__ == "__main__":
    main()
