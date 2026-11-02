# -*- coding: utf-8 -*-
"""用户与角色权限模型。

- sys_role：角色权限表（内置 ADMIN 管理员 / USER 普通用户）
- sys_user：用户表（密码 bcrypt 哈希存储；can_view_others / can_edit_others
  为管理员可单独配置的用户级权限开关）
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModelMixin


class SysRole(Base, BaseModelMixin):
    """角色权限表。"""

    __tablename__ = "sys_role"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    code = Column(String(32), nullable=False, unique=True, comment="角色编码：ADMIN/USER")
    name = Column(String(64), nullable=False, comment="角色名称")
    remark = Column(String(255), nullable=True, comment="角色说明")
    is_admin = Column(Boolean, nullable=False, default=False, comment="是否管理员角色")

    users = relationship("SysUser", back_populates="role")


class SysUser(Base, BaseModelMixin):
    """用户表。"""

    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(64), nullable=False, unique=True, comment="登录账号（唯一）")
    password_hash = Column(String(128), nullable=False, comment="密码哈希（bcrypt）")
    nickname = Column(String(64), nullable=True, comment="用户昵称")
    role_id = Column(Integer, ForeignKey("sys_role.id"), nullable=False, comment="角色ID")
    # 管理员单独配置的权限开关：是否允许查看/编辑他人记录册（管理员自身恒有全局权限）
    can_view_others = Column(Boolean, nullable=False, default=False, comment="允许查看他人记录册")
    can_edit_others = Column(Boolean, nullable=False, default=False, comment="允许编辑他人记录册")
    last_login_time = Column(DateTime, nullable=True, comment="最后登录时间")

    role = relationship("SysRole", back_populates="users", lazy="joined")

    @property
    def is_admin(self) -> bool:
        """是否管理员（依据角色的 is_admin 标志）。"""
        return bool(self.role is not None and self.role.is_admin)

    @property
    def display_name(self) -> str:
        """展示名：优先昵称。"""
        return self.nickname or self.username
