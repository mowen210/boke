# -*- coding: utf-8 -*-
"""模板渲染测试：验证 login/index/detail 三个 Jinja2 模板可正常渲染（不依赖 MySQL）。"""
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def make_request():
    return Request(scope={"type": "http", "method": "GET", "path": "/", "headers": [], "query_string": b""})


user = {"id": 1, "username": "demo", "nickname": "演示用户", "is_admin": True, "can_view_others": False}

albums = [{
    "id": 1, "name": "测试记录册", "description": "简介", "cover_image": "/static/img/default_cover.svg",
    "template_id": 1, "create_time": "2026-11-01 10:00", "owner_id": 1, "owner_nickname": "演示用户",
    "is_owner": True, "can_edit": True, "photo_count": 3,
}]

payload = {
    "album": dict(albums[0], owner_nickname="演示用户", can_edit=True),
    "modules": [{"id": 1, "album_id": 1, "title": "默认模块", "sort_order": 1, "photo_count": 1}],
    "photos": [{
        "id": 1, "album_id": 1, "module_id": 1, "file_path": "/upload/202611/x.jpg",
        "original_name": "x.jpg", "file_size": 1024, "file_type": "image/jpeg",
        "note": "<b>备注</b>", "sort_order": 1, "create_time": "2026-11-01 10:00",
    }],
    "templates": [
        {"id": 1, "code": "grid", "name": "经典网格", "css_class": "tpl-grid", "description": "", "is_default": True},
        {"id": 2, "code": "masonry", "name": "瀑布流", "css_class": "tpl-masonry", "description": "", "is_default": False},
    ],
    "current_user": {"id": 1, "nickname": "演示用户", "is_admin": False},
}

req = make_request()
html = templates.TemplateResponse(request=req, name="login.html", context={}).body.decode()
assert "login-form" in html
print("[PASS] login.html 渲染成功")

html = templates.TemplateResponse(request=req, name="index.html",
                                  context={"user": user, "albums": albums, "keyword": ""}).body.decode()
assert "album-grid" in html and "index-data" in html
# tojson 默认将非 ASCII 转义（\uXXXX），浏览器 JSON.parse 可正常还原
assert "\\u6d4b\\u8bd5\\u8bb0\\u5f55\\u518c" in html
print("[PASS] index.html 渲染成功")

html = templates.TemplateResponse(request=req, name="detail.html",
                                  context={"payload": payload, "current_css": "tpl-grid"}).body.decode()
assert "page-data" in html and "lightbox" in html and "upload-modal" in html and "tpl-grid" in html
# tojson 应转义 < 防止 </script> 注入（note 含 <b> 标签）
assert "<b>" not in html.split("page-data", 1)[1].split("</script>", 1)[0]
print("[PASS] detail.html 渲染成功（含 JSON 内嵌与 XSS 转义）")
print("ALL TEMPLATE TESTS PASSED")
