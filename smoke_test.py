# -*- coding: utf-8 -*-
"""本地冒烟测试：不连接 MySQL（不触发 lifespan），验证页面渲染、鉴权拦截、静态资源。"""
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)  # 不用 with，跳过 lifespan（init_database）

failures = []


def check(name, cond, extra=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {extra}")
    if not cond:
        failures.append(name)


# 1. 登录页渲染
r = client.get("/login")
check("GET /login -> 200", r.status_code == 200)
check("login 页含登录表单", "login-form" in r.text and "账号登录" in r.text)
check("login 引用 Tailwind 与自研 JS", "cdn.tailwindcss.com" in r.text and "/static/js/login.js" in r.text)

# 2. 未登录访问首页 → 302 跳转登录页
r = client.get("/", follow_redirects=False)
check("GET / 未登录 -> 302", r.status_code == 302, f"got {r.status_code}")
check("302 Location=/login", r.headers.get("location") == "/login")

# 3. 未登录访问详情页 → 302
r = client.get("/album/1", follow_redirects=False)
check("GET /album/1 未登录 -> 302", r.status_code == 302)

# 4. API 未登录 → 401
r = client.get("/api/albums")
check("GET /api/albums 未登录 -> 401", r.status_code == 401, r.text[:80])
r = client.get("/api/auth/me")
check("GET /api/auth/me 未登录 -> 401", r.status_code == 401)

# 5. 登录参数校验（后端二次校验）
r = client.post("/api/auth/login", json={"username": "a", "password": "123"})
check("POST /api/auth/login 参数不合法 -> 422", r.status_code == 422, r.text[:80])
try:
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    check("POST /api/auth/login 已进入业务层", r.status_code in (200, 401, 500), f"got {r.status_code}")
except Exception as e:  # 本机无 MySQL 时到达 ORM 层即视为链路正常
    check("POST /api/auth/login 已进入业务层(无DB环境)", "MySQL" in str(e) or "Can't connect" in str(e), type(e).__name__)

# 6. 静态资源
r = client.get("/static/css/app.css")
check("GET /static/css/app.css -> 200", r.status_code == 200)
r = client.get("/static/js/detail.js")
check("GET /static/js/detail.js -> 200", r.status_code == 200)
r = client.get("/static/img/default_cover.svg")
check("GET /static/img/default_cover.svg -> 200", r.status_code == 200)
r = client.get("/openapi.json")
check("GET /openapi.json -> 200", r.status_code == 200)
paths = r.json().get("paths", {})
expected = [
    "/api/auth/login", "/api/auth/logout", "/api/auth/me", "/api/auth/password",
    "/api/albums", "/api/albums/{album_id}", "/api/albums/{album_id}/template",
    "/api/modules/sort", "/api/modules", "/api/modules/{module_id}",
    "/api/albums/{album_id}/photos", "/api/albums/{album_id}/photos/sort",
    "/api/photos/{photo_id}/note", "/api/photos/{photo_id}/move", "/api/photos/{photo_id}",
    "/api/admin/users", "/api/admin/users/{user_id}/permissions",
    "/api/admin/settings",
]
missing = [p for p in expected if p not in paths]
check("OpenAPI 覆盖全部业务接口", not missing, f"missing={missing}")

print()
print("FAILED:" if failures else "ALL SMOKE TESTS PASSED", failures or "")
