# -*- coding: utf-8 -*-
"""记录册相关请求模型。"""
from pydantic import BaseModel, Field


class AlbumCreate(BaseModel):
    """新建记录册。"""

    name: str = Field(min_length=1, max_length=100, description="记录册名称")
    description: str | None = Field(default=None, max_length=500, description="记录册简介")


class AlbumUpdate(BaseModel):
    """编辑记录册基础信息（JSON 用法；封面走 multipart 接口）。"""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="记录册名称")
    description: str | None = Field(default=None, max_length=500, description="记录册简介")


class TemplateUpdate(BaseModel):
    """切换记录册展示模板。"""

    template_id: int = Field(gt=0, description="目标模板ID")
