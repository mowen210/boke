# -*- coding: utf-8 -*-
"""记录册接口：列表/新建/编辑/删除/模板切换/详情数据。"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import SysUser
from app.schemas.album import AlbumCreate, AlbumUpdate, TemplateUpdate
from app.services import (
    album_service,
    module_service,
    permission_service,
    photo_service,
    setting_service,
)
from app.utils.file import save_image

router = APIRouter(prefix="/api/albums", tags=["记录册"])


@router.get("", summary="记录册列表（权限过滤 + 名称模糊搜索）")
def list_albums(
    q: str = "",
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """当前用户可访问的记录册列表；q 为名称模糊搜索关键字。"""
    return {"message": "ok", "data": album_service.list_albums(db, user, q)}


@router.post("", summary="新建记录册")
def create_album(
    body: AlbumCreate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    return {"message": "创建成功", "data": album_service.create_album(db, user, body)}


@router.get("/{album_id}", summary="记录册详情数据（模块+照片+模板）")
def get_album_detail(
    album_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """详情页数据：基础信息、模块列表、照片列表、可选模板。"""
    album = permission_service.assert_can_view(db, user, album_id)
    return {
        "message": "ok",
        "data": {
            "album": album_service.album_brief(db, user, album),
            "modules": module_service.list_modules(db, album.id),
            "photos": photo_service.list_photos(db, album.id),
            "max_upload_size_mb": setting_service.get_max_upload_size_mb(db),
        },
    }


@router.put("/{album_id}", summary="编辑记录册基础信息（含更换封面，multipart）")
def update_album(
    album_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    cover: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """multipart 表单：name/description 文本，cover 封面图片（可选，走上传校验）。"""
    cover_path = None
    if cover and cover.filename:
        content = cover.file.read()
        max_size = setting_service.get_max_upload_size_mb(db) * 1024 * 1024
        cover_path, _ = save_image(cover.filename, content, max_size)
    body = AlbumUpdate(name=name, description=description)
    return {"message": "保存成功", "data": album_service.update_album(db, user, album_id, body, cover_path)}


@router.delete("/{album_id}", summary="删除记录册（级联软删除模块与照片）")
def delete_album(
    album_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    album_service.delete_album(db, user, album_id)
    return {"message": "删除成功"}


@router.put("/{album_id}/template", summary="切换展示模板（一键换风格）")
def update_template(
    album_id: int,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    return {"message": "模板已切换", "data": album_service.update_template(db, user, album_id, body.template_id)}
