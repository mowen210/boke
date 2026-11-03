# -*- coding: utf-8 -*-
"""系统设置服务：管理员可调的运行时配置（当前支持上传大小上限）。

设置持久化在 sys_setting 表；未写入时回退到 app/config.py 的默认值，
保证首次启动 / 旧库升级场景均可直接运行。
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import MAX_UPLOAD_SIZE_MB
from app.models.setting import SysSetting
from app.models.user import SysUser
from app.schemas.setting import MAX_UPLOAD_SIZE_LIMIT, SettingUpdate

SETTING_MAX_UPLOAD_SIZE = "max_upload_size"


def _get_raw(db: Session, key: str) -> str | None:
    row = db.query(SysSetting).filter(SysSetting.setting_key == key).first()
    return row.setting_value if row else None


def _set_value(db: Session, key: str, value: str, remark: str) -> None:
    row = db.query(SysSetting).filter(SysSetting.setting_key == key).first()
    if row is None:
        db.add(SysSetting(setting_key=key, setting_value=value, remark=remark))
    else:
        row.setting_value = value


def get_max_upload_size_mb(db: Session) -> int:
    """当前上传大小上限（MB）：sys_setting 优先，缺失/非法时回退默认值。"""
    raw = _get_raw(db, SETTING_MAX_UPLOAD_SIZE)
    if raw is None:
        return MAX_UPLOAD_SIZE_MB
    try:
        value = int(raw)
    except ValueError:
        return MAX_UPLOAD_SIZE_MB
    if value < 1:
        return MAX_UPLOAD_SIZE_MB
    return min(value, MAX_UPLOAD_SIZE_LIMIT)


def _ensure_admin(user: SysUser) -> None:
    """操作者必须是管理员。"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可执行该操作")


def get_settings(db: Session, operator: SysUser) -> dict:
    """读取系统设置（仅管理员）。"""
    _ensure_admin(operator)
    return {"max_upload_size": get_max_upload_size_mb(db)}


def update_settings(db: Session, operator: SysUser, data: SettingUpdate) -> dict:
    """更新系统设置（仅管理员），返回更新后的完整设置。"""
    _ensure_admin(operator)
    if data.max_upload_size is not None:
        _set_value(
            db,
            SETTING_MAX_UPLOAD_SIZE,
            str(data.max_upload_size),
            f"上传大小上限（MB），范围 1-{MAX_UPLOAD_SIZE_LIMIT}",
        )
    db.commit()
    return get_settings(db, operator)


def seed_settings(db: Session) -> None:
    """启动初始化：写入缺失设置的默认值（幂等）。"""
    if _get_raw(db, SETTING_MAX_UPLOAD_SIZE) is None:
        _set_value(
            db,
            SETTING_MAX_UPLOAD_SIZE,
            str(MAX_UPLOAD_SIZE_MB),
            f"上传大小上限（MB），范围 1-{MAX_UPLOAD_SIZE_LIMIT}",
        )
