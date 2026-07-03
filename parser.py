"""
1905 视频解析器 - 核心逻辑

流程:
  1. 打开视频页面 (带 cookie)
  2. 拦截 generate_token 和 playback_assets 的 API 调用
  3. 获取 JWT + 视频 CDN 地址
  4. 提取视频元信息
"""
import json
import logging
import re
import urllib.parse
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger("parser")

CDN_QUALITY = {
    "sd": {"name": "标清", "host": "https://m3u8.vodfile.m1905.com"},
    "hd": {"name": "高清", "host": "https://m3u8i4.vodfile.m1905.com"},
    "uhd": {"name": "超高清", "host": "https://m3u8ipay1.vodfile.m1905.com"},
    "av1hd": {"name": "AV1高清", "host": "https://fmp4hd.vodfile.m1905.com"},
    "av1uhd": {"name": "AV1超高清", "host": "https://fmp4uhd.vodfile.m1905.com"},
}


async def parse_video(page: Page, url: str, cookies_str: Optional[str] = None) -> dict:
    """
    解析 1905 视频页面

    Args:
        page: Playwright 页面对象
        url: 视频播放页 URL
        cookies_str: Cookie 字符串 (用于 VIP 视频)

    Returns:
        dict: 视频信息和播放地址
    """
    result = {"url": url, "success": False, "video_info": {}, "play_urls": []}

    # 设置 cookie
    if cookies_str:
        await _set_cookies(page, url, cookies_str)

    # 拦截 API 响应 (使用 page.route 更可靠)
    api_data = {}
    m3u8_urls = []

    async def intercept(route):
        url = route.request.url
        response = await route.fetch()

        if "playback_assets.php" in url:
            try:
                resp = await response.json()
                api_data["playback"] = resp
                logger.info(f"playback_assets captured")
            except:
                pass

        if "generate_token.php" in url:
            try:
                resp = await response.json()
                api_data["token"] = resp
                logger.info(f"generate_token captured")
            except:
                pass

        if ".m3u8" in url:
            m3u8_urls.append(url)

        await route.fulfill(response=response)

    await page.route("**/*", intercept)

    # 加载页面
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        logger.warning(f"Page load timeout: {e}")

    # 等待视频加载 (最多 15 秒)
    for i in range(15):
        await page.wait_for_timeout(1000)
        if api_data.get("playback"):
            break

    # 如果 API 没触发，尝试点击播放器
    if not api_data.get("playback"):
        try:
            player = await page.query_selector("#vodPlayer, .player-media, video")
            if player:
                await player.click()
                logger.info("Clicked player to trigger video load")
        except:
            pass
        # 再等一会
        await page.wait_for_timeout(5000)

    # 提取 VODCONFIG
    vodconfig = await page.evaluate(
        "() => typeof VODCONFIG !== 'undefined' ? JSON.parse(JSON.stringify(VODCONFIG)) : null"
    )

    # 提取页面标题
    page_title = await page.title()

    # 构建结果
    if vodconfig:
        result["video_info"] = {
            "title": vodconfig.get("title", ""),
            "vid": vodconfig.get("vid", ""),
            "score": vodconfig.get("score", ""),
            "duration": vodconfig.get("play_duration", ""),
            "year": _extract_year(page_title),
            "type": vodconfig.get("type", ""),
        }

    if api_data.get("playback"):
        data = api_data["playback"].get("data", {})
        paths = data.get("path", {})
        quality = data.get("quality", {})
        signs = data.get("sign", {})

        for qname in ["uhd", "hd", "sd"]:
            if qname in paths:
                qdata = paths[qname]
                qhost_info = quality.get(qname, {})
                qhost = qhost_info.get("host", CDN_QUALITY.get(qname, {}).get("host", ""))
                sign_info = signs.get(qname, {})

                entry = {
                    "quality": qname,
                    "quality_name": CDN_QUALITY.get(qname, {}).get("name", qname),
                }

                # AVC
                path = qdata.get("path", "")
                if path and qhost:
                    entry["url"] = f"{qhost}{path}"
                    entry["codec"] = "AVC"

                # AV1
                av1path = qdata.get("av1path", "")
                if av1path:
                    av1sign = sign_info.get("av1sign", "")
                    entry["av1_url"] = f"{qhost}{av1path}{av1sign}"
                    entry["av1_codec"] = "AV1"

                result["play_urls"].append(entry)

    # 补充从网络请求中捕获的 m3u8
    for u in m3u8_urls:
        if u not in [p.get("url", "") for p in result["play_urls"]]:
            result["play_urls"].append({"url": u, "source": "captured"})

    result["success"] = len(result["play_urls"]) > 0
    return result


async def _set_cookies(page: Page, url: str, cookies_str: str):
    """设置 Cookie"""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.hostname or "www.1905.com"

    for item in cookies_str.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, value = item.split("=", 1)
        try:
            await page.context.add_cookies([{
                "name": name.strip(),
                "value": value.strip(),
                "domain": f".{domain}",
                "path": "/",
            }])
        except Exception as e:
            logger.warning(f"Cookie set error: {name}={e}")


def _extract_year(title: str) -> str:
    """从标题中提取年份"""
    match = re.search(r"\((\d{4})\)", title)
    return match.group(1) if match else ""
