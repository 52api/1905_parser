"""
1905 视频 API - FastAPI 主服务
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from browser_pool import get_pool
from parser import parse_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("api")


# ===== JSON 请求模型 =====

class VideoRequest(BaseModel):
    url: str = Field(..., description="1905 视频播放页 URL")
    cookies: Optional[str] = Field(None, description="Cookie 字符串 (用于 VIP 视频)")


# ===== 应用生命周期 =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化浏览器池
    logger.info("正在启动浏览器池...")
    pool = await get_pool()
    logger.info(f"浏览器池已就绪 (最大 {pool._max_pages} 页面)")
    yield
    # 关闭时清理
    logger.info("正在关闭浏览器池...")
    await pool.close()


app = FastAPI(
    title="1905 视频解析 API",
    description="解析 1905 电影网的视频信息和播放地址",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== API 端点 =====

@app.get("/", tags=["健康检查"])
async def root():
    return {
        "service": "1905 视频解析 API",
        "version": "1.0.0",
        "endpoints": {
            "GET  /api/video": "通过 URL 查询参数解析视频",
            "POST /api/video": "通过表单提交解析视频 (支持 cookie)",
            "POST /api/video/json": "通过 JSON Body 解析视频 (支持 cookie)",
        },
    }


@app.get("/api/video", tags=["视频解析"])
async def get_video(
    url: str = Query(..., description="1905 视频播放页完整 URL"),
):
    """通过 GET 请求解析视频 (无需 Cookie)"""
    return await _handle_request(url)


@app.post("/api/video", tags=["视频解析"])
async def post_video_form(
    url: str = Form(..., description="1905 视频播放页 URL"),
    cookies: Optional[str] = Form(None, description="Cookie 字符串"),
):
    """通过 POST 表单提交解析视频"""
    return await _handle_request(url, cookies)


@app.post("/api/video/json", tags=["视频解析"])
async def post_video_json(body: VideoRequest):
    """通过 POST JSON 提交解析视频"""
    return await _handle_request(body.url, body.cookies)


# ===== 内部处理 =====

async def _handle_request(url: str, cookies: Optional[str] = None) -> dict:
    """统一处理视频解析请求"""
    start_time = time.time()

    # 验证 URL
    if not url or "1905.com" not in url:
        raise HTTPException(status_code=400, detail="无效的 URL，必须是 1905.com 的视频播放页")

    # 提取视频 ID
    import re
    vid_match = re.search(r"/play/(\d+)", url)
    if not vid_match:
        raise HTTPException(status_code=400, detail="无法从 URL 中提取视频 ID")

    pool = await get_pool()
    page = await pool.get_page()

    try:
        logger.info(f"解析视频: {url} (cookie={'是' if cookies else '否'})")
        result = await parse_video(page, url, cookies)

        elapsed = time.time() - start_time
        logger.info(f"解析完成: {result['success']}, 耗时 {elapsed:.2f}s, "
                    f"获取到 {len(result['play_urls'])} 个播放地址")

        if not result["success"]:
            result["message"] = "未能获取到视频播放地址，可能需要 VIP 登录"

        return result

    except Exception as e:
        logger.error(f"解析异常: {e}")
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

    finally:
        await pool.return_page(page)
