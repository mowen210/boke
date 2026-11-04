# -*- coding: utf-8 -*-
"""系统设置相关请求模型。"""
from pydantic import BaseModel, Field

MAX_UPLOAD_SIZE_LIMIT = 100  # 允许配置的上限上限（MB），防止误填过大数值拖垮服务器
MAX_VIDEO_SIZE_LIMIT = 2048  # 视频上限可配置的最大值（MB），视频体积天然较大


class SettingUpdate(BaseModel):
    """管理员更新系统设置请求体（字段可选，仅更新传入项）。"""

    max_upload_size: int | None = Field(
        default=None, ge=1, le=MAX_UPLOAD_SIZE_LIMIT, description="单张图片上传大小上限（MB），1-100"
    )
    max_video_size: int | None = Field(
        default=None, ge=1, le=MAX_VIDEO_SIZE_LIMIT, description="单个视频上传大小上限（MB），1-2048"
    )
