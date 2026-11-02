/* ============================================================
   login.js — 登录页交互
   前端校验（非空/长度） + 调用后端登录接口（后端二次校验）
   ============================================================ */
(function () {
    'use strict';

    var form = document.getElementById('login-form');
    var usernameEl = document.getElementById('username');
    var passwordEl = document.getElementById('password');
    var errorEl = document.getElementById('login-error');
    var submitBtn = document.getElementById('btn-login');

    /** 显示行内错误提示 */
    function showError(message) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    function hideError() {
        errorEl.classList.add('hidden');
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError();

        // ---- 前端校验（后端 Pydantic 仍会二次校验） ----
        var username = usernameEl.value.trim();
        var password = passwordEl.value;
        if (!username) return showError('请输入账号');
        if (username.length < 2) return showError('账号至少 2 个字符');
        if (!password) return showError('请输入密码');
        if (password.length < 6) return showError('密码至少 6 位');

        submitBtn.disabled = true;
        submitBtn.textContent = '登录中…';
        try {
            var res = await window.api('/api/auth/login', {
                method: 'POST',
                silent: true,
                body: { username: username, password: password }
            });
            window.toast('登录成功，正在进入…', 'success');
            setTimeout(function () { window.location.href = '/'; }, 350);
        } catch (err) {
            // 网络错误已由 common.js 提示；此处展示接口具体错误（如账号密码错误）
            if (err && err.message && err.message !== 'Failed to fetch') {
                showError(err.message);
            } else {
                showError('登录失败，请稍后重试');
            }
            submitBtn.disabled = false;
            submitBtn.textContent = '登 录';
        }
    });
})();
