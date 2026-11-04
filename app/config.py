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
UPLOAD_DIR = BASE_DIR / "upload"          # 上传文件保存目录（项目内 upload 文件夹）
# 单文件大小上限（MB）：首次启动写入 sys_setting 表的初始值，之后由管理员在前端调整
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}  # 允许的图片格式

# 单个视频大小上限（MB）：视频体积远大于图片，独立配置；同样由管理员在前端调整
MAX_VIDEO_UPLOAD_SIZE_MB = int(os.getenv("MAX_VIDEO_UPLOAD_SIZE_MB", "200"))
MAX_VIDEO_UPLOAD_SIZE = MAX_VIDEO_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v", "ogg"}  # 允许的视频格式（浏览器可直接播放）

# ---------------- 初始账号配置（首次启动自动创建） ----------------
INIT_ADMIN_USERNAME = os.getenv("INIT_ADMIN_USERNAME", "admin")
INIT_ADMIN_PASSWORD = os.getenv("INIT_ADMIN_PASSWORD", "admin123")
INIT_DEMO_USERNAME = os.getenv("INIT_DEMO_USERNAME", "demo")
INIT_DEMO_PASSWORD = os.getenv("INIT_DEMO_PASSWORD", "123456")
