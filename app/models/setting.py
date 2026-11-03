# -*- coding: utf-8 -*-
"""系统设置模型。

- sys_setting：键值对形式的系统配置（如上传大小上限），管理员可在前端修改
"""
from sqlalchemy import Column, String

from app.database import Base
from app.models.base import BaseModelMixin


class SysSetting(Base, BaseModelMixin):
    """系统设置表。"""

    __tablename__ = "sys_setting"

    setting_key = Column(String(64), primary_key=True, comment="设置键：如 max_upload_size")
    setting_value = Column(String(255), nullable=False, comment="设置值（字符串存储，业务侧自行转换类型）")
    remark = Column(String(255), nullable=True, comment="设置说明")
