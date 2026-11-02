# -*- coding: utf-8 -*-
"""权限服务：集中实现“数据隔离 + 越权判断”。

权限规则：
- 管理员（角色 is_admin=True）：全局权限，可查看/编辑所有数据
- 普通用户：默认仅能查看/编辑自己创建的记录册、模块、照片（数据隔离）
- 用户级开关：管理员可为指定用户单独开启
  can_view_others（查看他人记录册）/ can_edit_others（编辑他人记录册）
所有业务查询均通过本模块的方法附加权限条件，禁止在路由层裸查。
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.album import PhotoAlbum
from app.models.user import SysUser
from app.services import album_service


def can_view_albums_of(user: SysUser, owner_id: int) -> bool:
    """判断用户是否可以查看指定用户（owner_id）的记录册列表。"""
    if user.is_admin:
        return True
    return user.id == owner_id or bool(user.can_view_others)


def can_edit_album(user: SysUser, album: PhotoAlbum) -> bool:
    """判断用户是否可以编辑指定记录册。"""
    if user.is_admin:
        return True
    return album.user_id == user.id or bool(user.can_edit_others)


def assert_can_view(db: Session, user: SysUser, album_id: int) -> PhotoAlbum:
    """加载记录册并校验查看权限，无权限抛 403，不存在抛 404。"""
    album = album_service.get_album(db, album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="记录册不存在或已删除")
    if not can_view_albums_of(user, album.user_id):
        # 越权访问他人数据：统一按不存在处理，避免信息泄露
        raise HTTPException(status_code=403, detail="无权访问该记录册")
    return album


def assert_can_edit(db: Session, user: SysUser, album_id: int) -> PhotoAlbum:
    """加载记录册并校验编辑权限，无权限抛 403，不存在抛 404。"""
    album = album_service.get_album(db, album_id)
    if album is None:
        raise HTTPException(status_code=404, detail="记录册不存在或已删除")
    if not can_edit_album(user, album):
        raise HTTPException(status_code=403, detail="无权编辑该记录册")
    return album
