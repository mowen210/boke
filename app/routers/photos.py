# -*- coding: utf-8 -*-
"""照片接口：批量上传、模块内排序、备注、移动、删除。"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import SysUser
from app.schemas.photo import (
    PhotoBatchDeleteRequest,
    PhotoMoveRequest,
    PhotoNoteUpdate,
    PhotoSortRequest,
)
from app.services import photo_service

router = APIRouter(tags=["照片"])


@router.post("/api/albums/{album_id}/photos", summary="批量上传照片/视频")
async def upload_photos(
    album_id: int,
    module_id: Optional[int] = Form(None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """multipart 上传：module_id 目标模块（可选，默认第一个模块）；files 多文件（图片/视频可混传）。

    服务端校验：图片仅 jpg/png/gif/webp，视频仅 mp4/webm/mov/m4v/ogg，大小上限各自独立。
    """
    photos = await photo_service.upload_photos(db, user, album_id, module_id, files)
    return {"message": f"成功上传 {len(files)} 张照片", "data": photos}


@router.put("/api/albums/{album_id}/photos/sort", summary="模块内照片拖拽排序")
def sort_photos(
    album_id: int,
    body: PhotoSortRequest,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    return {
        "message": "排序已保存",
        "data": photo_service.reorder_photos(db, user, album_id, body.module_id, body.photo_ids),
    }


@router.put("/api/photos/{photo_id}/note", summary="更新照片备注")
def update_note(
    photo_id: int,
    body: PhotoNoteUpdate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    return {"message": "备注已保存", "data": photo_service.update_note(db, user, photo_id, body.note)}


@router.put("/api/photos/{photo_id}/move", summary="照片移动到其他模块")
def move_photo(
    photo_id: int,
    body: PhotoMoveRequest,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    return {"message": "照片已移动", "data": photo_service.move_photo(db, user, photo_id, body.module_id)}


@router.delete("/api/photos/{photo_id}", summary="删除照片")
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    photo_service.delete_photo(db, user, photo_id)
    return {"message": "照片已删除"}


@router.delete("/api/albums/{album_id}/photos", summary="批量删除照片（仅管理员）")
def batch_delete_photos(
    album_id: int,
    body: PhotoBatchDeleteRequest,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """JSON 请求体：photo_ids 待删除照片ID列表（须全部属于该记录册）。"""
    count = photo_service.batch_delete_photos(db, user, album_id, body.photo_ids)
    return {"message": f"已删除 {count} 张照片"}
