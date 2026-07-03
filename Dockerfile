FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libcups2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（使用清华镜像加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout 120 -r requirements.txt

# 安装 Playwright Chromium（使用国内镜像）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/playwright
RUN python -m playwright install chromium

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

COPY . .

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
