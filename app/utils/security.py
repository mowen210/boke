# -*- coding: utf-8 -*-
"""安全工具模块。

- 密码加密：passlib + bcrypt（禁止明文存储）
- 登录令牌：python-jose 签发/解析 JWT
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import logging

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import ALGORITHM, SECRET_KEY, TOKEN_EXPIRE_MINUTES

# passlib 1.7.4 在 bcrypt>=4.1 下会输出一次“(trapped) error reading bcrypt version”
# 无害警告，此处降噪（不影响功能）
logging.getLogger("passlib").setLevel(logging.ERROR)

# bcrypt 上下文：自动加盐哈希，兼容旧算法升级
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(raw_password: str) -> str:
    """明文密码 → bcrypt 哈希（存库使用）。"""
    return pwd_context.hash(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """校验明文密码与库中哈希是否匹配。"""
    return pwd_context.verify(raw_password, hashed_password)


def create_access_token(user_id: int, role_code: str, expires_minutes: Optional[int] = None) -> str:
    """签发 JWT 令牌。

    :param user_id: 用户ID（写入 sub 声明）
    :param role_code: 角色编码（写入 role 声明，便于扩展）
    :param expires_minutes: 有效期（分钟），缺省使用全局配置
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role_code, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    """解析 JWT，成功返回用户ID，失败（过期/伪造/格式错误）返回 None。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        return None
