# -*- coding: utf-8 -*-
"""ORM 模型包：汇总导出所有模型，便于 Base.metadata.create_all 一次性建表。"""
from app.models.user import SysRole, SysUser
from app.models.album import PhotoAlbum
from app.models.module import AlbumModule
from app.models.photo import Photo
from app.models.template import PhotoTemplate
from app.models.setting import SysSetting

__all__ = ["SysRole", "SysUser", "PhotoAlbum", "AlbumModule", "Photo", "PhotoTemplate", "SysSetting"]
