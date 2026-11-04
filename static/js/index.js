/* ============================================================
   index.js — 首页（记录册列表）交互
   卡片渲染 / 模糊搜索（防抖）/ 新建记录册 / 删除 /
   管理员用户权限开关配置 / 照片与视频上传大小上限设置
   ============================================================ */
(function () {
    'use strict';

    var grid = document.getElementById('album-grid');
    var emptyState = document.getElementById('empty-state');
    var emptyText = document.getElementById('empty-text');
    var searchInput = document.getElementById('search-input');
    var isAdmin = document.getElementById('btn-admin') !== null;

    // 服务端渲染的初始数据
    var albums = [];
    try { albums = JSON.parse(document.getElementById('index-data').textContent) || []; } catch (e) { albums = []; }

    var esc = window.escapeHtml;

    /** 渲染记录册卡片网格 */
    function render() {
        if (!albums.length) {
            grid.innerHTML = '';
            emptyText.textContent = searchInput.value.trim()
                ? '没有找到匹配「' + searchInput.value.trim() + '」的记录册'
                : '还没有记录册，点击右上角「新建记录册」开始收藏吧';
            emptyState.classList.remove('hidden');
            return;
        }
        emptyState.classList.add('hidden');
        grid.innerHTML = albums.map(function (a) {
            var canEdit = a.can_edit;
            return '' +
                '<div class="album-card group bg-white rounded-2xl shadow-card border border-stone-100 overflow-hidden ' +
                '       hover:-translate-y-1 hover:shadow-soft transition cursor-pointer" data-id="' + a.id + '">' +
                '  <div class="relative aspect-[4/3] overflow-hidden bg-stone-100">' +
                '    <img src="' + esc(a.cover_image) + '" alt="' + esc(a.name) + '" loading="lazy"' +
                '         class="w-full h-full object-cover group-hover:scale-105 transition duration-300">' +
                '    <span class="absolute top-2.5 left-2.5 text-[11px] px-2 py-0.5 rounded-full' +
                '          bg-white/85 backdrop-blur text-stone-600">&#128247; ' + a.photo_count + ' 张</span>' +
                (canEdit
                    ? '<button data-action="delete" data-id="' + a.id + '" title="删除记录册"' +
                      '        class="absolute top-2 right-2 w-7 h-7 rounded-full bg-white/85 backdrop-blur text-stone-400' +
                      '               hover:text-red-500 opacity-0 group-hover:opacity-100 transition text-sm">&#128465;</button>'
                    : '') +
                '  </div>' +
                '  <div class="p-4">' +
                '    <h3 class="font-semibold text-stone-700 truncate">' + esc(a.name) + '</h3>' +
                '    <p class="mt-1 text-[13px] text-stone-400 leading-relaxed line-clamp-2 min-h-[2.3rem]">' +
                (a.description ? esc(a.description) : '<span class="italic">暂无简介</span>') + '</p>' +
                '    <div class="mt-3 pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-400">' +
                '      <span>' + a.create_time + '</span>' +
                '      <span class="truncate max-w-[45%] text-right">' + (a.is_owner ? '我创建的' : '&#128100; ' + esc(a.owner_nickname)) + '</span>' +
                '    </div>' +
                '  </div>' +
                '</div>';
        }).join('');
    }

    /** 卡片点击进入详情；删除按钮单独拦截 */
    grid.addEventListener('click', async function (e) {
        var delBtn = e.target.closest('[data-action="delete"]');
        if (delBtn) {
            e.stopPropagation();
            var id = Number(delBtn.getAttribute('data-id'));
            var album = albums.find(function (a) { return a.id === id; });
            if (!window.confirm('确定删除记录册「' + (album ? album.name : '') + '」？\n其中的模块与照片将一并删除。')) return;
            await window.api('/api/albums/' + id, { method: 'DELETE' });
            window.toast('记录册已删除', 'success');
            await reload(searchInput.value.trim());
            return;
        }
        var card = e.target.closest('.album-card');
        if (card) window.location.href = '/album/' + card.getAttribute('data-id');
    });

    /** 重新拉取列表 */
    async function reload(keyword) {
        var res = await window.api('/api/albums?q=' + encodeURIComponent(keyword || ''));
        albums = res.data;
        render();
    }

    // ---- 模糊搜索（300ms 防抖） ----
    var timer = null;
    searchInput.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(function () { reload(searchInput.value.trim()); }, 300);
    });

    // ---- 新建记录册 ----
    var createName = document.getElementById('create-name');
    var createDesc = document.getElementById('create-desc');
    document.getElementById('btn-create').addEventListener('click', function () {
        createName.value = '';
        createDesc.value = '';
        window.openModal('create-modal');
    });
    document.getElementById('create-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        var name = createName.value.trim();
        if (!name) { window.toast('请填写记录册名称', 'error'); createName.focus(); return; }
        var res = await window.api('/api/albums', { method: 'POST', body: { name: name, description: createDesc.value.trim() } });
        window.closeModal('create-modal');
        window.toast('记录册「' + name + '」创建成功', 'success');
        window.location.href = '/album/' + res.data.id;
    });

    // ---- 管理员：用户权限配置 ----
    if (isAdmin) {
        var userRows = document.getElementById('admin-user-rows');
        document.getElementById('btn-admin').addEventListener('click', loadUsers);

        async function loadUsers() {
            var res = await window.api('/api/admin/users');
            userRows.innerHTML = res.data.map(function (u) {                var disableSwitch = u.is_admin ? 'disabled title="管理员默认拥有全局权限"' : '';
                return '<tr>' +
                    '<td class="py-3">' +
                    '  <div class="font-medium text-stone-700">' + esc(u.display_name) + (u.is_admin ? ' <span class="text-[10px] align-middle px-1.5 py-0.5 rounded bg-brand-100 text-brand-700">管理员</span>' : '') + '</div>' +
                    '  <div class="text-xs text-stone-400">@' + esc(u.username) + ' · ' + u.album_count + ' 本记录册</div>' +
                    '</td>' +
                    '<td class="py-3 text-stone-500">' + esc(u.role_name) + '</td>' +
                    '<td class="py-3 text-center text-stone-500">' + u.album_count + '</td>' +
                    '<td class="py-3 text-center">' +
                    '  <label class="switch"><input type="checkbox" data-uid="' + u.id + '" data-field="can_view_others"' +
                    (u.can_view_others ? ' checked' : '') + ' ' + disableSwitch + '><span class="slider"></span></label>' +
                    '</td>' +
                    '<td class="py-3 text-center">' +
                    '  <label class="switch"><input type="checkbox" data-uid="' + u.id + '" data-field="can_edit_others"' +
                    (u.can_edit_others ? ' checked' : '') + ' ' + disableSwitch + '><span class="slider"></span></label>' +
                    '</td>' +
                    '</tr>';
            }).join('');
            await loadSettings();
            window.openModal('admin-modal');
        }

        // ---- 管理员：上传设置（单张照片 / 单个视频大小上限） ----
        var maxUploadInput = document.getElementById('setting-max-upload');
        var maxVideoInput = document.getElementById('setting-max-video');

        async function loadSettings() {
            var res = await window.api('/api/admin/settings');
            maxUploadInput.value = res.data.max_upload_size;
            maxVideoInput.value = res.data.max_video_size;
        }

        document.getElementById('btn-save-settings').addEventListener('click', async function () {
            var imageValue = Number(maxUploadInput.value);
            var videoValue = Number(maxVideoInput.value);
            if (!Number.isInteger(imageValue) || imageValue < 1 || imageValue > 100) {
                window.toast('照片上限需为 1-100 的整数（MB）', 'error');
                maxUploadInput.focus();
                return;
            }
            if (!Number.isInteger(videoValue) || videoValue < 1 || videoValue > 2048) {
                window.toast('视频上限需为 1-2048 的整数（MB）', 'error');
                maxVideoInput.focus();
                return;
            }
            await window.api('/api/admin/settings', {
                method: 'PUT', body: { max_upload_size: imageValue, max_video_size: videoValue }
            });
            window.toast('上传设置已保存：照片 ≤' + imageValue + 'MB，视频 ≤' + videoValue + 'MB', 'success');
        });

        // 开关切换即保存
        userRows.addEventListener('change', async function (e) {
            var input = e.target;
            if (input.tagName !== 'INPUT') return;
            var body = {};
            body[input.getAttribute('data-field')] = input.checked;
            await window.api('/api/admin/users/' + input.getAttribute('data-uid') + '/permissions', {
                method: 'PUT', body: body
            });
            window.toast('权限已更新', 'success');
        });

        // ---- 管理员：新增用户 ----
        var userForm = document.getElementById('user-form');
        var usernameInput = document.getElementById('user-username');
        var nicknameInput = document.getElementById('user-nickname');
        var passwordInput = document.getElementById('user-password');
        var roleSelect = document.getElementById('user-role');
        var canViewInput = document.getElementById('user-can-view');
        var canEditInput = document.getElementById('user-can-edit');
        var userSubmitBtn = document.getElementById('btn-user-submit');

        document.getElementById('btn-add-user').addEventListener('click', function () {
            userForm.reset();
            roleSelect.value = 'USER';
            syncRoleSwitches();
            userSubmitBtn.disabled = false;
            userSubmitBtn.textContent = '创建用户';
            window.openModal('user-modal');
        });

        // 管理员默认拥有全局权限，选中 ADMIN 时禁用权限开关
        function syncRoleSwitches() {
            var isAdminRole = roleSelect.value === 'ADMIN';
            canViewInput.disabled = isAdminRole;
            canEditInput.disabled = isAdminRole;
        }
        roleSelect.addEventListener('change', syncRoleSwitches);

        userForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            var username = usernameInput.value.trim();
            var password = passwordInput.value;
            if (!username) { window.toast('请填写账号', 'error'); usernameInput.focus(); return; }
            if (username.length < 2) { window.toast('账号至少 2 个字符', 'error'); usernameInput.focus(); return; }
            if (!password) { window.toast('请填写初始密码', 'error'); passwordInput.focus(); return; }
            if (password.length < 6) { window.toast('密码至少 6 位', 'error'); passwordInput.focus(); return; }

            userSubmitBtn.disabled = true;
            userSubmitBtn.textContent = '创建中…';
            try {
                await window.api('/api/admin/users', {
                    method: 'POST',
                    body: {
                        username: username,
                        password: password,
                        nickname: nicknameInput.value.trim() || null,
                        role_code: roleSelect.value,
                        can_view_others: canViewInput.checked,
                        can_edit_others: canEditInput.checked
                    }
                });
                window.closeModal('user-modal');
                window.toast('用户「' + username + '」创建成功', 'success');
                await loadUsers();
            } catch (err) {
                userSubmitBtn.disabled = false;
                userSubmitBtn.textContent = '创建用户';
            }
        });
    }

    render();
})();
