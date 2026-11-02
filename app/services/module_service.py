# -*- coding: utf-8 -*-
"""模块服务：记录册内自定义模块的增删改查与拖拽排序。"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.album import PhotoAlbum
from app.models.module import AlbumModule
from app.models.photo import Photo
from app.models.user import SysUser
from app.schemas.module import ModuleCreate, ModuleUpdate
from app.services import permission_service

DEFAULT_MODULE_TITLE = "默认模块"


def get_module(db: Session, module_id: int) -> Optional[AlbumModule]:
    """按主键加载未删除的模块。"""
    return (
        db.query(AlbumModule)
        .filter(AlbumModule.id == module_id, AlbumModule.is_deleted == False)  # noqa: E712
        .first()
    )


def list_modules(db: Session, album_id: int) -> list[dict]:
    """列出记录册下全部模块（含照片计数），按排序号升序。"""
    rows = (
        db.query(AlbumModule, func.count(Photo.id))
        .outerjoin(
            Photo,
            (Photo.module_id == AlbumModule.id) & (Photo.is_deleted == False),  # noqa: E712
        )
        .filter(AlbumModule.album_id == album_id, AlbumModule.is_deleted == False)  # noqa: E712
        .group_by(AlbumModule.id)
        .order_by(AlbumModule.sort_order.asc(), AlbumModule.id.asc())
        .all()
    )
    return [
        {
            "id": module.id,
            "album_id": module.album_id,
            "title": module.title,
            "sort_order": module.sort_order,
            "photo_count": int(count or 0),
        }
        for module, count in rows
    ]


def _next_sort_order(db: Session, album_id: int) -> int:
    """计算模块列表末尾的排序号。"""
    current = (
        db.query(func.max(AlbumModule.sort_order))
        .filter(AlbumModule.album_id == album_id, AlbumModule.is_deleted == False)  # noqa: E712
        .scalar()
    )
    return (current or 0) + 1


def _ensure_module_in_album(module: AlbumModule, album: PhotoAlbum) -> None:
    """防止跨记录册越权操作模块。"""
    if module.album_id != album.id:
        raise HTTPException(status_code=400, detail="模块不属于该记录册")


def create_module(db: Session, user: SysUser, album_id: int, data: ModuleCreate) -> dict:
    """新增模块。"""
    permission_service.assert_can_edit(db, user, album_id)
    module = AlbumModule(
        album_id=album_id,
        title=data.title.strip(),
        sort_order=_next_sort_order(db, album_id),
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return {"id": module.id, "album_id": module.album_id, "title": module.title,
            "sort_order": module.sort_order, "photo_count": 0}


def update_module(db: Session, user: SysUser, module_id: int, data: ModuleUpdate) -> dict:
    """修改模块标题。"""
    module = get_module(db, module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="模块不存在或已删除")
    permission_service.assert_can_edit(db, user, module.album_id)
    module.title = data.title.strip()
    db.commit()
    db.refresh(module)
    return {"id": module.id, "album_id": module.album_id, "title": module.title,
            "sort_order": module.sort_order}


def delete_module(db: Session, user: SysUser, module_id: int) -> None:
    """删除模块。

    若模块内仍有照片，则先将照片移动到记录册的第一个剩余模块
    （若无剩余模块则自动创建“默认模块”），避免照片悬空。
    """
    module = get_module(db, module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="模块不存在或已删除")
    permission_service.assert_can_edit(db, user, module.album_id)

    remaining = (
        db.query(AlbumModule)
        .filter(
            AlbumModule.album_id == module.album_id,
            AlbumModule.id != module.id,
            AlbumModule.is_deleted == False,  # noqa: E712
        )
        .order_by(AlbumModule.sort_order.asc(), AlbumModule.id.asc())
        .first()
    )
    if remaining is None:
        remaining = AlbumModule(
            album_id=module.album_id, title=DEFAULT_MODULE_TITLE, sort_order=module.sort_order
        )
        db.add(remaining)
        db.flush()

    db.query(Photo).filter(
        Photo.module_id == module.id, Photo.is_deleted == False  # noqa: E712
    ).update({"module_id": remaining.id}, synchronize_session=False)
    module.is_deleted = True
    db.commit()


def reorder_modules(db: Session, user: SysUser, album_id: int, module_ids: list[int]) -> list[dict]:
    """按传入顺序重写模块排序号（拖拽排序）。"""
    album = permission_service.assert_can_edit(db, user, album_id)
    modules = (
        db.query(AlbumModule)
        .filter(
            AlbumModule.album_id == album.id,
            AlbumModule.id.in_(module_ids),
            AlbumModule.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    if len(modules) != len(module_ids):
        raise HTTPException(status_code=400, detail="排序列表包含无效模块")
    order_map = {module_id: index for index, module_id in enumerate(module_ids)}
    for module in modules:
        module.sort_order = order_map[module.id]
    db.commit()
    return list_modules(db, album.id)
