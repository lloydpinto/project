// ===================== FORGOT PASSWORD JS =====================

const API_BASE = window.location.origin + '/api';

// ── Company Logo URL — change this to match your login page ──
const COMPANY_LOGO_URL = "./images/Future_Connect.png";

let _resetEmail = '';

document.addEventListener('DOMContentLoaded', () => {
    // Apply logo
    if (COMPANY_LOGO_URL && COMPANY_LOGO_URL !== "./images/Future_Connect.png") {
        document.querySelectorAll('[data-company-logo]').forEach(img => {
            img.src = COMPANY_LOGO_URL;
        });
    }

    // If page opened with ?token=...&email=... go straight to step 2
    const params = new URLSearchParams(window.location.search);
    const token  = params.get('token');
    const email  = params.get('email');

    if (token && email) {
        _resetEmail = decodeURIComponent(email);
        document.getElementById('resetToken').value = token;
        if (document.getElementById('resetEmailStep2')) {
            document.getElementById('resetEmailStep2').value = _resetEmail;
        }
        _goToStep(2);

        // Show a helpful info message
        showAlert2(
            'Reset link detected! Enter your new password below.',
            'info'
        );
    }
});

// ════════════════════════════════════════════════
//  STEP NAVIGATION
// ════════════════════════════════════════════════

function _goToStep(step) {
    [1, 2, 3].forEach(n => {
        const el = document.getElementById(`step${n}`);
        if (el) el.classList.toggle('active', n === step);
    });
}

// ════════════════════════════════════════════════
//  STEP 1 — Request Reset Email
// ════════════════════════════════════════════════

async function requestReset(event) {
    event.preventDefault();

    const email = document.getElementById('resetEmail').value.trim();
    if (!email) {
        showAlert1('Please enter your email address.', 'error'); return;
    }
    if (!email.includes('@')) {
        showAlert1('Please enter a valid email address.', 'error'); return;
    }

    const btn = document.getElementById('requestResetBtn');
    setButtonLoading(btn, true, 'Sending...');
    _resetEmail = email;

    try {
        const res  = await fetch(`${API_BASE}/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await res.json();

        if (res.ok) {
            if (data.dev_mode) {
                // Development mode — show token
                _resetEmail = email;
                document.getElementById('resetToken').value = data.dev_token || '';
                _goToStep(2);
                showAlert2(
                    `Development mode: Email service not configured. Token auto-filled below.`,
                    'warning'
                );
            } else {
                // Real email sent — show confirmation screen
                _goToStep(2);
                showAlert2(
                    `A password reset link has been sent to <strong>${escapeHtml(email)}</strong>. 
                     Please check your inbox and spam/junk folder. 
                     The link expires in 60 minutes.`,
                    'success'
                );
                // Hide token field — user clicks the email link
                const tokenField = document.getElementById('tokenFieldWrap');
                if (tokenField) tokenField.style.display = 'none';
            }
        } else {
            showAlert1(data.error || 'Something went wrong. Please try again.', 'error');
        }
    } catch (e) {
        showAlert1('Connection error. Please check your network.', 'error');
    } finally {
        setButtonLoading(btn, false, 'Send Reset Link');
    }
}

// ════════════════════════════════════════════════
//  STEP 2 — Set New Password
// ════════════════════════════════════════════════

async function resetPassword(event) {
    event.preventDefault();

    const token    = document.getElementById('resetToken').value.trim();
    const newPw    = document.getElementById('newPassword').value;
    const confirmPw = document.getElementById('confirmNewPassword').value;

    if (!token) {
        showAlert2('Reset token is missing. Please use the link from your email.', 'error');
        return;
    }
    if (!newPw) {
        showAlert2('Please enter a new password.', 'error'); return;
    }
    if (newPw.length < 8) {
        showAlert2('Password must be at least 8 characters.', 'error'); return;
    }
    if (newPw !== confirmPw) {
        showAlert2('Passwords do not match.', 'error'); return;
    }

    // Get email — from URL params, or from step 2 email field
    let email = _resetEmail;
    const emailStep2El = document.getElementById('resetEmailStep2');
    if (!email && emailStep2El) {
        email = emailStep2El.value.trim();
    }
    if (!email) {
        showAlert2('Email address is missing. Please go back and try again.', 'error');
        return;
    }

    const btn = document.getElementById('resetPasswordBtn');
    setButtonLoading(btn, true, 'Resetting...');

    try {
        const res  = await fetch(`${API_BASE}/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                reset_token:      token,
                new_password:     newPw,
                confirm_password: confirmPw,
            })
        });
        const data = await res.json();

        if (res.ok) {
            _goToStep(3);
        } else {
            showAlert2(data.error || 'Reset failed. Please try again.', 'error');
        }
    } catch (e) {
        showAlert2('Connection error. Please try again.', 'error');
    } finally {
        setButtonLoading(btn, false, 'Reset Password');
    }
}

// ════════════════════════════════════════════════
//  HELPERS
// ════════════════════════════════════════════════

function togglePassword(inputId, btn) {
    const input  = document.getElementById(inputId);
    const isPass = input.type === 'password';
    input.type   = isPass ? 'text' : 'password';
    btn.innerHTML = isPass
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8
                        a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4
                        c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19
                        m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
               <line x1="1" y1="1" x2="23" y2="23"/>
           </svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
               <circle cx="12" cy="12" r="3"/>
           </svg>`;
}

function setButtonLoading(btn, loading, label) {
    if (!btn) return;
    btn.disabled = loading;
    btn.innerHTML = loading
        ? `<span class="btn-spinner"></span> ${label}`
        : label;
}

function showAlert1(msg, type) {
    _showAlert('resetAlert1', msg, type);
}

function showAlert2(msg, type) {
    _showAlert('resetAlert2', msg, type);
}

function _showAlert(containerId, msg, type) {
    const c = document.getElementById(containerId);
    if (!c) return;
    const icons = { error: '⚠', success: '✓', info: 'ℹ', warning: '⚠' };
    c.innerHTML = `
        <div class="alert alert-${type}">
            <span class="alert-icon">${icons[type] || 'ℹ'}</span>
            <span class="alert-content">${msg}</span>
        </div>`;
}

function showToast(title, message, type) {
    const c = document.getElementById('toastContainer');
    if (!c) return;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ'}</span>
        <div class="toast-body">
            <div class="toast-title">${escapeHtml(title)}</div>
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
        <div class="toast-progress"></div>`;
    c.appendChild(t);
    setTimeout(() => { if (t.parentElement) t.remove(); }, 5000);
}

function escapeHtml(text) {
    if (!text) return '';
    const d = document.createElement('div');
    d.textContent = String(text);
    return d.innerHTML;
}