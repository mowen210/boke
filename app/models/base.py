# -*- coding: utf-8 -*-
"""通用模型混入：所有业务表统一包含 id 主键、create_time、update_time、is_deleted。"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime


class BaseModelMixin:
    """表公共字段混入（配合各自表的主键 id 使用）。"""

    create_time = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    update_time = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间",
    )
    is_deleted = Column(Boolean, nullable=False, default=False, comment="软删除标识：0正常 1已删除")
