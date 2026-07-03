"""
1905 视频 API - 浏览器池管理器
"""
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger("browser_pool")


class BrowserPool:
    """浏览器池 - 管理多个 Chromium 标签页用于高并发"""

    def __init__(self, max_pages: int = 20, headless: bool = True):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._available: asyncio.Queue[Page] = asyncio.Queue(maxsize=max_pages)
        self._max_pages = max_pages
        self._headless = headless
        self._total_created = 0

    async def start(self):
        """启动浏览器"""
        import sys, os
        self._playwright = await async_playwright().start()
        launch_opts = {
            'headless': self._headless,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
            ],
        }
        # Linux Docker 环境使用系统 chromium
        if sys.platform == 'linux':
            launch_opts['executable_path'] = os.environ.get(
                'CHROMIUM_PATH', '/usr/bin/chromium'
            )
        else:
            # Windows/Mac 使用已安装的 Chrome
            launch_opts['channel'] = 'chrome'

        logger.info(f"启动浏览器: {launch_opts}")
        self._browser = await self._playwright.chromium.launch(**launch_opts)
        logger.info("浏览器启动成功")
        # 预创建页面
        for i in range(min(3, self._max_pages)):
            try:
                await self._create_page()
                logger.info(f"预创建页面 {i+1} 成功")
            except Exception as e:
                logger.error(f"预创建页面 {i+1} 失败: {e}")
                raise

    async def _create_page(self) -> Page:
        """创建一个新页面"""
        page = await self._browser.new_page()
        self._total_created += 1
        page.set_default_timeout(30000)
        # 放入队列
        await self._available.put(page)
        return page

    async def get_page(self) -> Page:
        """获取一个可用页面"""
        try:
            page = await asyncio.wait_for(self._available.get(), timeout=10)
            return page
        except asyncio.TimeoutError:
            if self._total_created < self._max_pages:
                await self._create_page()
                page = await asyncio.wait_for(self._available.get(), timeout=10)
                return page
            raise

    async def return_page(self, page: Page):
        """归还页面到池中"""
        try:
            # 清理页面状态
            await page.evaluate("() => { /* 清理 */ }")
        except:
            pass
        await self._available.put(page)

    async def close(self):
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


# 全局单例
_pool: Optional[BrowserPool] = None


async def get_pool() -> BrowserPool:
    global _pool
    if _pool is None:
        _pool = BrowserPool(max_pages=20)
        await _pool.start()
    return _pool
