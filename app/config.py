# -*- coding: utf-8 -*-
"""全局配置模块。

所有可变配置均支持通过环境变量 / .env 文件覆盖，便于部署时无需改代码即可切换环境。
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

# 优先加载项目根目录下的 .env 文件（存在则加载，不存在则使用默认值）
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # 未安装 python-dotenv 时直接使用环境变量/默认值
    pass

# 项目根目录（app/config.py 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------- MySQL 数据库配置 ----------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "192.168.1.4")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "mowen")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Mowen@1998")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "photo_album")

# SQLAlchemy 连接串（使用 PyMySQL 驱动）
# 密码含 @ : / 等特殊字符时必须 URL 编码，否则连接串解析错乱
# （例如密码 "abc@1998" 不编码会被解析成主机 "1998@..."）
DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

# ---------------- JWT 鉴权配置 ----------------
SECRET_KEY = os.getenv("SECRET_KEY", "photo-album-secret-key-please-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "1440"))  # 令牌有效期，默认 24 小时
COOKIE_NAME = "access_token"  # 登录令牌存放的 Cookie 名称

# ---------------- 上传文件配置 ----------------
UPLOAD_DIR = BASE_DIR / "upload"          # 上传图片保存目录（项目内 upload 文件夹）
MAX_UPLOAD_SIZE = 5 * 1024 * 1024         # 单文件最大 5MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}  # 允许的图片格式

# ---------------- 初始账号配置（首次启动自动创建） ----------------
INIT_ADMIN_USERNAME = os.getenv("INIT_ADMIN_USERNAME", "admin")
INIT_ADMIN_PASSWORD = os.getenv("INIT_ADMIN_PASSWORD", "admin123")
INIT_DEMO_USERNAME = os.getenv("INIT_DEMO_USERNAME", "demo")
INIT_DEMO_PASSWORD = os.getenv("INIT_DEMO_PASSWORD", "123456")
