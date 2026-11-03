# -*- coding: utf-8 -*-
"""认证接口：登录（签发 JWT Cookie）、退出、当前用户信息。"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import COOKIE_NAME, TOKEN_EXPIRE_MINUTES
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import SysUser
from app.schemas.user import LoginRequest, PasswordChange
from app.services import auth_service
from app.utils.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", summary="账号密码登录")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> JSONResponse:
    """校验账号密码，签发 JWT 并写入 HttpOnly Cookie。

    - 前端已做非空校验，此处后端二次校验（Pydantic 长度规则 + 账号密码比对）
    """
    user = auth_service.authenticate(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = create_access_token(user.id, user.role.code if user.role else "USER")
    resp = JSONResponse(
        content={
            "message": "登录成功",
            "data": {
                "id": user.id,
                "username": user.username,
                "nickname": user.display_name,
                "is_admin": user.is_admin,
            },
        }
    )
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,                        # 禁止 JS 读取，防 XSS 窃取令牌
        samesite="lax",                       # 基础 CSRF 防护
        max_age=TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return resp


@router.post("/logout", summary="退出登录")
def logout() -> JSONResponse:
    """清除登录 Cookie。"""
    resp = JSONResponse(content={"message": "已退出登录"})
    resp.delete_cookie(key=COOKIE_NAME, path="/")
    return resp


@router.get("/me", summary="当前登录用户信息")
def me(user: SysUser = Depends(get_current_user)) -> dict:
    """返回当前登录用户（用于前端渲染导航/权限 UI）。"""
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.display_name,
        "is_admin": user.is_admin,
        "can_view_others": bool(user.can_view_others),
        "can_edit_others": bool(user.can_edit_others),
    }


@router.put("/password", summary="修改自身密码")
def change_password(
    body: PasswordChange,
    db: Session = Depends(get_db),
    user: SysUser = Depends(get_current_user),
) -> dict:
    """已登录用户修改自身密码：校验原密码 + 两次新密码一致。"""
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")
    if body.new_password == body.old_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    auth_service.change_password(db, user, body.old_password, body.new_password)
    return {"message": "密码修改成功", "data": {"username": user.username}}
