# -*- coding: utf-8 -*-
"""数据库连接与会话管理。

采用 SQLAlchemy 2.x 风格，同步引擎 + PyMySQL 驱动连接 MySQL。
每个请求通过 FastAPI 依赖注入获取独立会话，请求结束自动关闭。
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

# pool_pre_ping 防止 MySQL 连接超时失效；pool_recycle 定期回收连接
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

# 所有 ORM 模型的公共基类
Base = declarative_base()


def get_db():
    """FastAPI 依赖：为每个请求提供数据库会话，请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
