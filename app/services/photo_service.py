# -*- coding: utf-8 -*-
"""照片服务：批量上传（格式/大小校验）、列表、备注、移动、删除、拖拽排序。"""
from typing import Optional, Sequence

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.module import AlbumModule
from app.models.photo import Photo
from app.models.user import SysUser
from app.services import module_service, permission_service, setting_service
from app.utils.file import guess_mime, save_image


def photo_dict(photo: Photo) -> dict:
    """照片记录 → 前端 JSON 结构。"""
    return {
        "id": photo.id,
        "album_id": photo.album_id,
        "module_id": photo.module_id,
        "file_path": photo.file_path,
        "original_name": photo.original_name,
        "file_size": photo.file_size,
        "file_type": photo.file_type,
        "note": photo.note,
        "sort_order": photo.sort_order,
        "create_time": photo.create_time.strftime("%Y-%m-%d %H:%M"),
    }


def get_photo(db: Session, photo_id: int) -> Optional[Photo]:
    """按主键加载未删除的照片。"""
    return (
        db.query(Photo)
        .filter(Photo.id == photo_id, Photo.is_deleted == False)  # noqa: E712
        .first()
    )


def list_photos(db: Session, album_id: int) -> list[dict]:
    """按模块排序号 + 照片排序号列出记录册内全部照片。"""
    photos = (
        db.query(Photo)
        .join(AlbumModule, AlbumModule.id == Photo.module_id)
        .filter(Photo.album_id == album_id, Photo.is_deleted == False)  # noqa: E712
        .order_by(AlbumModule.sort_order.asc(), Photo.sort_order.asc(), Photo.id.asc())
        .all()
    )
    return [photo_dict(p) for p in photos]


def _next_sort_order(db: Session, module_id: int) -> int:
    current = (
        db.query(func.max(Photo.sort_order))
        .filter(Photo.module_id == module_id, Photo.is_deleted == False)  # noqa: E712
        .scalar()
    )
    return (current or 0) + 1


def _load_module_for_upload(db: Session, album_id: int, module_id: Optional[int]) -> AlbumModule:
    """加载上传目标模块：未指定时落到记录册第一个模块。"""
    query = db.query(AlbumModule).filter(
        AlbumModule.album_id == album_id, AlbumModule.is_deleted == False  # noqa: E712
    )
    module = (
        query.filter(AlbumModule.id == module_id).first()
        if module_id
        else query.order_by(AlbumModule.sort_order.asc(), AlbumModule.id.asc()).first()
    )
    if module is None:
        raise HTTPException(status_code=400, detail="目标模块不存在")
    return module


async def upload_photos(
    db: Session,
    user: SysUser,
    album_id: int,
    module_id: Optional[int],
    files: Sequence[UploadFile],
) -> list[dict]:
    """批量上传照片：逐一校验（仅 jpg/png/gif/webp，单文件 ≤5MB），保存后入库。"""
    permission_service.assert_can_edit(db, user, album_id)
    module = _load_module_for_upload(db, album_id, module_id)
    max_size = setting_service.get_max_upload_size_mb(db) * 1024 * 1024

    created: list[dict] = []
    sort_order = _next_sort_order(db, module.id)
    for file in files:
        content = await file.read()
        path, size = save_image(file.filename or "", content, max_size)  # 校验失败抛 400
        photo = Photo(
            album_id=album_id,
            module_id=module.id,
            user_id=user.id,
            file_path=path,
            original_name=file.filename,
            file_size=size,
            file_type=guess_mime(file.filename or ""),
            sort_order=sort_order,
        )
        db.add(photo)
        sort_order += 1
    db.commit()
    # 重新按序查询，返回落库后的完整字段
    fresh = (
        db.query(Photo)
        .filter(Photo.album_id == album_id, Photo.module_id == module.id,
                Photo.is_deleted == False)  # noqa: E712
        .order_by(Photo.sort_order.asc(), Photo.id.asc())
        .all()
    )
    created = [photo_dict(p) for p in fresh]
    return created


def update_note(db: Session, user: SysUser, photo_id: int, note: Optional[str]) -> dict:
    """更新照片文字备注。"""
    photo = get_photo(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="照片不存在或已删除")
    permission_service.assert_can_edit(db, user, photo.album_id)
    photo.note = (note or "").strip() or None
    db.commit()
    db.refresh(photo)
    return photo_dict(photo)


def move_photo(db: Session, user: SysUser, photo_id: int, module_id: int) -> dict:
    """移动照片到同记录册的其他模块。"""
    photo = get_photo(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="照片不存在或已删除")
    permission_service.assert_can_edit(db, user, photo.album_id)
    module = module_service.get_module(db, module_id)
    if module is None or module.album_id != photo.album_id:
        raise HTTPException(status_code=400, detail="目标模块不存在")
    photo.module_id = module.id
    photo.sort_order = _next_sort_order(db, module.id)
    db.commit()
    db.refresh(photo)
    return photo_dict(photo)


def delete_photo(db: Session, user: SysUser, photo_id: int) -> None:
    """删除照片（软删除，物理文件保留以便恢复，见部署文档说明）。"""
    photo = get_photo(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="照片不存在或已删除")
    permission_service.assert_can_edit(db, user, photo.album_id)
    photo.is_deleted = True
    db.commit()


def batch_delete_photos(db: Session, user: SysUser, album_id: int, photo_ids: list[int]) -> int:
    """批量删除照片（软删除，仅管理员）。返回实际删除数量。

    :param photo_ids: 待删除照片ID列表，须全部属于该记录册且未删除，否则抛 400
    """
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可批量删除照片")
    photos = (
        db.query(Photo)
        .filter(
            Photo.album_id == album_id,
            Photo.id.in_(photo_ids),
            Photo.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    if len(photos) != len(set(photo_ids)):
        raise HTTPException(status_code=400, detail="删除列表包含无效照片")
    for photo in photos:
        photo.is_deleted = True
    db.commit()
    return len(photos)


def reorder_photos(
    db: Session, user: SysUser, album_id: int, module_id: int, photo_ids: list[int]
) -> list[dict]:
    """模块内照片拖拽排序：按传入顺序重写排序号。"""
    permission_service.assert_can_edit(db, user, album_id)
    photos = (
        db.query(Photo)
        .filter(
            Photo.album_id == album_id,
            Photo.module_id == module_id,
            Photo.id.in_(photo_ids),
            Photo.is_deleted == False,  # noqa: E712
        )
        .all()
    )
    if len(photos) != len(photo_ids):
        raise HTTPException(status_code=400, detail="排序列表包含无效照片")
    order_map = {pid: index for index, pid in enumerate(photo_ids)}
    for photo in photos:
        photo.sort_order = order_map[photo.id]
    db.commit()
    return list_photos(db, album_id)
