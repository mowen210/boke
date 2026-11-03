# -*- coding: utf-8 -*-
"""管理员接口：用户列表与用户权限开关配置。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import SysUser
from app.schemas.user import PermissionUpdate, UserCreate
from app.services import admin_service

router = APIRouter(prefix="/api/admin", tags=["管理员"])


@router.get("/users", summary="用户管理列表")
def list_users(
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """仅管理员可访问；返回用户、角色、权限开关、记录册数量。"""
    return {"message": "ok", "data": admin_service.list_users(db, user)}


@router.post("/users", summary="新增用户")
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """管理员新增用户：指定账号、初始密码、角色与权限开关。"""
    return {"message": "用户创建成功", "data": admin_service.create_user(db, user, body)}


@router.put("/users/{user_id}/permissions", summary="配置用户权限开关")
def update_permissions(
    user_id: int,
    body: PermissionUpdate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """单独设置指定用户是否允许查看/编辑他人记录册。"""
    return {
        "message": "权限已更新",
        "data": admin_service.update_permissions(db, user, user_id, body),
    }
