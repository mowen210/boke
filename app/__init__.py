# -*- coding: utf-8 -*-
"""照片记录册管理系统（photo_album）应用包。

整体分层：
- routers   路由层：接收 HTTP 请求，参数校验，调用 service
- services  业务层：业务逻辑、权限判断、事务操作
- models    数据层：SQLAlchemy ORM 模型（MySQL 持久化）
- schemas   数据校验层：Pydantic 请求体模型
- utils     工具层：安全（JWT/bcrypt）、文件校验保存
"""
