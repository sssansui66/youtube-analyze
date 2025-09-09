import os
import datetime as dt
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any


def _parse_video_id(url: str) -> Optional[str]:
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


def _iso8601_from_upload_date(upload_date: Optional[str]) -> Optional[str]:
    # yt-dlp upload_date format: YYYYMMDD
    if not upload_date or len(upload_date) != 8:
        return None
    try:
        dt_obj = dt.datetime.strptime(upload_date, "%Y%m%d")
        # Treat as UTC midnight if only date known
        return dt_obj.replace(tzinfo=dt.timezone.utc).isoformat()
    except Exception:
        return None


def _fmt_hms(seconds: Optional[int]) -> Optional[str]:
    if seconds is None:
        return None
    try:
        seconds = int(seconds)
    except Exception:
        return None
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _date_str_from_upload_date(upload_date: Optional[str]) -> Optional[str]:
    if not upload_date or len(upload_date) != 8:
        return None
    try:
        dt_obj = dt.datetime.strptime(upload_date, "%Y%m%d")
        return dt_obj.strftime("%Y-%m-%d")
    except Exception:
        return None


def _date_only_from_iso(iso_str: Optional[str]) -> Optional[str]:
    if not iso_str:
        return None
    try:
        # Expect formats like 2021-06-01T12:34:56Z or with offset
        return iso_str.split("T")[0]
    except Exception:
        return None


def _try_import_google():
    try:
        from googleapiclient.discovery import build  # type: ignore
        import isodate  # type: ignore
        return build, isodate
    except Exception:
        return None, None


def fetch_with_api(video_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    build, isodate = _try_import_google()
    if not build or not isodate:
        return None
    try:
        yt = build("youtube", "v3", developerKey=api_key)
        resp = yt.videos().list(part="snippet,contentDetails,statistics", id=video_id).execute()
        items = resp.get("items", [])
        if not items:
            return None
        item = items[0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        details = item.get("contentDetails", {})
        duration_iso = details.get("duration")
        duration_seconds = None
        if duration_iso:
            try:
                duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
            except Exception:
                duration_seconds = None
        published_at = snippet.get("publishedAt")
        return {
            "videoId": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "publishedAt": published_at,  # ISO8601
            "publishedDate": _date_only_from_iso(published_at),
            "durationSeconds": duration_seconds,
            "durationText": _fmt_hms(duration_seconds),
            "viewCount": int(stats.get("viewCount")) if stats.get("viewCount") is not None else None,
            "likeCount": int(stats.get("likeCount")) if stats.get("likeCount") is not None else None,
            "channelTitle": snippet.get("channelTitle"),
            "source": "youtube_api",
        }
    except Exception:
        return None


def fetch_with_ytdlp(url: str, cookies_path: Optional[str] = None) -> Dict[str, Any]:
    from yt_dlp import YoutubeDL  # lazy import to avoid heavy import at startup

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "extract_flat": False,
    }
    if cookies_path and os.path.exists(cookies_path):
        ydl_opts["cookiefile"] = cookies_path

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    upload_date = info.get("upload_date")
    upload_date_iso = _iso8601_from_upload_date(upload_date)
    duration_seconds = info.get("duration")
    return {
        "videoId": info.get("id"),
        "url": info.get("webpage_url") or url,
        "title": info.get("title"),
        "description": info.get("description"),
        "publishedAt": upload_date_iso,
        "publishedDate": _date_str_from_upload_date(upload_date),
        "durationSeconds": duration_seconds,
        "durationText": _fmt_hms(duration_seconds),
        "viewCount": info.get("view_count"),
        "likeCount": info.get("like_count"),
        "channelTitle": info.get("uploader"),
        "source": "yt_dlp",
    }


def fetch_video_meta(input_url: str) -> Dict[str, Any]:
    # Optional API path
    api_key = os.getenv("YOUTUBE_API_KEY")
    cookies_path = os.getenv("YTDLP_COOKIE_FILE")

    video_id = _parse_video_id(input_url)
    if api_key and video_id:
        api_data = fetch_with_api(video_id, api_key)
        if api_data:
            return api_data

    # Fallback to yt-dlp
    return fetch_with_ytdlp(input_url, cookies_path=cookies_path)


def render_clipboard_text(meta: Dict[str, Any]) -> str:
    # Order as requested: 链接、发布时间、标题、描述、点赞数、观看次数、时长
    fields = [
        ("链接", meta.get("url")),
        ("发布时间", meta.get("publishedDate") or meta.get("publishedAt")),
        ("标题", meta.get("title")),
        ("描述", meta.get("description")),
        ("点赞数", meta.get("likeCount")),
        ("观看次数", meta.get("viewCount")),
        ("时长", meta.get("durationText") or meta.get("durationSeconds")),
    ]
    lines = []
    for label, val in fields:
        if val is None:
            val = ""
        lines.append(f"{label}: {val}")
    return "\n".join(lines)
