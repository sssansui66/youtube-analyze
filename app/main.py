from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .analyzer import fetch_video_meta, render_clipboard_text

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

app = FastAPI(title="YouTube Analyze")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class AnalyzeRequest(BaseModel):
    url: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
async def api_root():
    return {
        "ok": True,
        "message": "Use POST /api/analyze",
        "endpoints": {"POST": ["/api/analyze"]},
    }


@app.post("/api/analyze")
async def analyze(body: AnalyzeRequest):
    try:
        meta = fetch_video_meta(body.url)
        text = render_clipboard_text(meta)
        return {"ok": True, "data": meta, "text": text}
    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})

@app.post("/api")
async def analyze_root(body: AnalyzeRequest):
    try:
        meta = fetch_video_meta(body.url)
        text = render_clipboard_text(meta)
        return {"ok": True, "data": meta, "text": text}
    except Exception as e:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})
