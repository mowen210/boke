# -*- coding: utf-8 -*-
"""上传文件校验与保存工具。

- 图片仅允许 jpg / jpeg / png / gif / webp
- 视频仅允许 mp4 / webm / mov / m4v / ogg（浏览器可直接播放）
- 单文件大小上限由调用方传入（管理员可在前端调整，见 setting_service）
- 保存到项目内 upload/YYYYMM/ 目录，文件名使用 UUID 防冲突与路径穿越
- 数据库仅保存形如 /upload/YYYYMM/xxx.jpg 的相对访问路径
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException

from app.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_UPLOAD_SIZE,
    MAX_VIDEO_UPLOAD_SIZE,
    UPLOAD_DIR,
)


def _extension(filename: str) -> str:
    """提取小写扩展名（不含点）。"""
    return Path(filename or "").suffix.lower().lstrip(".")


def is_video(filename: str) -> bool:
    """按扩展名判断是否为视频文件。"""
    return _extension(filename) in ALLOWED_VIDEO_EXTENSIONS


def is_image(filename: str) -> bool:
    """按扩展名判断是否为图片文件。"""
    return _extension(filename) in ALLOWED_EXTENSIONS


def validate_image(filename: str, content: bytes, max_size: Optional[int] = None) -> str:
    """校验图片格式与大小，通过则返回扩展名，否则抛出 400。

    :param max_size: 单文件大小上限（字节），缺省回退 config 默认值
    """
    limit = max_size or MAX_UPLOAD_SIZE
    ext = _extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式：{filename}（仅允许 jpg/png/gif/webp）")
    if not content:
        raise HTTPException(status_code=400, detail=f"上传文件为空：{filename}")
    if len(content) > limit:
        raise HTTPException(
            status_code=400, detail=f"文件超过 {limit // 1024 // 1024}MB 上限：{filename}"
        )
    return ext


def validate_video(filename: str, content: bytes, max_size: Optional[int] = None) -> str:
    """校验视频格式与大小，通过则返回扩展名，否则抛出 400。

    :param max_size: 单文件大小上限（字节），缺省回退 config 默认值
    """
    limit = max_size or MAX_VIDEO_UPLOAD_SIZE
    ext = _extension(filename)
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的视频格式：{filename}（仅允许 mp4/webm/mov/m4v/ogg）")
    if not content:
        raise HTTPException(status_code=400, detail=f"上传文件为空：{filename}")
    if len(content) > limit:
        raise HTTPException(
            status_code=400, detail=f"文件超过 {limit // 1024 // 1024}MB 上限：{filename}"
        )
    return ext


def _save(ext: str, content: bytes) -> Tuple[str, int]:
    """按扩展名写入 upload/YYYYMM/ 目录，返回相对访问路径与字节数。"""
    sub_dir = datetime.now().strftime("%Y%m")
    folder = UPLOAD_DIR / sub_dir
    folder.mkdir(parents=True, exist_ok=True)
    save_name = f"{uuid.uuid4().hex}.{ext}"
    (folder / save_name).write_bytes(content)
    return f"/upload/{sub_dir}/{save_name}", len(content)


def save_image(filename: str, content: bytes, max_size: Optional[int] = None) -> Tuple[str, int]:
    """保存图片字节到 upload 目录。

    :return: (相对访问路径, 文件字节数)，如 ("/upload/202611/ab12....jpg", 204800)
    """
    ext = validate_image(filename, content, max_size)
    return _save(ext, content)


def save_video(filename: str, content: bytes, max_size: Optional[int] = None) -> Tuple[str, int]:
    """保存视频字节到 upload 目录（校验规则与图片独立）。"""
    ext = validate_video(filename, content, max_size)
    return _save(ext, content)


def guess_mime(filename: str) -> str:
    """根据扩展名推断 MIME 类型（入库记录用）。"""
    ext = _extension(filename)
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "mp4": "video/mp4",
        "m4v": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
        "ogg": "video/ogg",
    }.get(ext, "application/octet-stream")
