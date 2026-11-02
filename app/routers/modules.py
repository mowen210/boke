# -*- coding: utf-8 -*-
"""模块接口：新增、改名、删除、拖拽排序。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import SysUser
from app.schemas.module import ModuleCreate, ModuleSortRequest, ModuleUpdate
from app.services import module_service

router = APIRouter(prefix="/api/modules", tags=["模块"])


@router.put("/sort", summary="模块拖拽排序")
def sort_modules(
    body: ModuleSortRequest,
    album_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """album_id 查询参数 + body.module_ids 有序列表。

    注意：本路由必须定义在 /{module_id} 之前，避免 "sort" 被当作路径参数匹配。
    """
    return {
        "message": "排序已保存",
        "data": module_service.reorder_modules(db, user, album_id, body.module_ids),
    }


@router.post("", summary="新增模块")
def create_module(
    body: ModuleCreate,
    album_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """album_id 以查询参数传入（?album_id=1）。"""
    return {"message": "模块已创建", "data": module_service.create_module(db, user, album_id, body)}


@router.put("/{module_id}", summary="修改模块标题")
def update_module(
    module_id: int,
    body: ModuleUpdate,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    return {"message": "模块已更新", "data": module_service.update_module(db, user, module_id, body)}


@router.delete("/{module_id}", summary="删除模块（照片自动移入剩余模块）")
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    module_service.delete_module(db, user, module_id)
    return {"message": "模块已删除"}
