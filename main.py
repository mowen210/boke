# -*- coding: utf-8 -*-
"""照片记录册管理系统入口。

启动方式：
    uvicorn main:app --host 0.0.0.0 --port 8000
    或开发模式：uvicorn main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, UPLOAD_DIR
from app.exceptions import PageLoginRequired
from app.init_db import init_database
from app.routers import admin, albums, auth, modules, pages, photos


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期：启动时建表并初始化内置数据（角色/模板/初始账号）。"""
    init_database()
    yield


app = FastAPI(
    title="照片记录册管理系统",
    description="FastAPI + Jinja2 + MySQL 的照片记录册（相册纪念册）管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# 静态资源：内置 static 目录（css/js/图片）与 upload 上传目录
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/upload", StaticFiles(directory=str(UPLOAD_DIR)), name="upload")

# 业务路由
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(albums.router)
app.include_router(modules.router)
app.include_router(photos.router)
app.include_router(admin.router)


@app.exception_handler(PageLoginRequired)
async def page_login_required_handler(request: Request, exc: PageLoginRequired) -> RedirectResponse:
    """页面未登录：302 跳转登录页。"""
    return RedirectResponse(url="/login", status_code=302)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc) -> JSONResponse:
    """统一 404 JSON 返回（API 与页面均给出友好提示）。"""
    return JSONResponse(status_code=404, content={"detail": "资源不存在"})
