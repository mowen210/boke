# -*- coding: utf-8 -*-
"""照片模型。"""
from sqlalchemy import Column, ForeignKey, Index, Integer, String

from app.database import Base
from app.models.base import BaseModelMixin


class Photo(Base, BaseModelMixin):
    """照片表：每张照片归属某记录册的某个模块，可附独立文字备注，支持排序。"""

    __tablename__ = "photo"
    __table_args__ = (
        # 常用查询：按记录册+模块加载照片列表（按排序号）
        Index("ix_photo_album_module_sort", "album_id", "module_id", "sort_order"),
        {"comment": "照片表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    album_id = Column(Integer, ForeignKey("photo_album.id"), nullable=False, comment="所属记录册ID")
    module_id = Column(Integer, ForeignKey("album_module.id"), nullable=False, comment="所属模块ID")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="上传人用户ID")
    file_path = Column(String(255), nullable=False, comment="图片相对访问路径（/upload/...）")
    original_name = Column(String(255), nullable=True, comment="原始文件名")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    file_type = Column(String(32), nullable=True, comment="MIME 类型")
    note = Column(String(500), nullable=True, comment="照片文字备注")
    sort_order = Column(Integer, nullable=False, default=0, comment="模块内排序号（越小越靠前）")
