/* ============================================================
   password.js — 顶部导航「修改密码」弹窗交互
   前端校验（非空/长度/两次一致） + 调用后端修改密码接口
   ============================================================ */
(function () {
    'use strict';

    var btnOpen = document.getElementById('btn-password');
    var form = document.getElementById('password-form');
    if (!btnOpen || !form) return; // 登录页等未登录页面不渲染该弹窗

    var oldEl = document.getElementById('pwd-old');
    var newEl = document.getElementById('pwd-new');
    var confirmEl = document.getElementById('pwd-confirm');
    var errorEl = document.getElementById('pwd-error');
    var submitBtn = document.getElementById('btn-password-submit');

    function showError(message) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    function hideError() {
        errorEl.classList.add('hidden');
    }

    btnOpen.addEventListener('click', function () {
        form.reset();
        hideError();
        submitBtn.disabled = false;
        submitBtn.textContent = '确认修改';
        window.openModal('password-modal');
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        hideError();

        // ---- 前端校验（后端 Pydantic 仍会二次校验） ----
        var oldPwd = oldEl.value;
        var newPwd = newEl.value;
        var confirmPwd = confirmEl.value;
        if (!oldPwd) return showError('请输入原密码');
        if (!newPwd) return showError('请输入新密码');
        if (newPwd.length < 6) return showError('新密码至少 6 位');
        if (newPwd !== confirmPwd) return showError('两次输入的新密码不一致');
        if (newPwd === oldPwd) return showError('新密码不能与原密码相同');

        submitBtn.disabled = true;
        submitBtn.textContent = '提交中…';
        try {
            await window.api('/api/auth/password', {
                method: 'PUT',
                silent: true,
                body: {
                    old_password: oldPwd,
                    new_password: newPwd,
                    confirm_password: confirmPwd
                }
            });
            window.closeModal('password-modal');
            window.toast('密码修改成功，下次登录请使用新密码', 'success');
        } catch (err) {
            if (err && err.message && err.message !== '未登录') showError(err.message);
            submitBtn.disabled = false;
            submitBtn.textContent = '确认修改';
        }
    });
})();
