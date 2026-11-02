# -*- coding: utf-8 -*-
"""记录册服务：列表（带权限过滤/模糊搜索）、新建、编辑、删除、模板切换。"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.album import PhotoAlbum
from app.models.module import AlbumModule
from app.models.photo import Photo
from app.models.template import PhotoTemplate
from app.models.user import SysUser
from app.schemas.album import AlbumCreate, AlbumUpdate
from app.services import permission_service

DEFAULT_TEMPLATE_CODE = "grid"


def get_album(db: Session, album_id: int) -> Optional[PhotoAlbum]:
    """按主键加载未删除的记录册。"""
    return (
        db.query(PhotoAlbum)
        .filter(PhotoAlbum.id == album_id, PhotoAlbum.is_deleted == False)  # noqa: E712
        .first()
    )


def _default_template(db: Session) -> Optional[PhotoTemplate]:
    """默认模板（无默认标记时取排序最前的一条）。"""
    return (
        db.query(PhotoTemplate)
        .filter(PhotoTemplate.is_deleted == False)  # noqa: E712
        .order_by(PhotoTemplate.is_default.desc(), PhotoTemplate.sort_order.asc())
        .first()
    )


def list_albums(db: Session, user: SysUser, keyword: str = "") -> list[dict]:
    """查询当前用户可访问的记录册列表（权限过滤 + 名称模糊搜索）。

    - 管理员 / 开启 can_view_others 的用户：返回全部记录册（附创建人昵称）
    - 普通用户：仅返回本人记录册（数据隔离）
    """
    query = (
        db.query(PhotoAlbum, SysUser.nickname, SysUser.username)
        .join(SysUser, SysUser.id == PhotoAlbum.user_id)
        .filter(PhotoAlbum.is_deleted == False)  # noqa: E712
    )
    if not permission_service.can_view_albums_of(user, owner_id=-1):
        query = query.filter(PhotoAlbum.user_id == user.id)
    if keyword:
        query = query.filter(PhotoAlbum.name.like(f"%{keyword.strip()}%"))
    rows = query.order_by(PhotoAlbum.update_time.desc()).all()

    # 一次性统计各记录册照片数，避免 N+1 查询
    album_ids = [a.id for a, _, _ in rows]
    counts: dict[int, int] = {}
    if album_ids:
        stat = (
            db.query(Photo.album_id, func.count(Photo.id))
            .filter(Photo.album_id.in_(album_ids), Photo.is_deleted == False)  # noqa: E712
            .group_by(Photo.album_id)
            .all()
        )
        counts = {album_id: cnt for album_id, cnt in stat}

    return [
        {
            "id": album.id,
            "name": album.name,
            "description": album.description,
            "cover_image": album.cover_image,
            "template_id": album.template_id,
            "create_time": album.create_time.strftime("%Y-%m-%d %H:%M"),
            "owner_id": album.user_id,
            "owner_nickname": nickname or username,
            "is_owner": album.user_id == user.id,
            "can_edit": permission_service.can_edit_album(user, album),
            "photo_count": counts.get(album.id, 0),
        }
        for album, nickname, username in rows
    ]


def album_brief(db: Session, user: SysUser, album: PhotoAlbum) -> dict:
    """记录册基础信息（详情页头部使用）。"""
    count = (
        db.query(func.count(Photo.id))
        .filter(Photo.album_id == album.id, Photo.is_deleted == False)  # noqa: E712
        .scalar()
    )
    return {
        "id": album.id,
        "name": album.name,
        "description": album.description,
        "cover_image": album.cover_image,
        "template_id": album.template_id,
        "create_time": album.create_time.strftime("%Y-%m-%d %H:%M"),
        "owner_id": album.user_id,
        "owner_nickname": (album.user.nickname or album.user.username) if album.user else "",
        "is_owner": album.user_id == user.id,
        "can_edit": permission_service.can_edit_album(user, album),
        "photo_count": int(count or 0),
    }


def create_album(db: Session, user: SysUser, data: AlbumCreate) -> dict:
    """新建空白记录册：自动创建一个“默认模块”，并绑定默认展示模板。"""
    template = _default_template(db)
    album = PhotoAlbum(
        user_id=user.id,
        name=data.name.strip(),
        description=(data.description or "").strip() or None,
        template_id=template.id if template else None,
    )
    db.add(album)
    db.flush()  # 取得 album.id
    db.add(AlbumModule(album_id=album.id, title="默认模块", sort_order=0))
    db.commit()
    db.refresh(album)
    return album_brief(db, user, album)


def update_album(
    db: Session,
    user: SysUser,
    album_id: int,
    data: AlbumUpdate,
    cover_path: Optional[str] = None,
) -> dict:
    """编辑记录册基础信息：名称 / 简介 / 封面（cover_path 为已保存的相对路径）。"""
    album = permission_service.assert_can_edit(db, user, album_id)
    if data.name is not None:
        album.name = data.name.strip()
    if data.description is not None:
        album.description = data.description.strip() or None
    if cover_path:
        album.cover_image = cover_path
    db.commit()
    db.refresh(album)
    return album_brief(db, user, album)


def update_template(db: Session, user: SysUser, album_id: int, template_id: int) -> dict:
    """一键切换记录册展示模板。"""
    album = permission_service.assert_can_edit(db, user, album_id)
    template = (
        db.query(PhotoTemplate)
        .filter(PhotoTemplate.id == template_id, PhotoTemplate.is_deleted == False)  # noqa: E712
        .first()
    )
    if template is None:
        raise HTTPException(status_code=400, detail="模板不存在")
    album.template_id = template.id
    db.commit()
    db.refresh(album)
    return album_brief(db, user, album)


def delete_album(db: Session, user: SysUser, album_id: int) -> None:
    """删除记录册：软删除记录册及其下所有模块、照片（文件保留在 upload 目录）。"""
    album = permission_service.assert_can_edit(db, user, album_id)
    now_deleted = True
    db.query(AlbumModule).filter(
        AlbumModule.album_id == album.id, AlbumModule.is_deleted == False  # noqa: E712
    ).update({"is_deleted": now_deleted}, synchronize_session=False)
    db.query(Photo).filter(
        Photo.album_id == album.id, Photo.is_deleted == False  # noqa: E712
    ).update({"is_deleted": now_deleted}, synchronize_session=False)
    album.is_deleted = True
    db.commit()
