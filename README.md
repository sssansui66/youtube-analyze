YouTube Analyze (个人自用)

功能
- 输入 YouTube 视频链接，提取并一键复制：链接、发布时间（ISO8601）、标题、描述、点赞数、观看次数、时长（文本与秒）。

运行
1) 安装依赖
- Python 3.10+
- pip install -r requirements.txt

2) 启动服务
- uvicorn app.main:app --reload
- 打开 http://127.0.0.1:8000/

零配置 API Key（推荐）
- 新建 `.env`（或复制 `.env.example` 重命名为 `.env`）并填入：
  YOUTUBE_API_KEY=你的APIKey
- 重启服务后，后端会自动读取 `.env`，优先通过官方 API 获取数据。

CLI（仅用官方 API，短平快）
- 环境变量：导出 YOUTUBE_API_KEY 或用 --key 传入
- 示例：
  - 文本（便于一键复制）：
    python app/api_cli.py "https://www.youtube.com/watch?v=VIDEO_ID"
  - JSON：
    python app/api_cli.py "https://youtu.be/VIDEO_ID" --json

可选配置
- YOUTUBE_API_KEY：若设置，优先使用官方 API（更稳定），失败回退 yt-dlp。
- YTDLP_COOKIE_FILE：指向从浏览器导出的 cookies.txt，提高受限视频可用性。

部署到 Vercel（推荐）
- 本仓库已包含 Vercel 约定：
  - `index.html` 与 `static/` 作为静态资源
  - `api/index.py` 作为 Python Serverless Function（FastAPI），提供 `/api/analyze`
- 步骤：
  1) 推送到 GitHub（一次性）
     - git init
     - git add .
     - git commit -m "init"
     - git branch -M main
     - git remote add origin https://github.com/你的用户名/youtube-analyze.git
     - git push -u origin main
  2) Vercel 控制台
     - New Project → 选择该 GitHub 仓库
     - Root Directory 选择仓库根目录
     - 添加环境变量：`YOUTUBE_API_KEY=你的Key`（建议在 Production/Preview/Development 都设置）
     - Deploy
  3) 访问你的域名，粘贴链接 → 点击“提取”即可

注意
- Vercel 的 `/api/analyze` 使用官方 API（不走 yt-dlp），速度稳定且配额可控。
- 本地开发服务仍保留 yt-dlp 回退，便于在未配置 Key 时也能测试。

接口
- POST /api/analyze
  - body: { "url": "https://www.youtube.com/watch?v=..." }
  - resp: { ok, data, text }

注意
- 点赞数可能在部分视频上不可用（返回 null）。
- 受限/私有视频可能无法提取，或需提供 cookies。
