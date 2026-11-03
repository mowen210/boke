# 拾光记 · 照片记录册管理系统

纯 Python 全栈实现的相册纪念册管理系统：**FastAPI + Jinja2 + SQLAlchemy + MySQL**，
前端为原生 HTML + TailwindCSS + 原生 JS（无独立前端工程），PC / 手机端响应式适配。

## 功能一览

- **登录页**：账号密码登录（前后端双重校验），JWT（HttpOnly Cookie）维持登录态；未登录访问首页 / 详情页自动跳转登录页；区分普通用户与管理员。
- **首页**：卡片布局展示可访问的记录册（封面、名称、简介、创建时间、照片数）；新建记录册；名称模糊搜索；普通用户数据隔离，仅见本人记录册。
- **记录册详情页**：
  - 照片单张 / 批量上传（拖拽 + 点击选择，上传前缩略预览）
  - 点击图片大图灯箱预览（支持键盘 ← → / Esc）
  - 自定义模块：新增、改名、删除、拖拽排序（移动端提供箭头微调）
  - 照片归类模块、独立文字备注、移动到其他模块、单独删除、模块内拖拽排序
  - 编辑记录册名称 / 简介 / 更换封面
  - 一键切换 5 套整册展示风格：经典网格 / 瀑布流 / 拍立得 / 时光轴 / 紧凑小图
- **权限**：管理员全局权限 + 用户级「查看他人 / 编辑他人」开关配置；所有业务查询自动携带权限条件，杜绝越权。

## 技术栈

| 层 | 技术 |
| ---- | ---- |
| Web 框架 | FastAPI |
| 模板引擎 | Jinja2（templates/） |
| ORM | SQLAlchemy 2.x + PyMySQL |
| 数据库 | MySQL 8.0（utf8mb4） |
| 鉴权 | python-jose（JWT）+ passlib/bcrypt（密码哈希） |
| 前端 | 原生 HTML + TailwindCSS（CDN）+ 原生 JS（static/） |

## 目录结构

```
boke/
├── main.py                  # 应用入口（启动、静态目录挂载、路由注册）
├── requirements.txt         # 依赖清单
├── .env.example             # 环境变量示例（复制为 .env 使用）
├── app/
│   ├── config.py            # 全局配置（数据库/JWT/上传）
│   ├── database.py          # 引擎与会话管理
│   ├── dependencies.py      # 全局登录鉴权依赖（API 401 / 页面 302）
│   ├── exceptions.py        # 自定义异常（页面未登录跳转）
│   ├── init_db.py           # 启动建表 + 内置数据种子
│   ├── models/              # SQLAlchemy 模型（6 张表）
│   ├── schemas/             # Pydantic 请求体校验
│   ├── services/            # 业务层（含权限服务）
│   ├── routers/             # 路由层（页面 + 认证/记录册/模块/照片/管理员 API）
│   └── utils/               # 安全工具（JWT/bcrypt）、文件校验保存
├── templates/               # Jinja2 模板：base / login / index / detail
├── static/                  # 内置静态资源：css / js / 默认封面
├── upload/                  # 上传图片保存目录（自动创建，数据库只存相对路径）
└── docs/
    ├── database.sql         # MySQL 完整建表脚本 + 种子数据
    ├── database.md          # 数据库设计文档（ER / 字段 / 索引）
    └── api.md               # 接口文档（入参 / 返回 JSON 示例）
```

## 部署运行

### 1. 环境要求

- Python 3.10+
- MySQL 8.0（或 5.7+）

### 2. 初始化 MySQL

方式一（推荐，自动建表）：

```sql
CREATE DATABASE photo_album DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

方式二（手工执行完整脚本，含表结构注释与种子数据）：

```bash
mysql -u root -p < docs/database.sql
```

### 3. 配置数据库连接

复制 `.env.example` 为 `.env`，按实际环境修改：

```ini
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=photo_album
SECRET_KEY=生产环境请更换为随机长字符串
```

### 4. 安装依赖

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate
pip install -r requirements.txt
```

### 5. 启动

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
# 开发热重载：uvicorn main:app --reload --port 8000
```

浏览器访问：<http://127.0.0.1:8000/login> （接口文档：<http://127.0.0.1:8000/docs>）

### 6. 初始账号（首次启动自动创建）

| 账号 | 密码 | 角色 | 权限 |
| ---- | ---- | ---- | ---- |
| admin | admin123 | 管理员 | 全局权限：可查看/编辑所有记录册、配置用户权限开关 |
| demo | 123456 | 普通用户 | 仅自己的记录册（已内置一本示例记录册） |

> 账号密码可通过 `.env` 的 `INIT_ADMIN_USERNAME / INIT_ADMIN_PASSWORD` 在首次启动前自定义。

## 上传文件路径配置

- 上传图片默认保存在**项目内 `upload/` 目录**（自动创建），按 `upload/YYYYMM/uuid.ext` 组织；
- 数据库仅保存相对访问路径（如 `/upload/202611/xx.jpg`），由 FastAPI 静态挂载 `/upload` 直接对外提供；
- 如需更换存储位置，修改 `.env` 无法直接调整（路径固定为项目内 `upload/`），
  可修改 `app/config.py` 中 `UPLOAD_DIR`，并将新目录以同样方式挂载（见 `main.py`）；
- 上传校验：仅 jpg / jpeg / png / gif / webp，单文件大小上限默认 5MB（前后端双重校验）；
  上限可由管理员在首页「用户权限」弹窗的「上传设置」中调整（1-100MB，存于 `sys_setting` 表，
  初始值取 `.env` 的 `MAX_UPLOAD_SIZE_MB`）；
- 删除照片为软删除，物理文件保留以便恢复；可按 `photo.is_deleted=1` 的记录定期清理磁盘。

## 权限模型速查

| 主体 | 查看他人记录册 | 编辑他人记录册 | 说明 |
| ---- | -------------- | -------------- | ---- |
| 管理员（ADMIN 角色） | ✅ | ✅ | 全局权限 |
| 普通用户（默认） | ❌ | ❌ | 仅本人数据（数据隔离） |
| 普通用户 + 管理员开启开关 | 按开关 | 按开关 | 首页「用户权限」弹窗实时配置 |

权限判断集中在 `app/services/permission_service.py`，所有记录册 / 模块 / 照片操作均先通过
`assert_can_view / assert_can_edit` 越权校验。

## 常见问题

1. **启动报数据库连接错误**：检查 MySQL 是否启动、`.env` 账号密码、`photo_album` 库是否已创建；首次启动会自动建表。
2. **登录后仍跳登录页**：确认浏览器未禁用 Cookie（JWT 存于 HttpOnly Cookie）。
3. **Tailwind 样式未生效**：页面依赖 TailwindCSS CDN，服务器需可访问外网；离线部署可将 CDN 脚本下载至 `static/` 并修改 `templates/base.html` 引用。
4. **修改端口**：启动命令 `--port` 参数；生产建议置于 Nginx 反向代理之后。

## 开发自测脚本（可选）

项目附带两个不依赖 MySQL 的自测脚本（需 `pip install httpx`）：

```bash
python smoke_test.py     # 冒烟测试：页面渲染 / 鉴权拦截 / 静态资源 / 接口注册
python template_test.py  # 模板渲染测试：login / index / detail（含 XSS 转义检查）
```
