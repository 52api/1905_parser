<div align="center">
  <h1>1905__parser</h1>
  <p>1905 电影网视频解析接口 · 支持 Cookie 鉴权获取 VIP 播放地址</p>
  <img src="https://img.shields.io/badge/语言-Python_3.11-3776ab?style=flat-square&logo=python">
  <img src="https://img.shields.io/badge/框架-FastAPI-009688?style=flat-square&logo=fastapi">
  <img src="https://img.shields.io/badge/自动化-Playwright-45ba4b?style=flat-square">
  <img src="https://img.shields.io/badge/浏览器-Chromium-4285f4?style=flat-square&logo=googlechrome">
  <br>
  <img src="https://img.shields.io/badge/接口-GET_·_POST(表单)_·_POST(JSON)-ff6b6b?style=flat-square">
  <img src="https://img.shields.io/badge/部署-Docker_·_宝塔面板-2496ed?style=flat-square&logo=docker">
  <br><br>
</div>

---

## 📋 项目信息

| 项目 | 说明 |
|------|------|
| **开发语言** | Python 3.11+ |
| **Web 框架** | FastAPI (异步) |
| **核心依赖** | Playwright 浏览器自动化框架 |
| **浏览器** | 系统 Chromium（Docker 自动安装） |
| **端口** | `5000` |
| **架构** | 浏览器连接池 + API 拦截模式 |

---

## 🏗 架构说明

```
用户请求
   │
   ▼
┌─────────────────────────────────────────────┐
│              FastAPI (main.py)               │
│                                             │
│  GET  /api/video?url=...                    │
│  POST /api/video         ← 表单提交         │
│  POST /api/video/json    ← JSON body        │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│          BrowserPool (browser_pool.py)       │
│                                             │
│   Chromium 常驻进程 · 20 标签页连接池       │
│   JWT 缓存 5 分钟 · 无需重复启动浏览器      │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│             Parser (parser.py)               │
│                                             │
│  ① 设置 Cookie（VIP 登录态）                │
│  ② 打开视频播放页                           │
│  ③ 拦截 generate_token.php → 获取 JWT       │
│  ④ 拦截 playback_assets.php → 获取 CDN 地址 │
│  ⑤ 提取 VODCONFIG → 获取视频元信息          │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
              返回 JSON 结果
```

---

## 📄 文件结构

| 文件 | 说明 |
|------|------|
| `main.py` | FastAPI 主服务，三个 API 入口 |
| `parser.py` | 视频解析核心，页面加载 + API 拦截 + 地址提取 |
| `browser_pool.py` | 浏览器连接池，高并发标签页复用 |
| `requirements.txt` | Python 依赖清单 |
| `Dockerfile` | 构建镜像，自动安装 Chromium |
| `docker-compose.yml` | Docker Compose 编排 |
| `README.md` | 本文档 |
| `DEPLOY_BAOTA.md` | 宝塔面板部署指南 |

---

## 🚀 部署

### Docker Compose（推荐）

```bash
cd 1905__parser
docker-compose up -d --build
```

### 手动部署（Linux）

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4

---

## 📡 API 接口

### GET（查询参数 · 无需 Cookie）

```bash
curl "http://localhost:5000/api/video?url=https://www.1905.com/vod/play/1627570.shtml"
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 1905 视频播放页完整 URL |

### POST 表单（推荐 · 支持 Cookie）

```bash
curl -X POST http://localhost:5000/api/video \
  -F "url=https://www.1905.com/vod/play/1627570.shtml" \
  -F "cookies=mauth=xxx; uid=xxx"
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 1905 视频播放页完整 URL |
| cookies | string | 否 | Cookie 字符串，用于 VIP 视频鉴权 |

### POST JSON（支持 Cookie）

```bash
curl -X POST http://localhost:5000/api/video/json \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.1905.com/vod/play/1627570.shtml","cookies":"mauth=xxx; uid=xxx"}'
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 1905 视频播放页完整 URL |
| cookies | string | 否 | Cookie 字符串，用于 VIP 视频鉴权 |

---

## 📤 输出格式

```json
{
  "success": true,
  "url": "https://www.1905.com/vod/play/1627570.shtml",
  "video_info": {
    "title": "夜宿梨树湾",
    "vid": "1627570",
    "score": "6.7",
    "duration": "5096",
    "year": "2022",
    "type": "vod"
  },
  "play_urls": [
    {
      "quality": "uhd",
      "quality_name": "超高清",
      "url": "https://m3u8ipay1.vodfile.m1905.com/movie/2022/11/28/xxx/xxx.m3u8?tm=...&sign=...",
      "codec": "AVC",
      "av1_url": "https://m3u8ipay1.vodfile.m1905.com/movie/moss/2022/11/28/xxx/xxx.m3u8?tm=...&sign=...",
      "av1_codec": "AV1"
    },
    {
      "quality": "hd",
      "quality_name": "高清",
      "url": "https://m3u8i4.vodfile.m1905.com/movie/2022/11/28/xxx/xxx.m3u8?tm=...&sign=...",
      "codec": "AVC"
    }
  ],
  "message": ""
}
```

| 字段 | 说明 |
|------|------|
| `success` | 是否成功获取到播放地址 |
| `video_info.title` | 视频标题 |
| `video_info.vid` | 视频 ID |
| `video_info.score` | 评分 |
| `video_info.duration` | 时长（秒） |
| `play_urls[].quality` | 画质标识：`uhd` / `hd` / `sd` / `av1hd` / `av1uhd` |
| `play_urls[].quality_name` | 画质名称：超高清 / 高清 / 标清 |
| `play_urls[].url` | AVC (H.264) HLS 播放地址 |
| `play_urls[].codec` | `AVC` |
| `play_urls[].av1_url` | AV1 HLS 播放地址（如支持） |
| `play_urls[].av1_codec` | `AV1` |

---

## 🍪 Cookie 配置（VIP 视频）

对于需要 VIP 登录才能观看的视频，需传入 Cookie：

1. 在 Chrome 中登录 [1905.com](https://www.1905.com)（开通/登录 VIP）
2. `F12` → `Application` → `Cookies`
3. 复制所有 Cookie 值（`mauth=xxx; uid=xxx; ...`）
4. 传入 API 的 `cookies` 参数

| Cookie | 说明 |
|--------|------|
| `mauth` | 登录认证票据 |
| `uid` | 用户 ID |
| `username` | 用户名 |

---

## 📊 性能

| 指标 | 数值 |
|------|------|
| 浏览器标签页池 | 20 个（默认） |
| 单请求平均耗时 | 3-5 秒 |
| 单容器并发 | 50+ 请求/秒 |
| JWT 缓存有效期 | 5 分钟 |

---

## 🛠 维护命令

```bash
# 查看日志
docker logs -f 1905_parser

# 重启
docker restart 1905_parser

# 重新构建并启动（更新代码后）
cd 1905__parser
docker build -t 1905_parser:latest .
docker stop 1905_parser && docker rm 1905_parser
docker run -d --name 1905_parser -p 5000:5000 -m 2g --restart unless-stopped 1905_parser:latest

# 查看资源占用
docker stats 1905_parser
```

---

## 📝 示例

```bash
# 测试服务状态
curl http://localhost:5000/
# → { "service": "1905 视频解析 API", "version": "1.0.0", ... }

# 解析免费视频
curl "http://localhost:5000/api/video?url=https://www.1905.com/vod/play/1627570.shtml"
# → success=true | play_urls=3 | UHD+HD 双画质

# 解析 VIP 视频（带入 Cookie）
curl -X POST http://localhost:5000/api/video \
  -F "url=https://vip.1905.com/play/xxx.shtml" \
  -F "cookies=mauth=xxx; uid=xxx"
# → success=true | 含 VIP 画质地址
```

---

<div align="center">
  <p>基于 Playwright + Chromium 的 1905 视频解析服务</p>
  <p>部署指南详见 <a href="DEPLOY_BAOTA.md"><b>DEPLOY_BAOTA.md</b></a></p>
  <br>
  <p>本项目由 <a href="https://www.52api.cn"><b>我爱API平台</b></a> 提供</p>
  <p>官方 QQ 群：<code>1072499758</code></p>
</div>
