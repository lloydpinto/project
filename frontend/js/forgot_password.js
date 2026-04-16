const API_BASE = window.location.origin + '/api';
let resetEmail = '';

async function requestReset(event) {
    event.preventDefault();
    const email = document.getElementById('resetEmail').value.trim();
    if (!email) { showResetAlert('Please enter your email.', 'error', 'resetAlert'); return; }

    const btn = document.getElementById('requestResetBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-spinner"></span> Sending...';

    try {
        const res = await fetch(`${API_BASE}/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (res.ok) {
            resetEmail = email;
            document.getElementById('step1').classList.remove('active');
            document.getElementById('step2').classList.add('active');
            if (data.reset_token) {
                document.getElementById('tokenDisplay').style.display = 'flex';
                document.getElementById('tokenValue').textContent = data.reset_token;
                document.getElementById('resetToken').value = data.reset_token;
            }
            showToast('Token sent', 'Reset token generated successfully.', 'success');
        } else {
            showResetAlert(data.error || 'Request failed.', 'error', 'resetAlert');
        }
    } catch (e) {
        showResetAlert('Connection error.', 'error', 'resetAlert');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Send Reset Token';
    }
}

async function resetPassword(event) {
    event.preventDefault();
    const token = document.getElementById('resetToken').value.trim();
    const newPw = document.getElementById('newPassword').value;
    const confirmPw = document.getElementById('confirmNewPassword').value;

    if (!token || !newPw || !confirmPw) { showResetAlert('All fields required.', 'error', 'resetAlert2'); return; }
    if (newPw.length < 8) { showResetAlert('Password must be at least 8 characters.', 'error', 'resetAlert2'); return; }
    if (newPw !== confirmPw) { showResetAlert('Passwords do not match.', 'error', 'resetAlert2'); return; }

    try {
        const res = await fetch(`${API_BASE}/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: resetEmail, reset_token: token, new_password: newPw })
        });
        const data = await res.json();
        if (res.ok) {
            document.getElementById('step2').classList.remove('active');
            document.getElementById('step3').classList.add('active');
            showToast('Success', 'Password reset successfully.', 'success');
        } else {
            showResetAlert(data.error || 'Reset failed.', 'error', 'resetAlert2');
        }
    } catch (e) {
        showResetAlert('Connection error.', 'error', 'resetAlert2');
    }
}

function showResetAlert(msg, type, id) {
    document.getElementById(id).innerHTML = `<div class="alert alert-${type}"><span class="alert-icon">${type === 'error' ? '⚠' : '✓'}</span><span class="alert-content">${msg}</span></div>`;
}

function togglePassword(id, btn) {
    const input = document.getElementById(id);
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    btn.innerHTML = isPassword
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
}

function showToast(title, message, type) {
    const c = document.getElementById('toastContainer');
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.innerHTML = `<span class="toast-icon">${type === 'success' ? '✓' : 'ℹ'}</span><div class="toast-body"><div class="toast-title">${title}</div><div class="toast-message">${message}</div></div><button class="toast-close" onclick="this.parentElement.remove()">✕</button><div class="toast-progress"></div>`;
    c.appendChild(t);
    setTimeout(() => { if (t.parentElement) t.remove(); }, 4000);
}