# -*- coding: utf-8 -*-
"""认证与用户相关请求模型。"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求体（JSON）。"""

    username: str = Field(min_length=2, max_length=64, description="登录账号")
    password: str = Field(min_length=6, max_length=64, description="登录密码")


class PermissionUpdate(BaseModel):
    """管理员配置用户权限开关请求体（字段可选，仅更新传入项）。"""

    can_view_others: bool | None = Field(default=None, description="允许查看他人记录册")
    can_edit_others: bool | None = Field(default=None, description="允许编辑他人记录册")
