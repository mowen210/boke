/* ============================================================
   player.js — 记录册视频播放（全屏幻灯片）
   双缓冲 <img> + CSS 动画实现 6 种播放风格：
   淡入淡出 / 树叶飘落 / 翻书页 / 缩放聚焦 / 卷轴展开 / 旋转飞入
   支持：自动播放/暂停、上一张/下一张、速度调节、
   键盘快捷键（← → 切换、空格 播放暂停、Esc 退出）、
   风格与速度按记录册记忆（localStorage）
   由 detail.js 调用：window.AlbumPlayer.open(photos, {albumId, title})
   ============================================================ */
(function () {
    'use strict';

    /* 播放风格：code 对应 CSS 动画类前缀 anim-<code>-in/out */
    var STYLES = [
        { code: 'fade', name: '淡入淡出' },
        { code: 'leaf', name: '树叶飘落' },
        { code: 'flip', name: '翻书页' },
        { code: 'zoom', name: '缩放聚焦' },
        { code: 'wipe', name: '卷轴展开' },
        { code: 'rotate', name: '旋转飞入' }
    ];

    /* 播放速度：每张停留时长 */
    var SPEEDS = [
        { ms: 2000, name: '快速 · 2秒' },
        { ms: 4000, name: '标准 · 4秒' },
        { ms: 6000, name: '慢速 · 6秒' },
        { ms: 8000, name: '极慢 · 8秒' }
    ];

    var overlay, stage, slots, titleEl, noteEl, counterEl,
        styleSel, speedSel, toggleBtn, bar;
    var built = false;

    var st = {
        photos: [],          // 播放列表（详情页照片有序列表）
        index: 0,            // 当前照片下标
        active: 0,           // 双缓冲当前展示槽位（0/1）
        playing: false,
        style: 'fade',
        interval: 4000,      // 每张停留毫秒数
        timer: null,
        startedAt: 0,        // 当前张开始播放的时间戳（用于暂停续播）
        remaining: 0,        // 暂停后剩余停留毫秒数
        albumId: 0
    };

    function $(id) { return document.getElementById(id); }

    /* ---------------- 配置存取（localStorage 按记录册记忆） ---------------- */

    function loadConfig() {
        var style = null, interval = NaN;
        try {
            style = localStorage.getItem('album_player_style_' + st.albumId);
            interval = parseInt(localStorage.getItem('album_player_speed_' + st.albumId), 10);
        } catch (e) { /* 隐私模式等场景忽略 */ }
        st.style = STYLES.some(function (s) { return s.code === style; }) ? style : 'fade';
        st.interval = SPEEDS.some(function (s) { return s.ms === interval; }) ? interval : 4000;
    }

    function saveConfig() {
        try {
            localStorage.setItem('album_player_style_' + st.albumId, st.style);
            localStorage.setItem('album_player_speed_' + st.albumId, String(st.interval));
        } catch (e) { /* 忽略写入失败 */ }
    }

    /* ---------------- 打开 / 关闭 ---------------- */

    function open(photos, opts) {
        opts = opts || {};
        st.photos = photos.slice();
        st.albumId = opts.albumId || 0;
        st.index = 0;
        st.active = 0;
        st.remaining = 0;
        loadConfig();
        buildControls();
        titleEl.textContent = opts.title || '';
        overlay.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        showFirst();
        play();
    }

    function close() {
        pause();
        overlay.classList.add('hidden');
        if (!document.querySelector('.modal-overlay:not(.hidden)')) {
            document.body.style.overflow = '';
        }
    }

    /* ---------------- 双缓冲渲染 ---------------- */

    /** 首张直接展示（无过渡动画） */
    function showFirst() {
        var img = slots[st.active];
        img.src = st.photos[0].file_path;
        img.className = 'player-img show';
        slots[1 - st.active].className = 'player-img';
        updateCaption();
        preload(st.index + 1);
    }

    /** 切换到第 nextIndex 张：旧图按风格出场、新图按风格进场 */
    function transitionTo(nextIndex) {
        var incoming = slots[1 - st.active];
        var outgoing = slots[st.active];
        incoming.src = st.photos[nextIndex].file_path;
        incoming.className = 'player-img in anim-' + st.style + '-in';
        outgoing.className = 'player-img out anim-' + st.style + '-out';
        st.active = 1 - st.active;
        st.index = nextIndex;
        updateCaption();
        preload(nextIndex + 1);
    }

    function updateCaption() {
        var photo = st.photos[st.index] || {};
        noteEl.textContent = photo.note || photo.original_name || '';
        counterEl.textContent = (st.index + 1) + ' / ' + st.photos.length;
    }

    /** 预加载下一张，切换更顺滑 */
    function preload(i) {
        if (!st.photos.length) return;
        var photo = st.photos[i % st.photos.length];
        if (photo) {
            var img = new Image();
            img.src = photo.file_path;
        }
    }

    /* ---------------- 播放控制 ---------------- */

    function next() {
        if (st.photos.length < 2) return;
        goTo((st.index + 1) % st.photos.length);
    }

    /** 手动上一张 / 下一张 */
    function step(delta) {
        if (st.photos.length < 2) return;
        goTo((st.index + delta + st.photos.length) % st.photos.length);
    }

    /** 跳到第 i 张：播放中重置计时，暂停中仅切换画面 */
    function goTo(i) {
        clearTimeout(st.timer);
        st.remaining = 0;
        transitionTo(i);
        if (st.playing) scheduleNext();
        else bar.style.animation = 'none';
    }

    function play() {
        if (st.playing || st.photos.length < 2) { renderToggle(); return; }
        st.playing = true;
        overlay.classList.remove('paused');
        if (st.remaining > 0) {
            // 暂停续播：按剩余时间继续（进度条由 .paused 类控制恢复）
            st.timer = setTimeout(next, st.remaining);
            st.startedAt = Date.now() - (st.interval - st.remaining);
        } else {
            scheduleNext();
        }
        renderToggle();
    }

    function pause() {
        if (!st.playing) return;
        st.playing = false;
        clearTimeout(st.timer);
        st.remaining = Math.max(500, st.interval - (Date.now() - st.startedAt));
        overlay.classList.add('paused');
        renderToggle();
    }

    function togglePlay() {
        if (st.playing) pause();
        else play();
    }

    function scheduleNext() {
        st.startedAt = Date.now();
        st.timer = setTimeout(next, st.interval);
        restartBar();
    }

    function restartBar() {
        bar.style.animation = 'none';
        void bar.offsetWidth; // 强制回流，重新触发进度动画
        bar.style.animation = 'playerProgress ' + st.interval + 'ms linear forwards';
    }

    function renderToggle() {
        toggleBtn.innerHTML = st.playing ? '&#10074;&#10074;' : '&#9654;';
        toggleBtn.title = st.playing ? '暂停 (空格)' : '播放 (空格)';
    }

    /* ---------------- 顶栏控件 ---------------- */

    function buildControls() {
        if (built) {
            styleSel.value = st.style;
            speedSel.value = String(st.interval);
            return;
        }
        built = true;
        styleSel.innerHTML = STYLES.map(function (s) {
            return '<option value="' + s.code + '">' + s.name + '</option>';
        }).join('');
        speedSel.innerHTML = SPEEDS.map(function (s) {
            return '<option value="' + s.ms + '">' + s.name + '</option>';
        }).join('');
        styleSel.value = st.style;
        speedSel.value = String(st.interval);
    }

    /* ---------------- 事件绑定 ---------------- */

    function bindEvents() {
        $('player-close').addEventListener('click', close);
        $('player-prev').addEventListener('click', function () { this.blur(); step(-1); });
        $('player-next').addEventListener('click', function () { this.blur(); step(1); });
        toggleBtn.addEventListener('click', function () { this.blur(); togglePlay(); });
        // 点击画面任意处：播放 / 暂停（与视频播放器一致）
        stage.addEventListener('click', togglePlay);

        styleSel.addEventListener('change', function () {
            st.style = this.value;
            saveConfig();
            // 立即以新风格重放当前张，即时预览效果
            if (!overlay.classList.contains('hidden')) goTo(st.index);
            var tpl = STYLES.find(function (s) { return s.code === st.style; });
            window.toast('已切换为「' + (tpl ? tpl.name : '') + '」播放风格', 'success');
        });

        speedSel.addEventListener('change', function () {
            st.interval = Number(this.value);
            saveConfig();
            if (st.playing) { // 播放中调整速度：以新速度重新计时当前张
                clearTimeout(st.timer);
                scheduleNext();
            }
        });

        document.addEventListener('keydown', function (e) {
            if (overlay.classList.contains('hidden')) return;
            if (e.key === 'Escape') {
                close();
            } else if (e.key === 'ArrowLeft') {
                step(-1);
            } else if (e.key === 'ArrowRight') {
                step(1);
            } else if (e.key === ' ' || e.key === 'Spacebar') {
                e.preventDefault();
                togglePlay();
            }
        });
    }

    /* ---------------- 初始化（仅详情页存在播放器结构） ---------------- */

    overlay = $('player-overlay');
    if (!overlay) return;
    stage = $('player-stage');
    slots = [$('player-img-a'), $('player-img-b')];
    titleEl = $('player-title');
    noteEl = $('player-note');
    counterEl = $('player-counter');
    styleSel = $('player-style');
    speedSel = $('player-speed');
    toggleBtn = $('player-toggle');
    bar = $('player-bar');
    bindEvents();

    window.AlbumPlayer = { open: open };
})();
