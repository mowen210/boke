# -*- coding: utf-8 -*-
"""照片相关请求模型。"""
from pydantic import BaseModel, Field


class PhotoNoteUpdate(BaseModel):
    """更新照片备注。"""

    note: str | None = Field(default=None, max_length=500, description="照片文字备注")


class PhotoMoveRequest(BaseModel):
    """照片移动到其他模块。"""

    module_id: int = Field(gt=0, description="目标模块ID")


class PhotoSortRequest(BaseModel):
    """照片拖拽排序：模块内按顺序传入照片ID列表。"""

    module_id: int = Field(gt=0, description="照片所属模块ID")
    photo_ids: list[int] = Field(min_length=1, description="排序后的照片ID列表")
