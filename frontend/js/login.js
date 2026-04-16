// ===================== LOGIN PAGE JS =====================

const API_BASE = window.location.origin + '/api';

// ── Company Logo URL (set once, used everywhere) ──
// Change this to your actual logo URL or '/logo.png'
const COMPANY_LOGO_URL = "./images/Future_Connect.png";

// ── Apply logo to all img tags on this page ──
document.addEventListener('DOMContentLoaded', () => {
    if (COMPANY_LOGO_URL && COMPANY_LOGO_URL !== "./images/Future_Connect.png") {
        document.querySelectorAll('[data-company-logo]').forEach(img => {
            img.src = COMPANY_LOGO_URL;
        });
    }
    initLoginPage();
});

function initLoginPage() {
    // Check if already logged in → redirect to dashboard
    const token = localStorage.getItem('access_token') ||
                  sessionStorage.getItem('access_token');
    if (token) {
        fetch(`${API_BASE}/auth/profile`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        .then(r => {
            if (r.ok) window.location.href = '/dashboard';
            else {
                localStorage.removeItem('access_token');
                sessionStorage.removeItem('access_token');
            }
        })
        .catch(() => {});
    }

    // ── Remember Me — restore saved credentials ──
    restoreSavedCredentials();
}

// ════════════════════════════════════════════════
//  REMEMBER ME
// ════════════════════════════════════════════════

const REMEMBER_KEY   = 'ap_remember';
const SAVED_USER_KEY = 'ap_saved_username';
const SAVED_PASS_KEY = 'ap_saved_password_enc';

function restoreSavedCredentials() {
    try {
        const remember = localStorage.getItem(REMEMBER_KEY) === 'true';
        if (!remember) return;

        const savedUser = localStorage.getItem(SAVED_USER_KEY) || '';
        const savedPass = _decodePass(localStorage.getItem(SAVED_PASS_KEY) || '');

        const usernameEl = document.getElementById('loginUsername');
        const passwordEl = document.getElementById('loginPassword');
        const rememberEl = document.getElementById('rememberMe');

        if (usernameEl && savedUser) usernameEl.value = savedUser;
        if (passwordEl && savedPass) passwordEl.value = savedPass;
        if (rememberEl) rememberEl.checked = true;
    } catch (e) {
        // Silently fail
    }
}

function saveCredentials(username, password) {
    try {
        localStorage.setItem(REMEMBER_KEY, 'true');
        localStorage.setItem(SAVED_USER_KEY, username);
        localStorage.setItem(SAVED_PASS_KEY, _encodePass(password));
    } catch (e) {}
}

function clearSavedCredentials() {
    try {
        localStorage.removeItem(REMEMBER_KEY);
        localStorage.removeItem(SAVED_USER_KEY);
        localStorage.removeItem(SAVED_PASS_KEY);
    } catch (e) {}
}

// Simple reversible obfuscation (NOT encryption — just hides from casual view)
function _encodePass(str) {
    try {
        return btoa(unescape(encodeURIComponent(str)));
    } catch (e) { return ''; }
}

function _decodePass(enc) {
    try {
        return decodeURIComponent(escape(atob(enc)));
    } catch (e) { return ''; }
}

// ════════════════════════════════════════════════
//  MACHINE ID
// ════════════════════════════════════════════════

function generateMachineId() {
    const cached = localStorage.getItem('ap_machine_id');
    if (cached) return cached;
    try {
        const c   = document.createElement('canvas');
        const ctx = c.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('ap_fp', 2, 2);
        const raw = [
            navigator.userAgent,
            screen.width, screen.height, screen.colorDepth,
            Intl.DateTimeFormat().resolvedOptions().timeZone,
            navigator.language,
            navigator.platform || '',
            c.toDataURL()
        ].join('|');
        let hash = 0;
        for (let i = 0; i < raw.length; i++) {
            hash = ((hash << 5) - hash) + raw.charCodeAt(i);
            hash |= 0;
        }
        const id = Math.abs(hash).toString(36) + Date.now().toString(36);
        localStorage.setItem('ap_machine_id', id);
        return id;
    } catch (e) {
        const id = Math.random().toString(36).slice(2);
        localStorage.setItem('ap_machine_id', id);
        return id;
    }
}

// ════════════════════════════════════════════════
//  TAB SWITCH
// ════════════════════════════════════════════════

function switchTab(tab) {
    document.querySelectorAll('.auth-tab-btn').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

    document.getElementById('loginPanel').classList.toggle('active', tab === 'login');
    document.getElementById('registerPanel').classList.toggle('active', tab === 'register');

    const isLogin = tab === 'login';
    document.getElementById('authTitle').textContent =
        isLogin ? 'Welcome back' : 'Create your account';
    document.getElementById('authSubtitle').textContent =
        isLogin ? 'Enter your credentials to access your account'
                : 'Get started with Authorized Partners';
    document.getElementById('switchText').textContent =
        isLogin ? "Don't have an account?" : 'Already have an account?';
    document.getElementById('switchLink').textContent =
        isLogin ? 'Create one' : 'Sign in';

    hideAlert();
}

// ════════════════════════════════════════════════
//  LOGIN
// ════════════════════════════════════════════════

async function handleLogin(event) {
    event.preventDefault();

    const username   = document.getElementById('loginUsername').value.trim();
    const password   = document.getElementById('loginPassword').value;
    const rememberMe = document.getElementById('rememberMe').checked;

    if (!username) { showAlert('Please enter your username or email.', 'error'); return; }
    if (!password) { showAlert('Please enter your password.', 'error'); return; }

    const btn = document.getElementById('loginBtn');
    setButtonLoading(btn, true, 'Signing in...');
    showLoading(true);

    try {
        const machineId = generateMachineId();
        const res  = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, machine_id: machineId })
        });
        const data = await res.json();

        if (res.ok) {
            // ── Store auth tokens ──
            // Always put access_token in sessionStorage for security
            // Put in localStorage too only if Remember Me is checked
            sessionStorage.setItem('access_token',  data.access_token);
            sessionStorage.setItem('refresh_token', data.refresh_token);
            sessionStorage.setItem('user', JSON.stringify(data.user));
            sessionStorage.setItem('machine_id', machineId);

            if (rememberMe) {
                localStorage.setItem('access_token',  data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                localStorage.setItem('machine_id', machineId);
                // Save credentials for auto-fill
                saveCredentials(username, password);
            } else {
                // Clear any previously saved credentials
                clearSavedCredentials();
            }

            showToast('Login successful', 'Redirecting to dashboard...', 'success');
            setTimeout(() => { window.location.href = '/dashboard'; }, 600);
        } else {
            showAlert(data.error || 'Login failed. Please try again.', 'error');
        }
    } catch (e) {
        showAlert('Connection error. Please check your network and try again.', 'error');
    } finally {
        setButtonLoading(btn, false, 'Sign In');
        showLoading(false);
    }
}

// ════════════════════════════════════════════════
//  REGISTER
// ════════════════════════════════════════════════

async function handleRegister(event) {
    event.preventDefault();

    const firstName      = document.getElementById('regFirstName').value.trim();
    const lastName       = document.getElementById('regLastName').value.trim();
    const username       = document.getElementById('regUsername').value.trim();
    const email          = document.getElementById('regEmail').value.trim();
    const password       = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    if (!firstName || !lastName || !username || !email || !password) {
        showAlert('All fields are required.', 'error'); return;
    }
    if (username.length < 3) {
        showAlert('Username must be at least 3 characters.', 'error'); return;
    }
    if (password.length < 8) {
        showAlert('Password must be at least 8 characters.', 'error'); return;
    }
    if (password !== confirmPassword) {
        showAlert('Passwords do not match.', 'error'); return;
    }

    const btn = document.getElementById('registerBtn');
    setButtonLoading(btn, true, 'Creating account...');
    showLoading(true);

    try {
        const res  = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                first_name: firstName, last_name: lastName,
                username, email, password,
                machine_id: generateMachineId()
            })
        });
        const data = await res.json();

        if (res.ok) {
            showToast(
                'Account created!',
                'Check your email for a welcome message. You can now sign in.',
                'success'
            );
            showAlert(
                'Registration successful! A welcome email has been sent. You can now sign in.',
                'success'
            );
            document.getElementById('registerForm').reset();
            document.getElementById('strengthBar').className = 'meter-fill';
            document.getElementById('strengthText').textContent = '';
            setTimeout(() => switchTab('login'), 2000);
        } else {
            showAlert(data.error || 'Registration failed. Please try again.', 'error');
        }
    } catch (e) {
        showAlert('Connection error. Please try again.', 'error');
    } finally {
        setButtonLoading(btn, false, 'Create Account');
        showLoading(false);
    }
}

// ════════════════════════════════════════════════
//  PASSWORD STRENGTH
// ════════════════════════════════════════════════

function checkPasswordStrength(pw) {
    const bar  = document.getElementById('strengthBar');
    const text = document.getElementById('strengthText');
    if (!pw) { bar.className = 'meter-fill'; text.textContent = ''; return; }

    let score = 0;
    if (pw.length >= 8)  score++;
    if (pw.length >= 12) score++;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
    if (/\d/.test(pw))   score++;
    if (/[^a-zA-Z0-9]/.test(pw)) score++;

    const levels = [
        { class: '',       label: '' },
        { class: 'weak',   label: 'Weak' },
        { class: 'weak',   label: 'Weak' },
        { class: 'fair',   label: 'Fair' },
        { class: 'good',   label: 'Good' },
        { class: 'strong', label: 'Strong' },
    ];
    const lvl = levels[Math.min(score, levels.length - 1)];
    bar.className  = `meter-fill ${lvl.class}`;
    text.textContent = lvl.label;
}

// ════════════════════════════════════════════════
//  TOGGLE PASSWORD VISIBILITY
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

// ════════════════════════════════════════════════
//  UI HELPERS
// ════════════════════════════════════════════════

function setButtonLoading(btn, loading, label) {
    if (!btn) return;
    btn.disabled = loading;
    btn.innerHTML = loading
        ? `<span class="btn-spinner"></span> ${label}`
        : label;
}

function showAlert(msg, type = 'error') {
    const c = document.getElementById('authAlert');
    if (!c) return;
    const icons = { error: '⚠', success: '✓', info: 'ℹ', warning: '⚠' };
    c.innerHTML = `
        <div class="alert alert-${type}">
            <span class="alert-icon">${icons[type] || 'ℹ'}</span>
            <span class="alert-content">${escapeHtml(msg)}</span>
            <button class="alert-close" onclick="hideAlert()">✕</button>
        </div>`;
}

function hideAlert() {
    const c = document.getElementById('authAlert');
    if (c) c.innerHTML = '';
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

function showLoading(show) {
    const el = document.getElementById('loadingOverlay');
    if (el) { if (show) el.classList.add('active'); else el.classList.remove('active'); }
}

function escapeHtml(text) {
    if (!text) return '';
    const d = document.createElement('div');
    d.textContent = String(text);
    return d.innerHTML;
}