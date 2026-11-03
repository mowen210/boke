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


class PasswordChange(BaseModel):
    """用户修改自身密码请求体。"""

    old_password: str = Field(min_length=6, max_length=64, description="原密码")
    new_password: str = Field(min_length=6, max_length=64, description="新密码（至少 6 位）")
    confirm_password: str = Field(min_length=6, max_length=64, description="确认新密码")


class UserCreate(BaseModel):
    """管理员新增用户请求体。"""

    username: str = Field(min_length=2, max_length=64, description="登录账号（唯一）")
    password: str = Field(min_length=6, max_length=64, description="初始密码（至少 6 位）")
    nickname: str | None = Field(default=None, max_length=64, description="用户昵称")
    role_code: str = Field(default="USER", description="角色编码：ADMIN/USER")
    can_view_others: bool = Field(default=False, description="允许查看他人记录册")
    can_edit_others: bool = Field(default=False, description="允许编辑他人记录册")
