# -*- coding: utf-8 -*-
"""模块相关请求模型。"""
from pydantic import BaseModel, Field


class ModuleCreate(BaseModel):
    """新增模块。"""

    title: str = Field(min_length=1, max_length=100, description="模块标题")


class ModuleUpdate(BaseModel):
    """修改模块标题。"""

    title: str = Field(min_length=1, max_length=100, description="模块标题")


class ModuleSortRequest(BaseModel):
    """模块拖拽排序：按顺序传入模块ID列表，服务端按序写排序号。"""

    module_ids: list[int] = Field(min_length=1, description="排序后的模块ID列表")
