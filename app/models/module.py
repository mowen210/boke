# -*- coding: utf-8 -*-
"""记录册自定义模块模型（记录册内的分组/章节）。"""
from sqlalchemy import Column, ForeignKey, Index, Integer, String

from app.database import Base
from app.models.base import BaseModelMixin


class AlbumModule(Base, BaseModelMixin):
    """模块表：每本记录册可自定义多个模块（如“春游”“生日”），支持拖拽排序。"""

    __tablename__ = "album_module"
    __table_args__ = (
        # 常用查询：按记录册列出模块并按排序号展示
        Index("ix_module_album_sort", "album_id", "sort_order"),
        {"comment": "记录册自定义模块表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    album_id = Column(Integer, ForeignKey("photo_album.id"), nullable=False, comment="所属记录册ID")
    title = Column(String(100), nullable=False, comment="模块标题")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序号（越小越靠前）")
