# -*- coding: utf-8 -*-
"""页面路由：登录页、首页（记录册列表）、记录册详情页。

页面由 Jinja2 模板渲染；未登录访问首页/详情页自动 302 跳转登录页。
详情页数据以 JSON 形式内嵌到模板中，由原生 JS 接管交互（上传/拖拽/弹窗等）。
"""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.database import get_db
from app.dependencies import require_page_user, try_get_user
from app.models.template import PhotoTemplate
from app.models.user import SysUser
from app.services import album_service, module_service, permission_service, photo_service, setting_service

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/login", response_class=HTMLResponse, summary="登录页")
def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """已登录用户访问登录页时直接跳转首页。"""
    user: Optional[SysUser] = try_get_user(request, db)
    if user is not None:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={})


@router.get("/", response_class=HTMLResponse, summary="首页（记录册列表）")
def home(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_page_user),
) -> HTMLResponse:
    """卡片布局展示当前用户可访问的记录册，支持名称模糊搜索。"""
    albums = album_service.list_albums(db, user, q)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.display_name,
                "is_admin": user.is_admin,
                "can_view_others": bool(user.can_view_others),
            },
            "albums": albums,
            "keyword": q,
        },
    )


@router.get("/album/{album_id}", response_class=HTMLResponse, summary="记录册详情页")
def album_detail(
    request: Request,
    album_id: int,
    db: Session = Depends(get_db),
    user: SysUser = Depends(require_page_user),
) -> HTMLResponse:
    """详情页：内嵌 album/modules/photos/templates JSON 数据供前端 JS 渲染。"""
    album = permission_service.assert_can_view(db, user, album_id)
    templates_list = (
        db.query(PhotoTemplate)
        .filter(PhotoTemplate.is_deleted == False)  # noqa: E712
        .order_by(PhotoTemplate.sort_order.asc(), PhotoTemplate.id.asc())
        .all()
    )
    payload = {
        "album": album_service.album_brief(db, user, album),
        "modules": module_service.list_modules(db, album.id),
        "photos": photo_service.list_photos(db, album.id),
        "templates": [
            {
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "css_class": t.css_class,
                "description": t.description,
                "is_default": bool(t.is_default),
            }
            for t in templates_list
        ],
        "current_user": {
            "id": user.id,
            "nickname": user.display_name,
            "is_admin": user.is_admin,
        },
        "max_upload_size_mb": setting_service.get_max_upload_size_mb(db),
    }
    current_css = next(
        (t["css_class"] for t in payload["templates"] if t["id"] == album.template_id),
        "tpl-grid",
    )
    return templates.TemplateResponse(
        request=request,
        name="detail.html",
        context={"payload": payload, "current_css": current_css, "user": payload["current_user"]},
    )
