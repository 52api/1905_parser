# 宝塔面板部署 1905__parser

## 前置条件

- 宝塔面板已安装（Linux）
- 服务器配置 ≥ 2GB 内存 / 2核 CPU

## 操作步骤

### 1. 上传项目文件

```
本地电脑 D:\n\1905__parser\  →  服务器 /www/wwwroot/1905__parser/
```

在宝塔 **文件管理器** 中操作：
1. 将 `1905__parser` 文件夹压缩
2. 上传到 `/www/wwwroot/` 目录
3. 解压，得到 `/www/wwwroot/1905__parser/`

确认目录结构：

```
/www/wwwroot/1905__parser/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── main.py
├── parser.py
├── browser_pool.py
└── README.md
```

### 2. 安装 Docker

宝塔面板 → **软件商店** → 搜索 `docker` → **安装 Docker 管理器**

安装完成后打开 Docker 管理器，确认运行状态为 **运行中**。

### 3. 构建镜像

**方法一：SSH 命令行（推荐）**

宝塔面板 → **终端** → 执行：

```bash
cd /www/wwwroot/1905__parser
docker build -t 1905_parser:latest .
```

构建过程约 5-10 分钟（需要下载 Chromium）。

**方法二：宝塔 Docker 界面**

宝塔面板 → **Docker** → **镜像管理** → **构建镜像**
- 名称：`1905_parser`
- 版本：`latest`
- Dockerfile 目录：`/www/wwwroot/1905__parser/`
- 点击 **提交**

### 4. 创建容器

**方法一：SSH 命令行**

```bash
docker run -d \
  --name 1905_parser \
  -p 5000:5000 \
  -m 2g \
  --cpus 2 \
  --restart unless-stopped \
  1905_parser:latest
```

**方法二：宝塔 Docker 界面**

宝塔面板 → **Docker** → **容器** → **创建容器**

| 配置项 | 值 |
|--------|-----|
| 镜像 | `1905_parser:latest` |
| 容器名称 | `1905_parser` |
| 端口映射 | `5000:5000` |
| 内存限制 | `2048 MB` |
| CPU 限制 | `2` 核 |
| 重启策略 | `始终重启 (unless-stopped)` |

其他选项保持默认，点击 **确定**。

### 5. 验证服务

容器启动后，执行：

```bash
curl http://127.0.0.1:5000/
```

返回：

```json
{
  "service": "1905 视频解析 API",
  "version": "1.0.0",
  "endpoints": {
    "GET  /api/video": "通过 URL 查询参数解析视频",
    "POST /api/video": "通过表单提交解析视频 (支持 cookie)",
    "POST /api/video/json": "通过 JSON Body 解析视频 (支持 cookie)"
  }
}
```

### 6. 设置反向代理（可选）

如需通过域名访问，配置反向代理：

宝塔面板 → **网站** → **添加站点**
- 域名：`video.你的域名.com`
- 数据库、PHP 等全部选择 **不创建**

站点创建后 → **设置** → **反向代理**

| 配置项 | 值 |
|--------|-----|
| 代理名称 | `1905_parser` |
| 目标 URL | `http://127.0.0.1:5000` |
| 缓存 | 关闭 |
| 高级功能 → 开启 | √ 发送域名 |

### 7. 测试 API

```bash
# 直接访问
curl "http://你的服务器IP:5000/api/video?url=https://www.1905.com/vod/play/1627570.shtml"

# 或通过域名
curl "https://video.你的域名.com/api/video?url=https://www.1905.com/vod/play/1627570.shtml"
```

### 8. 维护命令

```bash
# 查看日志
docker logs -f 1905_parser

# 重启容器
docker restart 1905_parser

# 停止容器
docker stop 1905_parser

# 删除容器（需先 stop）
docker rm 1905_parser

# 重新构建并启动（更新代码后）
cd /www/wwwroot/1905__parser
docker build -t 1905_parser:latest .
docker stop 1905_parser && docker rm 1905_parser
docker run -d --name 1905_parser -p 5000:5000 -m 2g --restart unless-stopped 1905_parser:latest

# 查看资源占用
docker stats 1905_parser
```

## 常见问题

### Q: 构建镜像时报错连接超时

国内服务器拉取 Chromium 可能较慢。如多次失败，SSH 执行：

```bash
# 使用淘宝镜像安装 Chromium
cd /www/wwwroot/1905__parser
pip install playwright
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/playwright python -m playwright install chromium
```

### Q: 容器启动后无法访问 5000

检查防火墙和云安全组是否放行 5000 端口。

宝塔面板 → **安全** → **添加端口规则**
- 端口：`5000`
- 协议：`TCP`
- 来源：`全部`

### Q: 内存不足导致容器退出

```bash
docker update 1905_parser --memory-swap -1 --memory 4g
```

或降低并发标签页数，修改 `browser_pool.py` 中 `BrowserPool(max_pages=10)`。
