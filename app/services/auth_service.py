# -*- coding: utf-8 -*-
"""认证服务：账号校验与用户加载。"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import SysUser
from app.utils.security import hash_password, verify_password


def authenticate(db: Session, username: str, password: str) -> Optional[SysUser]:
    """账号密码校验。

    :return: 校验通过返回用户对象；账号不存在 / 密码错误 / 已删除均返回 None
    """
    user = (
        db.query(SysUser)
        .filter(SysUser.username == username, SysUser.is_deleted == False)  # noqa: E712
        .first()
    )
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_time = datetime.now()
    db.commit()
    return user


def get_user(db: Session, user_id: int) -> Optional[SysUser]:
    """按主键加载有效用户（含角色，供鉴权使用）。"""
    return (
        db.query(SysUser)
        .filter(SysUser.id == user_id, SysUser.is_deleted == False)  # noqa: E712
        .first()
    )


def change_password(db: Session, user: SysUser, old_password: str, new_password: str) -> None:
    """修改自身密码：先校验原密码，再以 bcrypt 哈希写入新密码。

    :raises HTTPException: 原密码错误时 400
    """
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(new_password)
    db.commit()
