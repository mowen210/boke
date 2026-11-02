-- ============================================================
-- 照片记录册管理系统 · MySQL 完整建表脚本
-- 数据库：photo_album（utf8mb4）
-- 说明：应用首次启动时也会自动建表（幂等），
--       本脚本用于手工初始化 / 审阅表结构。
--       初始管理员账号由应用启动时自动创建（admin / admin123）。
-- ============================================================

CREATE DATABASE IF NOT EXISTS photo_album
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE photo_album;

-- ------------------------------------------------------------
-- 1. 角色权限表 sys_role
-- 内置：ADMIN（管理员，全局权限）/ USER（普通用户，数据隔离）
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_role (
    id          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    code        VARCHAR(32)  NOT NULL                COMMENT '角色编码：ADMIN/USER',
    name        VARCHAR(64)  NOT NULL                COMMENT '角色名称',
    remark      VARCHAR(255) DEFAULT NULL            COMMENT '角色说明',
    is_admin    TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '是否管理员角色：0否 1是',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted  TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '软删除标识：0正常 1已删除',
    PRIMARY KEY (id),
    UNIQUE KEY uk_role_code (code)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色权限表';

-- ------------------------------------------------------------
-- 2. 用户表 sys_user
-- 密码 bcrypt 哈希存储；can_view_others / can_edit_others
-- 为管理员可单独配置的用户级权限开关
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user (
    id              INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    username        VARCHAR(64)  NOT NULL                COMMENT '登录账号（唯一）',
    password_hash   VARCHAR(128) NOT NULL                COMMENT '密码哈希（bcrypt，禁止明文）',
    nickname        VARCHAR(64)  DEFAULT NULL            COMMENT '用户昵称',
    role_id         INT          NOT NULL                COMMENT '角色ID → sys_role.id',
    can_view_others TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '权限开关：允许查看他人记录册',
    can_edit_others TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '权限开关：允许编辑他人记录册',
    last_login_time DATETIME     DEFAULT NULL            COMMENT '最后登录时间',
    create_time     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted      TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '软删除标识：0正常 1已删除',
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_username (username),
    KEY ix_user_role (role_id),
    CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES sys_role (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表';

-- ------------------------------------------------------------
-- 3. 相册展示模板配置表 photo_template
-- 内置 5 套风格：经典网格 / 瀑布流 / 拍立得 / 时光轴 / 紧凑小图
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS photo_template (
    id          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    code        VARCHAR(32)  NOT NULL                COMMENT '模板编码（唯一）',
    name        VARCHAR(64)  NOT NULL                COMMENT '模板名称',
    css_class   VARCHAR(64)  NOT NULL                COMMENT '模板对应前端 CSS 类名',
    description VARCHAR(255) DEFAULT NULL            COMMENT '模板说明',
    sort_order  INT          NOT NULL DEFAULT 0      COMMENT '模板展示排序',
    is_default  TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '是否默认模板：0否 1是',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted  TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '软删除标识：0正常 1已删除',
    PRIMARY KEY (id),
    UNIQUE KEY uk_template_code (code)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '相册展示模板配置表';

-- ------------------------------------------------------------
-- 4. 照片记录册表 photo_album
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS photo_album (
    id          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    user_id     INT          NOT NULL                COMMENT '创建人用户ID → sys_user.id',
    name        VARCHAR(100) NOT NULL                COMMENT '记录册名称',
    description VARCHAR(500) DEFAULT NULL            COMMENT '记录册简介',
    cover_image VARCHAR(255) NOT NULL DEFAULT '/static/img/default_cover.svg' COMMENT '封面图相对访问路径',
    template_id INT          DEFAULT NULL            COMMENT '当前展示模板ID → photo_template.id',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted  TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '软删除标识：0正常 1已删除',
    PRIMARY KEY (id),
    KEY ix_album_user_deleted (user_id, is_deleted),
    KEY ix_album_name (name),
    KEY fk_album_template (template_id),
    CONSTRAINT fk_album_user FOREIGN KEY (user_id) REFERENCES sys_user (id),
    CONSTRAINT fk_album_template FOREIGN KEY (template_id) REFERENCES photo_template (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '照片记录册表';

-- ------------------------------------------------------------
-- 5. 记录册自定义模块表 album_module
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS album_module (
    id          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    album_id    INT          NOT NULL                COMMENT '所属记录册ID → photo_album.id',
    title       VARCHAR(100) NOT NULL                COMMENT '模块标题',
    sort_order  INT          NOT NULL DEFAULT 0      COMMENT '排序号（越小越靠前）',
    create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted  TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '软删除标识：0正常 1已删除',
    PRIMARY KEY (id),
    KEY ix_module_album_sort (album_id, sort_order),
    CONSTRAINT fk_module_album FOREIGN KEY (album_id) REFERENCES photo_album (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '记录册自定义模块表';

-- ------------------------------------------------------------
-- 6. 照片表 photo
-- file_path 只保存 /upload/... 相对访问路径，物理文件在项目 upload 目录
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS photo (
    id           INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    album_id     INT          NOT NULL                COMMENT '所属记录册ID → photo_album.id',
    module_id    INT          NOT NULL                COMMENT '所属模块ID → album_module.id',
    user_id      INT          NOT NULL                COMMENT '上传人用户ID → sys_user.id',
    file_path    VARCHAR(255) NOT NULL                COMMENT '图片相对访问路径（/upload/...）',
    original_name VARCHAR(255) DEFAULT NULL           COMMENT '原始文件名',
    file_size    INT          DEFAULT NULL            COMMENT '文件大小（字节）',
    file_type    VARCHAR(32)  DEFAULT NULL            COMMENT 'MIME 类型',
    note         VARCHAR(500) DEFAULT NULL            COMMENT '照片文字备注',
    sort_order   INT          NOT NULL DEFAULT 0      COMMENT '模块内排序号（越小越靠前）',
    create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted   TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '软删除标识：0正常 1已删除',
    PRIMARY KEY (id),
    KEY ix_photo_album_module_sort (album_id, module_id, sort_order),
    KEY ix_photo_user (user_id),
    CONSTRAINT fk_photo_album FOREIGN KEY (album_id) REFERENCES photo_album (id),
    CONSTRAINT fk_photo_module FOREIGN KEY (module_id) REFERENCES album_module (id),
    CONSTRAINT fk_photo_user FOREIGN KEY (user_id) REFERENCES sys_user (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '照片表';

-- ============================================================
-- 内置种子数据（角色 + 展示模板）
-- 初始管理员/演示用户由应用首次启动自动创建：
--   admin / admin123（管理员）    demo / 123456（普通用户）
-- ============================================================
INSERT INTO sys_role (code, name, is_admin, remark) VALUES
    ('ADMIN', '管理员', 1, '拥有全局权限，可管理用户与所有记录册'),
    ('USER',  '普通用户', 0, '默认仅可查看、编辑自己的记录册')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO photo_template (code, name, css_class, description, sort_order, is_default) VALUES
    ('grid',     '经典网格', 'tpl-grid',     '整齐统一的方形网格排版，简洁大方', 1, 1),
    ('masonry',  '瀑布流',   'tpl-masonry',  '按原始比例错落排布，长图短图自然混排', 2, 0),
    ('polaroid', '拍立得',   'tpl-polaroid', '白色相纸边框 + 轻微旋转，复古纪念册质感', 3, 0),
    ('timeline', '时光轴',   'tpl-timeline', '左侧时间轴线的纵向回忆列表', 4, 0),
    ('compact',  '紧凑小图', 'tpl-compact',  '高密度小图排版，一屏纵览全部照片', 5, 0)
ON DUPLICATE KEY UPDATE name = VALUES(name);
