# ============================================================
# 照片记录册管理系统 · 镜像构建
# 构建：docker compose build
# 运行：见 docker-compose.yml（app + mysql 一键编排）
# ============================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# tzdata：使 TZ=Asia/Shanghai 生效（照片时间与 upload/YYYYMM 目录按本地时区生成）
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

# 依赖单独一层，充分利用构建缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 业务代码（.dockerignore 已排除 .env / upload / 文档与测试脚本）
COPY main.py .
COPY app ./app
COPY templates ./templates
COPY static ./static

# 上传目录（compose 中以 bind mount 挂载到宿主机持久化）
RUN mkdir -p upload

# 非 root 运行（uid/gid 1000，与多数 Linux 发行版首位普通用户一致）
RUN useradd -u 1000 -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
