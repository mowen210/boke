# -*- coding: utf-8 -*-
"""管理员接口：用户列表、用户权限开关配置、系统设置（上传大小上限）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import SysUser
from app.schemas.setting import SettingUpdate
from app.schemas.user import PermissionUpdate, UserCreate
from app.services import admin_service, setting_service

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


@router.get("/settings", summary="系统设置（当前含上传大小上限）")
def get_settings(
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """仅管理员可访问。"""
    return {"message": "ok", "data": setting_service.get_settings(db, user)}


@router.put("/settings", summary="更新系统设置")
def update_settings(
    body: SettingUpdate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """仅管理员可访问；max_upload_size 单位为 MB（1-100），即时生效。"""
    return {
        "message": "设置已保存",
        "data": setting_service.update_settings(db, user, body),
    }
