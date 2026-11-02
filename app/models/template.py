# -*- coding: utf-8 -*-
"""展示模板（相册风格）配置模型。"""
from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base
from app.models.base import BaseModelMixin


class PhotoTemplate(Base, BaseModelMixin):
    """模板配置表：内置多套相册展示风格，记录册可一键切换整册排版样式。"""

    __tablename__ = "photo_template"
    __table_args__ = {"comment": "相册展示模板配置表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    code = Column(String(32), nullable=False, unique=True, comment="模板编码（唯一）")
    name = Column(String(64), nullable=False, comment="模板名称")
    css_class = Column(String(64), nullable=False, comment="模板对应的前端 CSS 类名")
    description = Column(String(255), nullable=True, comment="模板说明")
    sort_order = Column(Integer, nullable=False, default=0, comment="模板展示排序")
    is_default = Column(Boolean, nullable=False, default=False, comment="是否默认模板")
