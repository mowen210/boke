# -*- coding: utf-8 -*-
"""全局鉴权依赖。

- get_current_user：API 依赖，未登录抛出 401（前端 JS 捕获后跳转登录页）
- require_page_user：页面依赖，未登录抛出 PageLoginRequired，由全局处理器 302 跳转 /login

令牌来源优先级：Cookie（浏览器页面/同源 fetch 自动携带） > Authorization: Bearer 头（开放 API 调用）。
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import PageLoginRequired
from app.models.user import SysUser
from app.services import auth_service
from app.config import COOKIE_NAME
from app.utils.security import decode_access_token


def _extract_token(request: Request) -> Optional[str]:
    """从 Cookie 或 Authorization 头中提取 JWT 令牌。"""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
    return token or None


def try_get_user(request: Request, db: Session) -> Optional[SysUser]:
    """解析令牌并加载用户；任何失败均返回 None（不抛错，便于页面跳转处理）。"""
    token = _extract_token(request)
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    return auth_service.get_user(db, user_id)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> SysUser:
    """API 接口通用依赖：必须已登录，否则 401。"""
    user = try_get_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return user


def require_page_user(request: Request, db: Session = Depends(get_db)) -> SysUser:
    """页面路由通用依赖：未登录抛出 PageLoginRequired → 302 跳转登录页。"""
    user = try_get_user(request, db)
    if user is None:
        raise PageLoginRequired()
    return user
