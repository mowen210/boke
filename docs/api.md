# 接口文档（照片记录册管理系统）

## 通用约定

- **Base URL**：`http://<host>:8000`
- **鉴权方式**：登录成功后服务端将 JWT 写入 HttpOnly Cookie（`access_token`）；
  所有业务接口需携带该 Cookie（同源 fetch 自动携带），或使用请求头 `Authorization: Bearer <token>`。
- **未登录**：业务接口返回 `401`；页面路由（`/`、`/album/{id}`）返回 `302` 跳转 `/login`。
- **无权限（越权）**：返回 `403`，例如普通用户访问他人记录册。
- **响应结构**：
  ```json
  { "message": "提示文案", "data": { } }
  ```
  失败时返回 FastAPI 标准结构：`{ "detail": "错误原因" }`。
- 交互式文档：启动后访问 `http://<host>:8000/docs`（Swagger UI）。

## 页面路由

| 路径 | 说明 |
| ---- | ---- |
| GET `/login` | 登录页（已登录访问会 302 到 `/`） |
| GET `/` | 首页（记录册卡片列表，支持 `?q=名称关键字` 模糊搜索） |
| GET `/album/{album_id}` | 记录册详情页（未登录 302 登录页，无权限 403） |

---

## 1. 认证

### 1.1 登录

`POST /api/auth/login`

请求体（JSON）：

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| username | string | 是 | 账号，2-64 字符 |
| password | string | 是 | 密码，6-64 字符（后端二次校验） |

请求示例：

```json
{ "username": "admin", "password": "admin123" }
```

成功（200，同时 Set-Cookie: access_token=…）：

```json
{
  "message": "登录成功",
  "data": {
    "id": 1,
    "username": "admin",
    "nickname": "系统管理员",
    "is_admin": true
  }
}
```

失败（401）：`{ "detail": "账号或密码错误" }`

### 1.2 退出登录

`POST /api/auth/logout`

成功（200，清除 Cookie）：`{ "message": "已退出登录" }`

### 1.3 当前用户信息

`GET /api/auth/me`

```json
{
  "id": 2,
  "username": "demo",
  "nickname": "演示用户",
  "is_admin": false,
  "can_view_others": false,
  "can_edit_others": false
}
```

### 1.4 修改自身密码

`PUT /api/auth/password`（需登录）

请求体（JSON）：

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| old_password | string | 是 | 原密码，6-64 字符 |
| new_password | string | 是 | 新密码，6-64 字符 |
| confirm_password | string | 是 | 确认新密码，须与 new_password 一致 |

请求示例：

```json
{ "old_password": "123456", "new_password": "abc123456", "confirm_password": "abc123456" }
```

成功（200）：`{ "message": "密码修改成功", "data": { "username": "demo" } }`

失败：
- 400：`{ "detail": "原密码错误" }` / `{ "detail": "两次输入的新密码不一致" }` / `{ "detail": "新密码不能与原密码相同" }`
- 401：未登录

---

## 2. 记录册

### 2.1 记录册列表（权限过滤 + 模糊搜索）

`GET /api/albums?q=旅行`

- 管理员 / 开启 `can_view_others` 的用户：返回全部记录册；
- 普通用户：仅返回本人记录册（数据隔离）。

```json
{
  "message": "ok",
  "data": [
    {
      "id": 1,
      "name": "2026 春日旅行",
      "description": "和朋友的江南三日行",
      "cover_image": "/upload/202611/a1b2c3.jpg",
      "template_id": 1,
      "create_time": "2026-11-01 10:00",
      "owner_id": 2,
      "owner_nickname": "演示用户",
      "is_owner": true,
      "can_edit": true,
      "photo_count": 12
    }
  ]
}
```

### 2.2 新建记录册

`POST /api/albums`

```json
{ "name": "宝宝成长记", "description": "记录每一天的变化" }
```

成功（200）：

```json
{
  "message": "创建成功",
  "data": {
    "id": 3, "name": "宝宝成长记", "description": "记录每一天的变化",
    "cover_image": "/static/img/default_cover.svg", "template_id": 1,
    "create_time": "2026-11-01 11:20", "owner_id": 2, "owner_nickname": "演示用户",
    "is_owner": true, "can_edit": true, "photo_count": 0
  }
}
```

> 新建时自动创建「默认模块」并绑定默认展示模板。

### 2.3 记录册详情数据

`GET /api/albums/{album_id}`

```json
{
  "message": "ok",
  "data": {
    "album": { "id": 1, "name": "2026 春日旅行", "photo_count": 12, "can_edit": true, "...": "..." },
    "modules": [
      { "id": 5, "album_id": 1, "title": "生活日常", "sort_order": 1, "photo_count": 8 },
      { "id": 6, "album_id": 1, "title": "旅行风景", "sort_order": 2, "photo_count": 4 }
    ],
    "photos": [
      {
        "id": 21, "album_id": 1, "module_id": 5,
        "file_path": "/upload/202611/9f8e7d.jpg",
        "original_name": "IMG_0102.jpg", "file_size": 1048576,
        "file_type": "image/jpeg", "note": "巷口的猫", "sort_order": 1,
        "create_time": "2026-11-01 11:30"
      }
    ]
  }
}
```

### 2.4 编辑记录册基础信息（含更换封面）

`PUT /api/albums/{album_id}`（multipart/form-data）

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| name | string | 否 | 新名称（1-100 字符） |
| description | string | 否 | 新简介（≤500 字符） |
| cover | file | 否 | 新封面图片（jpg/png/gif/webp，≤5MB） |

成功：`{ "message": "保存成功", "data": { "...album": "..." } }`
校验失败（400）：`{ "detail": "不支持的文件格式：a.bmp（仅允许 jpg/png/gif/webp）" }`

### 2.5 删除记录册（级联软删除模块与照片）

`DELETE /api/albums/{album_id}`

成功：`{ "message": "删除成功" }`

### 2.6 切换展示模板

`PUT /api/albums/{album_id}/template`

```json
{ "template_id": 3 }
```

成功：`{ "message": "模板已切换", "data": { "...album": "..." } }`

---

## 3. 模块

### 3.1 新增模块

`POST /api/modules?album_id=1`

```json
{ "title": "春日野餐" }
```

成功：

```json
{
  "message": "模块已创建",
  "data": { "id": 7, "album_id": 1, "title": "春日野餐", "sort_order": 3, "photo_count": 0 }
}
```

### 3.2 修改模块标题

`PUT /api/modules/{module_id}`

```json
{ "title": "春日野餐（修改）" }
```

成功：`{ "message": "模块已更新", "data": { "id": 7, "album_id": 1, "title": "春日野餐（修改）", "sort_order": 3 } }`

### 3.3 删除模块

`DELETE /api/modules/{module_id}`

> 模块内仍有照片时，照片自动移入该记录册第一个剩余模块（无剩余模块则自动创建「默认模块」）。

成功：`{ "message": "模块已删除" }`

### 3.4 模块拖拽排序

`PUT /api/modules/sort?album_id=1`

```json
{ "module_ids": [6, 5, 7] }
```

成功：`{ "message": "排序已保存", "data": [ { "id": 6, "...": "..." }, { "id": 5, "...": "..." }, { "id": 7, "...": "..." } ] }`

---

## 4. 照片

### 4.1 批量上传照片

`POST /api/albums/{album_id}/photos`（multipart/form-data）

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| module_id | int | 否 | 目标模块（缺省为第一个模块） |
| files | file[] | 是 | 多文件；仅 jpg/png/gif/webp，单文件 ≤5MB |

成功：

```json
{
  "message": "成功上传 2 张照片",
  "data": [
    { "id": 22, "album_id": 1, "module_id": 5, "file_path": "/upload/202611/aa11.jpg",
      "original_name": "cat.jpg", "file_size": 204800, "file_type": "image/jpeg",
      "note": null, "sort_order": 2, "create_time": "2026-11-01 11:40" },
    { "id": 23, "...": "..." }
  ]
}
```

失败（400）：`{ "detail": "文件超过 5MB 上限：big.png" }`

### 4.2 模块内照片拖拽排序

`PUT /api/albums/{album_id}/photos/sort`

```json
{ "module_id": 5, "photo_ids": [23, 22, 21] }
```

成功：`{ "message": "排序已保存", "data": [ "...该记录册全部照片..." ] }`

### 4.3 更新照片备注

`PUT /api/photos/{photo_id}/note`

```json
{ "note": "巷口的猫，晒着太阳打盹" }
```

成功：`{ "message": "备注已保存", "data": { "id": 21, "note": "巷口的猫，晒着太阳打盹", "...": "..." } }`

### 4.4 照片移动到其他模块

`PUT /api/photos/{photo_id}/move`

```json
{ "module_id": 6 }
```

成功：`{ "message": "照片已移动", "data": { "id": 21, "module_id": 6, "...": "..." } }`
跨记录册模块（400）：`{ "detail": "目标模块不存在" }`

### 4.5 删除照片

`DELETE /api/photos/{photo_id}`

成功：`{ "message": "照片已删除" }`（软删除）

---

## 5. 管理员

### 5.1 用户管理列表

`GET /api/admin/users`（仅管理员）

```json
{
  "message": "ok",
  "data": [
    {
      "id": 2, "username": "demo", "nickname": "演示用户", "display_name": "演示用户",
      "role_code": "USER", "role_name": "普通用户", "is_admin": false,
      "can_view_others": false, "can_edit_others": false,
      "album_count": 1, "last_login_time": "2026-11-01 10:00"
    }
  ]
}
```

非管理员（403）：`{ "detail": "仅管理员可执行该操作" }`

### 5.2 配置用户权限开关

`PUT /api/admin/users/{user_id}/permissions`（仅管理员）

```json
{ "can_view_others": true, "can_edit_others": false }
```

成功：

```json
{
  "message": "权限已更新",
  "data": { "id": 2, "username": "demo", "can_view_others": true, "can_edit_others": false }
}
```

### 5.3 新增用户

`POST /api/admin/users`（仅管理员）

请求体（JSON）：

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| username | string | 是 | 登录账号，2-64 字符，全库唯一 |
| password | string | 是 | 初始密码，6-64 字符 |
| nickname | string | 否 | 昵称，≤64 字符，缺省同账号 |
| role_code | string | 否 | 角色编码：ADMIN / USER，缺省 USER |
| can_view_others | boolean | 否 | 允许查看他人记录册，缺省 false |
| can_edit_others | boolean | 否 | 允许编辑他人记录册，缺省 false |

请求示例：

```json
{
  "username": "xiaoming", "password": "abc123456", "nickname": "小明",
  "role_code": "USER", "can_view_others": false, "can_edit_others": false
}
```

成功（200）：

```json
{
  "message": "用户创建成功",
  "data": {
    "id": 3, "username": "xiaoming", "nickname": "小明", "display_name": "小明",
    "role_code": "USER", "role_name": "普通用户", "is_admin": false,
    "can_view_others": false, "can_edit_others": false
  }
}
```

失败：
- 400：`{ "detail": "账号已存在，请更换后重试" }` / `{ "detail": "角色不存在：ADMIN / USER" }`
- 403：`{ "detail": "仅管理员可执行该操作" }`

---

## 6. 错误码速查

| 状态码 | 场景 |
| ------ | ---- |
| 400 | 参数/上传校验失败（格式、大小、无效排序等） |
| 401 | 未登录或登录令牌过期 |
| 403 | 已登录但无权限（越权访问他人数据、非管理员调用管理接口） |
| 404 | 资源不存在或已删除 |
| 422 | 请求体不符合 Pydantic 校验规则 |
