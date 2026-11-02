# -*- coding: utf-8 -*-
"""管理员服务：用户列表与用户级权限开关配置（仅管理员可调用）。"""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.album import PhotoAlbum
from app.models.user import SysRole, SysUser
from app.schemas.user import PermissionUpdate


def _ensure_admin(user: SysUser) -> None:
    """操作者必须是管理员。"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可执行该操作")


def list_users(db: Session, operator: SysUser) -> list[dict]:
    """用户管理列表：账号、角色、权限开关、记录册数量。"""
    _ensure_admin(operator)
    rows = (
        db.query(SysUser, SysRole, func.count(PhotoAlbum.id))
        .join(SysRole, SysRole.id == SysUser.role_id)
        .outerjoin(
            PhotoAlbum,
            (PhotoAlbum.user_id == SysUser.id) & (PhotoAlbum.is_deleted == False),  # noqa: E712
        )
        .filter(SysUser.is_deleted == False)  # noqa: E712
        .group_by(SysUser.id)
        .order_by(SysUser.id.asc())
        .all()
    )
    return [
        {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "display_name": user.display_name,
            "role_code": role.code,
            "role_name": role.name,
            "is_admin": bool(role.is_admin),
            "can_view_others": bool(user.can_view_others),
            "can_edit_others": bool(user.can_edit_others),
            "album_count": int(count or 0),
            "last_login_time": (
                user.last_login_time.strftime("%Y-%m-%d %H:%M") if user.last_login_time else ""
            ),
        }
        for user, role, count in rows
    ]


def update_permissions(
    db: Session, operator: SysUser, user_id: int, data: PermissionUpdate
) -> dict:
    """单独配置指定用户的“查看/编辑他人记录册”权限开关。"""
    _ensure_admin(operator)
    user = (
        db.query(SysUser)
        .filter(SysUser.id == user_id, SysUser.is_deleted == False)  # noqa: E712
        .first()
    )
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.can_view_others is not None:
        user.can_view_others = data.can_view_others
    if data.can_edit_others is not None:
        user.can_edit_others = data.can_edit_others
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "can_view_others": bool(user.can_view_others),
        "can_edit_others": bool(user.can_edit_others),
    }
