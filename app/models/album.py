# -*- coding: utf-8 -*-
"""记录册（相册）模型。"""
from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModelMixin


class PhotoAlbum(Base, BaseModelMixin):
    """记录册表：一本记录册即一个照片纪念册，属于某个用户。"""

    __tablename__ = "photo_album"
    __table_args__ = (
        # 常用查询：按用户列出其记录册（带软删除过滤）
        Index("ix_album_user_deleted", "user_id", "is_deleted"),
        {"comment": "照片记录册表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("sys_user.id"), nullable=False, comment="创建人用户ID")
    name = Column(String(100), nullable=False, comment="记录册名称")
    description = Column(String(500), nullable=True, comment="记录册简介")
    cover_image = Column(String(255), nullable=False, default="/static/img/default_cover.svg",
                         comment="封面图相对访问路径")
    template_id = Column(Integer, ForeignKey("photo_template.id"), nullable=True,
                         comment="当前使用的展示模板ID")

    user = relationship("SysUser")
    template = relationship("PhotoTemplate")
