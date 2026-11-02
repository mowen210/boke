/* ============================================================
   common.js — 通用工具：API 请求封装 / 轻提示 / 模态框控制
   全站共用，需在页面 JS 之前引入
   ============================================================ */
(function () {
    'use strict';

    var FLAG = { toastCount: 0 };

    /**
     * 统一 API 请求
     * - 自动设置 JSON 头并序列化对象
     * - 401（登录失效）自动跳转登录页
     * - 非 2xx 弹出后端返回的 detail / message 提示并抛错
     */
    async function api(url, options) {
        options = options || {};
        var opt = Object.assign({ credentials: 'same-origin' }, options);
        opt.headers = Object.assign({}, options.headers || {});
        if (opt.body && !(opt.body instanceof FormData)) {
            if (!opt.headers['Content-Type']) opt.headers['Content-Type'] = 'application/json';
            if (typeof opt.body !== 'string') opt.body = JSON.stringify(opt.body);
        }
        var res;
        try {
            res = await fetch(url, opt);
        } catch (err) {
            toast('网络异常，请稍后重试', 'error');
            throw err;
        }
        if (res.status === 401) {
            window.location.href = '/login';
            throw new Error('未登录');
        }
        var data = {};
        try { data = await res.json(); } catch (e) { /* 允许空响应体 */ }
        if (!res.ok) {
            var msg = data.detail || data.message || ('请求失败 (' + res.status + ')');
            if (!opt.silent) toast(typeof msg === 'string' ? msg : JSON.stringify(msg), 'error');
            throw new Error(String(msg));
        }
        return data;
    }

    /** 轻提示：type = success | error | info */
    function toast(message, type) {
        var box = document.getElementById('toast-box');
        if (!box) return;
        var el = document.createElement('div');
        el.className = 'toast ' + (type || 'info');
        el.textContent = message;
        box.appendChild(el);
        FLAG.toastCount += 1;
        setTimeout(function () {
            el.style.transition = 'opacity .3s';
            el.style.opacity = '0';
            setTimeout(function () {
                el.remove();
                FLAG.toastCount -= 1;
            }, 300);
        }, 2400);
    }

    /** 打开模态框（锁定页面滚动） */
    function openModal(id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        var first = el.querySelector('input:not([type=hidden]), textarea, select');
        if (first) setTimeout(function () { first.focus(); }, 60);
    }

    /** 关闭模态框（恢复页面滚动） */
    function closeModal(id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.classList.add('hidden');
        if (!document.querySelector('.modal-overlay:not(.hidden)')) {
            document.body.style.overflow = '';
        }
    }

    // 点击遮罩空白处关闭模态框
    document.addEventListener('click', function (e) {
        if (e.target.classList && e.target.classList.contains('modal-overlay')) closeModal(e.target.id);
    });
    // Esc 关闭最上层模态框
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape') return;
        var opened = document.querySelectorAll('.modal-overlay:not(.hidden)');
        if (opened.length) closeModal(opened[opened.length - 1].id);
    });
    // data-close="modal-id" 通用关闭按钮
    document.addEventListener('click', function (e) {
        var target = e.target.closest ? e.target.closest('[data-close]') : null;
        if (target) closeModal(target.getAttribute('data-close'));
    });

    /** HTML 转义，防止用户输入注入（XSS） */
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    }

    /** 文件大小格式化 */
    function formatSize(bytes) {
        if (!bytes && bytes !== 0) return '';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1024 / 1024).toFixed(2) + ' MB';
    }

    window.api = api;
    window.toast = toast;
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.escapeHtml = escapeHtml;
    window.formatSize = formatSize;
})();
