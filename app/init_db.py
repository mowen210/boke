# -*- coding: utf-8 -*-
"""启动初始化：建表 + 内置数据种子（角色、展示模板、初始管理员/演示账号）。

首次启动自动完成，重复启动幂等（已存在则跳过），保证“一套项目直接运行”。
"""
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import (
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)
from app.database import Base, SessionLocal, engine
from app.models import AlbumModule, PhotoAlbum, PhotoTemplate, SysRole, SysUser
from app.utils.security import hash_password


def _ensure_database() -> None:
    """若目标数据库不存在则自动创建（utf8mb4），免手工执行建库 SQL。"""
    server_url = (
        f"mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/?charset=utf8mb4"
    )
    server_engine = create_engine(server_url, pool_pre_ping=True)
    try:
        with server_engine.connect() as conn:
            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
                    f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            conn.commit()
    finally:
        server_engine.dispose()

# 内置展示模板：code / 名称 / CSS 类 / 说明 / 排序 / 是否默认
BUILTIN_TEMPLATES = [
    ("grid", "经典网格", "tpl-grid", "整齐统一的方形网格排版，简洁大方", 1, True),
    ("masonry", "瀑布流", "tpl-masonry", "按原始比例错落排布，长图短图自然混排", 2, False),
    ("polaroid", "拍立得", "tpl-polaroid", "白色相纸边框 + 轻微旋转，复古纪念册质感", 3, False),
    ("timeline", "时光轴", "tpl-timeline", "左侧时间轴线的纵向回忆列表", 4, False),
    ("compact", "紧凑小图", "tpl-compact", "高密度小图排版，一屏纵览全部照片", 5, False),
]


def _seed_roles(db: Session) -> dict[str, SysRole]:
    """内置角色：ADMIN 管理员 / USER 普通用户。"""
    roles: dict[str, SysRole] = {}
    for code, name, is_admin, remark in [
        ("ADMIN", "管理员", True, "拥有全局权限，可管理用户与所有记录册"),
        ("USER", "普通用户", False, "默认仅可查看、编辑自己的记录册"),
    ]:
        role = db.query(SysRole).filter(SysRole.code == code).first()
        if role is None:
            role = SysRole(code=code, name=name, is_admin=is_admin, remark=remark)
            db.add(role)
            db.flush()
        roles[code] = role
    return roles


def _seed_templates(db: Session) -> None:
    """内置展示模板。"""
    for code, name, css_class, description, sort_order, is_default in BUILTIN_TEMPLATES:
        exists = db.query(PhotoTemplate).filter(PhotoTemplate.code == code).first()
        if exists is None:
            db.add(
                PhotoTemplate(
                    code=code,
                    name=name,
                    css_class=css_class,
                    description=description,
                    sort_order=sort_order,
                    is_default=is_default,
                )
            )


def _seed_user(db: Session, role: SysRole, username: str, password: str,
               nickname: str, can_view_others: bool, can_edit_others: bool) -> None:
    """按配置创建初始账号（已存在则跳过）。"""
    exists = db.query(SysUser).filter(SysUser.username == username).first()
    if exists is not None:
        return
    db.add(
        SysUser(
            username=username,
            password_hash=hash_password(password),
            nickname=nickname,
            role_id=role.id,
            can_view_others=can_view_others,
            can_edit_others=can_edit_others,
        )
    )


def _seed_demo_album(db: Session) -> None:
    """为演示账号创建一本示例记录册（仅首次、演示账号无任何记录册时）。"""
    demo = db.query(SysUser).filter(SysUser.username == "demo").first()
    if demo is None:
        return
    has_album = (
        db.query(PhotoAlbum)
        .filter(PhotoAlbum.user_id == demo.id, PhotoAlbum.is_deleted == False)  # noqa: E712
        .first()
    )
    if has_album is not None:
        return
    template = (
        db.query(PhotoTemplate)
        .filter(PhotoTemplate.is_default == True)  # noqa: E712
        .first()
    )
    album = PhotoAlbum(
        user_id=demo.id,
        name="示例：我的第一本记录册",
        description="这是演示账号的示例记录册，可上传照片、新建模块、切换风格模板体验全部功能。",
        template_id=template.id if template else None,
    )
    db.add(album)
    db.flush()
    db.add(AlbumModule(album_id=album.id, title="生活日常", sort_order=1))
    db.add(AlbumModule(album_id=album.id, title="旅行风景", sort_order=2))


def init_database() -> None:
    """应用启动时执行：建库（如缺失）+ 建表 + 种子数据（幂等）。"""
    # 导入全部模型，确保 metadata 完整（Python 3.8 兼容写法，无需 import *）
    _ensure_database()
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        roles = _seed_roles(db)
        _seed_templates(db)
        # 初始管理员：admin / admin123（全局权限）
        _seed_user(db, roles["ADMIN"], "admin", "admin123", "系统管理员", True, True)
        # 演示普通用户：demo / 123456（仅自己的数据）
        _seed_user(db, roles["USER"], "demo", "123456", "演示用户", False, False)
        _seed_demo_album(db)
        db.commit()
    finally:
        db.close()
