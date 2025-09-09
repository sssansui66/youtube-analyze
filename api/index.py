from fastapi import FastAPI
from pydantic import BaseModel
import os
from app.api_cli import parse_video_id, fetch_api, render_clip_text

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

app = FastAPI(title="YouTube Analyze API")


class AnalyzeBody(BaseModel):
    url: str


@app.get("/")
@app.get("/api")
async def root():
    return {"ok": True, "message": "Use POST /api/analyze"}

@app.post("/analyze")
@app.post("/api/analyze")
async def analyze(body: AnalyzeBody):
    vid = parse_video_id(body.url)
    if not vid:
        return {"ok": False, "error": "无法解析视频ID，请确认是视频链接"}
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {"ok": False, "error": "服务器未配置 YOUTUBE_API_KEY"}
    try:
        meta = fetch_api(vid, api_key)
        text = render_clip_text(meta)
        return {"ok": True, "data": meta, "text": text}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/")
async def analyze_root(body: AnalyzeBody):
    vid = parse_video_id(body.url)
    if not vid:
        return {"ok": False, "error": "无法解析视频ID，请确认是视频链接"}
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {"ok": False, "error": "服务器未配置 YOUTUBE_API_KEY"}
    try:
        meta = fetch_api(vid, api_key)
        text = render_clip_text(meta)
        return {"ok": True, "data": meta, "text": text}
    except Exception as e:
        return {"ok": False, "error": str(e)}
