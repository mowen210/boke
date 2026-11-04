/* ============================================================
   detail.js — 记录册详情页交互
   模块管理（新增/改名/删除/拖拽排序）、照片/视频批量上传（拖拽+预览）、
   大图灯箱（图片查看 / 视频播放）、备注、移动模块、删除、模块内拖拽排序、
   记录册信息编辑、展示风格模板一键切换、
   管理员批量删除模块内照片（勾选模式）
   ============================================================ */
(function () {
    'use strict';

    /* ---------------- 页面初始数据（服务端内嵌 JSON） ---------------- */
    var DATA = JSON.parse(document.getElementById('page-data').textContent);
    var state = {
        album: DATA.album,
        modules: DATA.modules || [],
        photos: DATA.photos || [],
        templates: DATA.templates || [],
        currentUser: DATA.current_user || {}
    };
    var albumId = state.album.id;
    var canEdit = !!state.album.can_edit;
    var isAdmin = !!state.currentUser.is_admin;
    var maxUploadMb = DATA.max_upload_size_mb || 5;
    var maxVideoUploadMb = DATA.max_video_size_mb || 200;
    var IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    var VIDEO_EXTS = ['mp4', 'webm', 'mov', 'm4v', 'ogg'];
    var esc = window.escapeHtml;
    var photoArea = document.getElementById('photo-area');

    /* 批量选择模式（仅管理员）：moduleId 当前操作的模块，ids 已选照片ID */
    var batchMode = { moduleId: null, ids: [] };

    /* ================= 通用小工具 ================= */

    function moduleById(id) {
        return state.modules.find(function (m) { return m.id === Number(id); });
    }

    function photosOf(moduleId) {
        return state.photos.filter(function (p) { return p.module_id === Number(moduleId); });
    }

    function refreshModuleCounts() {
        state.modules.forEach(function (m) {
            m.photo_count = photosOf(m.id).length;
        });
    }

    /** 全量刷新：重新拉取详情数据并重渲染 */
    async function refresh() {
        var res = await window.api('/api/albums/' + albumId);
        state.album = res.data.album;
        state.modules = res.data.modules;
        state.photos = res.data.photos;
        if (res.data.max_upload_size_mb) maxUploadMb = res.data.max_upload_size_mb;
        if (res.data.max_video_size_mb) maxVideoUploadMb = res.data.max_video_size_mb;
        renderUploadHints();
        renderAll();
    }

    /** 上传提示文案（大小上限由管理员配置，可能变化） */
    function renderUploadHints() {
        var uploadHint = document.getElementById('upload-size-hint');
        var coverHint = document.getElementById('cover-size-hint');
        var videoHint = document.getElementById('upload-video-size-hint');
        if (uploadHint) uploadHint.textContent = maxUploadMb;
        if (coverHint) coverHint.textContent = maxUploadMb;
        if (videoHint) videoHint.textContent = maxVideoUploadMb;
    }

    /* ================= 渲染 ================= */

    function renderAll() {
        renderHeader();
        renderTemplateSelect();
        renderModules();
        renderSections();
        applyTemplateCss();
        // 无可播放图片时隐藏「视频播放」入口（幻灯片仅播放图片，视频请在灯箱中观看）
        var playable = state.photos.filter(function (p) { return !p.is_video; });
        document.getElementById('btn-play').classList.toggle('hidden', !playable.length);
    }

    function renderHeader() {
        document.title = state.album.name + ' · 拾光记';
        document.getElementById('album-title').textContent = state.album.name;
        document.getElementById('album-desc').textContent = state.album.description || '这本记录册还没有简介';
        document.getElementById('album-meta').innerHTML =
            '&#128100; ' + esc(state.album.owner_nickname) +
            ' &nbsp;·&nbsp; &#128197; 创建于 ' + state.album.create_time +
            ' &nbsp;·&nbsp; &#128247; ' + state.album.photo_count + ' 张照片';
        var badge = document.getElementById('album-owner-badge');
        if (!state.album.is_owner) {
            badge.textContent = state.album.owner_nickname + ' 的记录册';
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
        document.getElementById('album-actions').classList.toggle('hidden', !canEdit);
    }

    function renderTemplateSelect() {
        var select = document.getElementById('template-select');
        select.innerHTML = state.templates.map(function (t) {
            return '<option value="' + t.id + '"' + (t.id === state.album.template_id ? ' selected' : '') + '>' +
                esc(t.name) + '</option>';
        }).join('');
    }

    function applyTemplateCss() {
        var tpl = state.templates.find(function (t) { return t.id === state.album.template_id; });
        var cls = tpl ? tpl.css_class : 'tpl-grid';
        photoArea.className = cls;
    }

    /** 模块栏：拖拽排序 + 箭头微调（移动端） + 新增 */
    function renderModules() {
        var bar = document.getElementById('module-bar');
        var html = state.modules.map(function (m) {
            return '' +
                '<div class="module-chip" draggable="true" data-module-id="' + m.id + '" title="拖拽调整模块顺序">' +
                '  <span class="chip-btn cursor-grab" title="拖拽排序">&#8759;</span>' +
                '  <span class="font-medium">' + esc(m.title) + '</span>' +
                '  <span class="chip-count">' + m.photo_count + '</span>' +
                (canEdit
                    ? '<span class="chip-btn" data-op="left" title="前移">&#8249;</span>' +
                      '<span class="chip-btn" data-op="right" title="后移">&#8250;</span>' +
                      '<span class="chip-btn" data-op="rename" title="重命名">&#9998;</span>' +
                      '<span class="chip-btn" data-op="delete" title="删除模块">&#10005;</span>'
                    : '') +
                '</div>';
        }).join('');
        if (canEdit) {
            html += '<button id="btn-add-module" class="flex-none px-3.5 py-1.5 rounded-full border border-dashed border-brand-300' +
                    ' text-brand-500 text-sm hover:bg-brand-50 transition">+ 新增模块</button>';
        }
        bar.innerHTML = html;
        bindModuleDrag(bar);
        if (canEdit) {
            document.getElementById('btn-add-module').addEventListener('click', openModuleCreate);
        }
    }

    /** 照片区：按模块分节 */
    function renderSections() {
        refreshModuleCounts();
        var emptyRoot = document.getElementById('photos-empty');
        if (!state.modules.length) {
            photoArea.innerHTML = '';
            emptyRoot.classList.remove('hidden');
            return;
        }
        emptyRoot.classList.toggle('hidden', state.photos.length > 0);
        photoArea.innerHTML = state.modules.map(function (m) {
            var photos = photosOf(m.id);
            var cards = photos.map(function (p) { return photoCardHtml(p); }).join('');
            return '' +
                '<section class="module-section" id="section-' + m.id + '" data-module-id="' + m.id + '">' +
                '  <div class="section-head">' +
                '    <span class="section-title">' + esc(m.title) + '</span>' +
                '    <span class="section-count">' +
                (batchMode.moduleId === m.id
                    ? '已选 <b id="batch-count">' + batchMode.ids.length + '</b> / ' + photos.length + ' 张'
                    : photos.length + ' 张') + '</span>' +
                (canEdit ? '<span class="ml-auto text-[11px] text-stone-300 hidden md:inline">拖拽照片可排序</span>' : '') +
                (batchMode.moduleId === m.id
                    ? '<button class="batch-btn" data-op="select-all" data-module-id="' + m.id + '">全选</button>' +
                      '<button class="batch-btn danger" data-op="batch-delete" data-module-id="' + m.id + '">删除所选</button>' +
                      '<button class="batch-btn" data-op="batch-cancel">取消</button>'
                    : (isAdmin
                        ? '<button class="batch-btn' + (canEdit ? ' ml-2' : ' ml-auto') + '" data-op="batch-enter" data-module-id="' + m.id + '"' +
                          ' title="批量删除本模块照片">批量删除</button>'
                        : '')) +
                '  </div>' +
                '  <div class="photo-grid" data-module-id="' + m.id + '">' +
                (cards || '<div class="module-empty col-span-full">这个模块还没有照片</div>') +
                '  </div>' +
                '</section>';
        }).join('');
        bindPhotoDrag();
    }

    /** 卡片媒体：图片用 <img>，视频用 <video>（首帧预览 + 角标） */
    function mediaHtml(p) {
        if (p.is_video) {
            return '' +
                '<video class="photo-img" src="' + esc(p.file_path) + '" preload="metadata" muted playsinline></video>' +
                '<span class="video-badge">&#9654; 视频</span>';
        }
        return '<img class="photo-img" src="' + esc(p.file_path) + '" alt="' + esc(p.original_name || '') + '" loading="lazy">';
    }

    /** 单张照片卡片 */
    function photoCardHtml(p) {
        var note = p.note ? esc(p.note) : '<span class="italic text-stone-300">未添加备注</span>';
        // 批量选择模式：卡片带勾选标记，点击整卡切换选中，禁用拖拽与单张操作
        if (batchMode.moduleId === p.module_id) {
            var selected = batchMode.ids.indexOf(p.id) > -1;
            return '' +
                '<figure class="photo-card batch-mode' + (selected ? ' selected' : '') + '" data-photo-id="' + p.id + '">' +
                '  <span class="select-check">&#10003;</span>' +
                '  ' + mediaHtml(p) +
                '  <figcaption class="photo-note">' + note + '</figcaption>' +
                '</figure>';
        }
        return '' +
            '<figure class="photo-card" draggable="true" data-photo-id="' + p.id + '" title="拖拽排序，点击查看大图 / 播放视频">' +
            '  ' + mediaHtml(p) +
            '  <figcaption class="photo-note">' + note + '</figcaption>' +
            '  <div class="photo-actions">' +
            (canEdit
                ? '<button class="pa" data-op="note" title="编辑备注">&#9998; 备注</button>' +
                  '<button class="pa" data-op="move" title="移动到其他模块">&#8690; 移动</button>' +
                  '<button class="pa" data-op="left" title="前移">&#8249;</button>' +
                  '<button class="pa" data-op="right" title="后移">&#8250;</button>' +
                  '<button class="pa danger" data-op="delete" title="删除照片">&#10005;</button>'
                : '<button class="pa" data-op="view" title="查看大图">&#128269; 查看</button>') +
            '  </div>' +
            '</figure>';
    }

    /* ================= 照片操作（事件委托） ================= */

    /** 退出批量选择模式并恢复渲染 */
    function exitBatchMode() {
        batchMode.moduleId = null;
        batchMode.ids = [];
        renderSections();
    }

    /** 切换单张照片选中态（仅更新 DOM，不整体重绘） */
    function toggleBatchSelected(photoId) {
        var idx = batchMode.ids.indexOf(photoId);
        if (idx > -1) batchMode.ids.splice(idx, 1);
        else batchMode.ids.push(photoId);
        var card = photoArea.querySelector('.photo-card[data-photo-id="' + photoId + '"]');
        if (card) {
            card.classList.toggle('selected', idx === -1);
            var count = document.getElementById('batch-count');
            if (count) count.textContent = batchMode.ids.length;
        }
    }

    photoArea.addEventListener('click', async function (e) {
        // ---- 管理员批量删除按钮（进入/全选/删除所选/取消） ----
        var batchBtn = e.target.closest('.batch-btn');
        if (batchBtn) {
            var batchOp = batchBtn.getAttribute('data-op');
            var batchModuleId = Number(batchBtn.getAttribute('data-module-id'));
            if (batchOp === 'batch-enter') {
                batchMode.moduleId = batchModuleId;
                batchMode.ids = [];
                renderSections();
                return;
            }
            if (batchOp === 'batch-cancel') {
                exitBatchMode();
                return;
            }
            if (batchOp === 'select-all') {
                var allIds = photosOf(batchModuleId).map(function (p) { return p.id; });
                batchMode.ids = batchMode.ids.length === allIds.length ? [] : allIds;
                renderSections();
                return;
            }
            if (batchOp === 'batch-delete') {
                if (!batchMode.ids.length) { window.toast('请先勾选要删除的照片', 'error'); return; }
                if (!window.confirm('确定删除已选的 ' + batchMode.ids.length + ' 张照片吗？')) return;
                var res = await window.api('/api/albums/' + albumId + '/photos', {
                    method: 'DELETE', body: { photo_ids: batchMode.ids.slice() }
                });
                window.toast(res.message || '照片已删除', 'success');
                batchMode.moduleId = null;
                batchMode.ids = [];
                await refresh();
                return;
            }
            return;
        }

        // ---- 批量选择模式：点击卡片切换选中，屏蔽灯箱/单张操作/排序 ----
        if (batchMode.moduleId !== null) {
            var selCard = e.target.closest('.photo-card');
            if (selCard) toggleBatchSelected(Number(selCard.getAttribute('data-photo-id')));
            return;
        }

        var btn = e.target.closest('.pa');
        if (!btn) {
            var img = e.target.closest('.photo-img');
            if (img) openLightbox(Number(img.closest('.photo-card').getAttribute('data-photo-id')));
            return;
        }
        var op = btn.getAttribute('data-op');
        var card = btn.closest('.photo-card');
        var photoId = Number(card.getAttribute('data-photo-id'));
        var photo = state.photos.find(function (p) { return p.id === photoId; });
        if (!photo) return;

        if (op === 'note') {
            openNoteModal(photo);
        } else if (op === 'move') {
            openMoveModal(photo);
        } else if (op === 'delete') {
            if (!window.confirm('确定删除这张照片吗？')) return;
            await window.api('/api/photos/' + photoId, { method: 'DELETE' });
            window.toast('照片已删除', 'success');
            await refresh();
        } else if (op === 'left' || op === 'right') {
            shiftPhoto(photo, op === 'left' ? -1 : 1);
        }
    });

    /** 照片左右微调（移动端排序兜底） */
    async function shiftPhoto(photo, delta) {
        var list = photosOf(photo.module_id);
        var index = list.findIndex(function (p) { return p.id === photo.id; });
        var target = index + delta;
        if (target < 0 || target >= list.length) return;
        var arr = list.slice();
        arr.splice(target, 0, arr.splice(index, 1)[0]);
        var res = await window.api('/api/albums/' + albumId + '/photos/sort', {
            method: 'PUT',
            body: { module_id: photo.module_id, photo_ids: arr.map(function (p) { return p.id; }) }
        });
        state.photos = res.data;
        renderSections();
    }

    /* ================= 照片拖拽排序（同模块内） ================= */

    function bindPhotoDrag() {
        if (!canEdit) return;
        var dragging = null;
        photoArea.querySelectorAll('.photo-card').forEach(function (card) {
            card.addEventListener('dragstart', function () {
                dragging = card;
                card.classList.add('dragging');
            });
            card.addEventListener('dragend', function () {
                card.classList.remove('dragging');
                photoArea.querySelectorAll('.drop-before').forEach(function (el) { el.classList.remove('drop-before'); });
                dragging = null;
            });
            card.addEventListener('dragover', function (e) {
                e.preventDefault();
                if (!dragging || dragging === card) return;
                var grid1 = dragging.closest('.photo-grid');
                var grid2 = card.closest('.photo-grid');
                if (grid1 !== grid2) return; // 仅支持同模块内排序，跨模块请用「移动」
                card.classList.add('drop-before');
            });
            card.addEventListener('dragleave', function () { card.classList.remove('drop-before'); });
            card.addEventListener('drop', async function (e) {
                e.preventDefault();
                if (!dragging || dragging === card) return;
                var grid1 = dragging.closest('.photo-grid');
                var grid2 = card.closest('.photo-grid');
                if (grid1 !== grid2) return;
                grid1.insertBefore(dragging, card); // 视觉先行
                var ids = Array.prototype.map.call(grid1.querySelectorAll('.photo-card'), function (el) {
                    return Number(el.getAttribute('data-photo-id'));
                });
                var res = await window.api('/api/albums/' + albumId + '/photos/sort', {
                    method: 'PUT',
                    body: { module_id: Number(grid1.getAttribute('data-module-id')), photo_ids: ids }
                });
                state.photos = res.data;
                renderSections();
            });
        });
    }

    /* ================= 模块操作 ================= */

    document.getElementById('module-bar').addEventListener('click', async function (e) {
        var btn = e.target.closest('.chip-btn[data-op]');
        if (!btn || !canEdit) return;
        var chip = btn.closest('.module-chip');
        var moduleId = Number(chip.getAttribute('data-module-id'));
        var module = moduleById(moduleId);
        var op = btn.getAttribute('data-op');

        if (op === 'rename') {
            openModuleRename(module);
        } else if (op === 'delete') {
            if (!window.confirm('确定删除模块「' + module.title + '」吗？\n模块内的照片将自动移入第一个剩余模块。')) return;
            await window.api('/api/modules/' + moduleId, { method: 'DELETE' });
            window.toast('模块已删除', 'success');
            await refresh();
        } else if (op === 'left' || op === 'right') {
            shiftModule(module, op === 'left' ? -1 : 1);
        }
    });

    /** 模块左右微调（移动端排序兜底） */
    async function shiftModule(module, delta) {
        var index = state.modules.findIndex(function (m) { return m.id === module.id; });
        var target = index + delta;
        if (target < 0 || target >= state.modules.length) return;
        var arr = state.modules.slice();
        arr.splice(target, 0, arr.splice(index, 1)[0]);
        await saveModuleOrder(arr);
    }

    async function saveModuleOrder(orderedModules) {
        var res = await window.api('/api/modules/sort?album_id=' + albumId, {
            method: 'PUT',
            body: { module_ids: orderedModules.map(function (m) { return m.id; }) }
        });
        state.modules = res.data;
        refreshModuleCounts();
        renderModules();
        renderSections();
    }

    /** 模块拖拽排序 */
    function bindModuleDrag(bar) {
        if (!canEdit) return;
        var dragging = null;
        bar.querySelectorAll('.module-chip').forEach(function (chip) {
            chip.addEventListener('dragstart', function () {
                dragging = chip;
                chip.classList.add('dragging');
            });
            chip.addEventListener('dragend', function () {
                chip.classList.remove('dragging');
                bar.querySelectorAll('.drop-before').forEach(function (el) { el.classList.remove('drop-before'); });
                dragging = null;
            });
            chip.addEventListener('dragover', function (e) {
                e.preventDefault();
                if (!dragging || dragging === chip) return;
                chip.classList.add('drop-before');
            });
            chip.addEventListener('dragleave', function () { chip.classList.remove('drop-before'); });
            chip.addEventListener('drop', async function (e) {
                e.preventDefault();
                if (!dragging || dragging === chip) return;
                var from = Number(dragging.getAttribute('data-module-id'));
                var to = Number(chip.getAttribute('data-module-id'));
                var arr = state.modules.slice();
                var fromIndex = arr.findIndex(function (m) { return m.id === from; });
                var toIndex = arr.findIndex(function (m) { return m.id === to; });
                arr.splice(toIndex, 0, arr.splice(fromIndex, 1)[0]);
                await saveModuleOrder(arr);
            });
        });
    }

    /* 新增 / 重命名模块（复用弹窗） */
    var moduleModal = {
        editingId: null
    };

    function openModuleCreate() {
        moduleModal.editingId = null;
        document.getElementById('module-modal-title').textContent = '新增模块';
        document.getElementById('module-input').value = '';
        window.openModal('module-modal');
    }

    function openModuleRename(module) {
        moduleModal.editingId = module.id;
        document.getElementById('module-modal-title').textContent = '重命名模块';
        document.getElementById('module-input').value = module.title;
        window.openModal('module-modal');
    }

    document.getElementById('module-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        var title = document.getElementById('module-input').value.trim();
        if (!title) { window.toast('请填写模块标题', 'error'); return; }
        if (moduleModal.editingId == null) {
            await window.api('/api/modules?album_id=' + albumId, { method: 'POST', body: { title: title } });
            window.toast('模块已创建', 'success');
        } else {
            await window.api('/api/modules/' + moduleModal.editingId, { method: 'PUT', body: { title: title } });
            window.toast('模块已更新', 'success');
        }
        window.closeModal('module-modal');
        await refresh();
    });

    /* ================= 照片上传 ================= */

    var pendingFiles = []; // { file, invalid }
    var uploadInput = document.getElementById('upload-input');
    var dropzone = document.getElementById('dropzone');
    var previewBox = document.getElementById('upload-preview');
    var moduleSelect = document.getElementById('upload-module');

    function openUploadModal() {
        // 刷新目标模块下拉
        moduleSelect.innerHTML = state.modules.map(function (m) {
            return '<option value="' + m.id + '">' + esc(m.title) + '（' + m.photo_count + ' 张）</option>';
        }).join('');
        pendingFiles = [];
        renderUploadPreview();
        window.openModal('upload-modal');
    }

    function addFiles(fileList) {
        Array.prototype.forEach.call(fileList, function (file) {
            var ext = (file.name.split('.').pop() || '').toLowerCase();
            var isVideo = VIDEO_EXTS.indexOf(ext) > -1;
            var isImage = IMAGE_EXTS.indexOf(ext) > -1;
            var limitMb = isVideo ? maxVideoUploadMb : maxUploadMb;
            var invalid = (!isImage && !isVideo) || file.size > limitMb * 1024 * 1024;
            pendingFiles.push({ file: file, isVideo: isVideo, invalid: invalid });
        });
        renderUploadPreview();
    }

    function renderUploadPreview() {
        previewBox.innerHTML = pendingFiles.map(function (item, index) {
            var url = URL.createObjectURL(item.file);
            var media = item.isVideo
                ? '<video src="' + url + '" preload="metadata" muted></video>'
                : '<img src="' + url + '" alt="预览">';
            return '' +
                '<div class="upload-thumb">' +
                '  ' + media +
                (item.isVideo ? '<div class="thumb-type">&#9654; 视频</div>' : '') +
                (item.invalid
                    ? '<div class="thumb-invalid">格式/大小不符</div>'
                    : '') +
                '  <span class="thumb-remove" data-index="' + index + '" title="移除">&times;</span>' +
                '</div>';
        }).join('');
        // 未选择文件时显示提示
        if (!pendingFiles.length) {
            previewBox.innerHTML = '<p class="col-span-full text-center text-xs text-stone-400 py-2">尚未选择图片或视频</p>';
        }
    }

    previewBox.addEventListener('click', function (e) {
        var remove = e.target.closest('.thumb-remove');
        if (!remove) return;
        pendingFiles.splice(Number(remove.getAttribute('data-index')), 1);
        renderUploadPreview();
    });

    dropzone.addEventListener('click', function () { uploadInput.click(); });
    dropzone.addEventListener('dragover', function (e) { e.preventDefault(); dropzone.classList.add('drag-over'); });
    dropzone.addEventListener('dragleave', function () { dropzone.classList.remove('drag-over'); });
    dropzone.addEventListener('drop', function (e) {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
    });
    uploadInput.addEventListener('change', function () {
        if (uploadInput.files.length) addFiles(uploadInput.files);
        uploadInput.value = '';
    });

    document.getElementById('btn-upload').addEventListener('click', openUploadModal);

    document.getElementById('btn-upload-submit').addEventListener('click', async function () {
        var valid = pendingFiles.filter(function (item) { return !item.invalid; });
        if (!valid.length) {
            window.toast('请先选择符合要求的文件（图片 jpg/png/gif/webp ≤' + maxUploadMb +
                'MB，视频 mp4/webm/mov/m4v/ogg ≤' + maxVideoUploadMb + 'MB）', 'error');
            return;
        }
        var form = new FormData();
        form.append('module_id', moduleSelect.value);
        valid.forEach(function (item) { form.append('files', item.file, item.file.name); });

        var btn = this;
        btn.disabled = true;
        btn.textContent = '上传中…';
        try {
            await window.api('/api/albums/' + albumId + '/photos', { method: 'POST', body: form });
            window.toast('成功上传 ' + valid.length + ' 个文件', 'success');
            window.closeModal('upload-modal');
            await refresh();
        } finally {
            btn.disabled = false;
            btn.textContent = '开始上传';
        }
    });

    /* ================= 照片备注 / 移动 ================= */

    var noteTargetId = null;
    var moveTargetId = null;

    function openNoteModal(photo) {
        noteTargetId = photo.id;
        var thumb = document.getElementById('note-thumb');
        if (photo.is_video) {
            thumb.classList.add('hidden'); // 视频无静态缩略图
        } else {
            thumb.src = photo.file_path;
            thumb.classList.remove('hidden');
        }
        document.getElementById('note-input').value = photo.note || '';
        window.openModal('note-modal');
    }

    document.getElementById('btn-note-save').addEventListener('click', async function () {
        var res = await window.api('/api/photos/' + noteTargetId + '/note', {
            method: 'PUT',
            body: { note: document.getElementById('note-input').value }
        });
        var index = state.photos.findIndex(function (p) { return p.id === res.data.id; });
        if (index > -1) state.photos[index] = res.data;
        window.closeModal('note-modal');
        window.toast('备注已保存', 'success');
        renderSections();
    });

    function openMoveModal(photo) {
        moveTargetId = photo.id;
        var select = document.getElementById('move-target');
        select.innerHTML = state.modules
            .filter(function (m) { return m.id !== photo.module_id; })
            .map(function (m) { return '<option value="' + m.id + '">' + esc(m.title) + '</option>'; })
            .join('');
        if (!select.innerHTML) {
            select.innerHTML = '<option value="">没有其他可移动的模块</option>';
        }
        window.openModal('move-modal');
    }

    document.getElementById('btn-move-save').addEventListener('click', async function () {
        var target = document.getElementById('move-target').value;
        if (!target) { window.toast('请选择目标模块', 'error'); return; }
        var res = await window.api('/api/photos/' + moveTargetId + '/move', {
            method: 'PUT',
            body: { module_id: Number(target) }
        });
        window.closeModal('move-modal');
        window.toast('照片已移动', 'success');
        state.photos = state.photos.map(function (p) { return p.id === res.data.id ? res.data : p; });
        renderSections();
        renderModules();
    });

    /* ================= 大图灯箱预览 ================= */

    var lightbox = {
        list: [],
        index: 0
    };

    function openLightbox(photoId) {
        lightbox.list = state.photos.slice();
        lightbox.index = lightbox.list.findIndex(function (p) { return p.id === photoId; });
        if (lightbox.index < 0) return;
        renderLightbox();
        window.openModal('lightbox');
    }

    function renderLightbox() {
        var photo = lightbox.list[lightbox.index];
        if (!photo) return;
        var img = document.getElementById('lightbox-img');
        var video = document.getElementById('lightbox-video');
        if (photo.is_video) {
            img.classList.add('hidden');
            video.src = photo.file_path;
            video.classList.remove('hidden');
            video.play().catch(function () { /* 浏览器限制自动播放时由用户手动点击播放 */ });
        } else {
            stopLightboxVideo();
            img.src = photo.file_path;
            img.classList.remove('hidden');
        }
        document.getElementById('lightbox-note').textContent = photo.note || photo.original_name || '';
        document.getElementById('lightbox-index').textContent =
            (lightbox.index + 1) + ' / ' + lightbox.list.length;
    }

    /** 暂停并复位灯箱视频（切换/关闭时调用） */
    function stopLightboxVideo() {
        var video = document.getElementById('lightbox-video');
        video.pause();
        video.currentTime = 0;
        video.classList.add('hidden');
    }

    function stepLightbox(delta) {
        if (!lightbox.list.length) return;
        lightbox.index = (lightbox.index + delta + lightbox.list.length) % lightbox.list.length;
        renderLightbox();
    }

    document.getElementById('lightbox-prev').addEventListener('click', function () { stepLightbox(-1); });
    document.getElementById('lightbox-next').addEventListener('click', function () { stepLightbox(1); });
    document.getElementById('lightbox-close').addEventListener('click', function () { window.closeModal('lightbox'); });

    // 灯箱关闭（按钮 / Esc / 点击遮罩）时暂停视频播放
    var lightboxEl = document.getElementById('lightbox');
    new MutationObserver(function () {
        if (lightboxEl.classList.contains('hidden')) stopLightboxVideo();
    }).observe(lightboxEl, { attributes: true, attributeFilter: ['class'] });

    document.addEventListener('keydown', function (e) {
        if (document.getElementById('lightbox').classList.contains('hidden')) return;
        if (e.key === 'ArrowLeft') stepLightbox(-1);
        if (e.key === 'ArrowRight') stepLightbox(1);
    });

    /* ================= 编辑记录册信息 ================= */

    var editCoverFile = null;

    document.getElementById('btn-edit-album').addEventListener('click', function () {
        document.getElementById('edit-name').value = state.album.name;
        document.getElementById('edit-desc').value = state.album.description || '';
        document.getElementById('edit-cover-preview').src = state.album.cover_image;
        editCoverFile = null;
        document.getElementById('edit-cover').value = '';
        window.openModal('edit-modal');
    });

    document.getElementById('edit-cover').addEventListener('change', function () {
        editCoverFile = this.files[0] || null;
        if (editCoverFile) {
            document.getElementById('edit-cover-preview').src = URL.createObjectURL(editCoverFile);
        }
    });

    document.getElementById('edit-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        var name = document.getElementById('edit-name').value.trim();
        if (!name) { window.toast('请填写记录册名称', 'error'); return; }
        var form = new FormData();
        form.append('name', name);
        form.append('description', document.getElementById('edit-desc').value.trim());
        if (editCoverFile) form.append('cover', editCoverFile, editCoverFile.name);
        var res = await window.api('/api/albums/' + albumId, { method: 'PUT', body: form });
        state.album = Object.assign(state.album, res.data);
        window.closeModal('edit-modal');
        window.toast('记录册信息已保存', 'success');
        renderAll();
    });

    /* ================= 风格模板切换 ================= */

    document.getElementById('template-select').addEventListener('change', async function () {
        var templateId = Number(this.value);
        var res = await window.api('/api/albums/' + albumId + '/template', {
            method: 'PUT',
            body: { template_id: templateId }
        });
        state.album = Object.assign(state.album, res.data);
        applyTemplateCss();
        var tpl = state.templates.find(function (t) { return t.id === templateId; });
        window.toast('已切换为「' + (tpl ? tpl.name : '') + '」风格', 'success');
    });

    /* ================= 视频播放（全屏幻灯片） ================= */

    document.getElementById('btn-play').addEventListener('click', function () {
        var images = state.photos.filter(function (p) { return !p.is_video; });
        if (!images.length) { window.toast('这本记录册还没有可播放的照片', 'error'); return; }
        window.AlbumPlayer.open(images, { albumId: albumId, title: state.album.name });
    });

    /* ================= 初始化 ================= */

    renderUploadHints();
    renderAll();
})();
