const API_BASE = window.location.origin + '/api';

function switchTab(tab) {
    document.querySelectorAll('.auth-tab-btn').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

    document.getElementById('loginPanel').classList.toggle('active', tab === 'login');
    document.getElementById('registerPanel').classList.toggle('active', tab === 'register');

    const title = document.getElementById('authTitle');
    const subtitle = document.getElementById('authSubtitle');
    const switchText = document.getElementById('switchText');
    const switchLink = document.getElementById('switchLink');

    if (tab === 'login') {
        title.textContent = 'Welcome back';
        subtitle.textContent = 'Enter your credentials to access your account';
        switchText.textContent = "Don't have an account?";
        switchLink.textContent = 'Create one';
    } else {
        title.textContent = 'Create your account';
        subtitle.textContent = 'Get started with Authorized Partners';
        switchText.textContent = 'Already have an account?';
        switchLink.textContent = 'Sign in';
    }
    hideAlert();
}

function generateMachineId() {
    const c = document.createElement('canvas');
    const ctx = c.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('fp', 2, 2);
    const d = c.toDataURL();
    const raw = `${navigator.userAgent}|${screen.width}x${screen.height}x${screen.colorDepth}|${Intl.DateTimeFormat().resolvedOptions().timeZone}|${navigator.language}|${navigator.platform||''}|${d}`;
    let hash = 0;
    for (let i = 0; i < raw.length; i++) {
        hash = ((hash << 5) - hash) + raw.charCodeAt(i);
        hash = hash & hash;
    }
    return Math.abs(hash).toString(36) + Date.now().toString(36);
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const rememberMe = document.getElementById('rememberMe').checked;

    if (!username || !password) { showAlert('Please fill in all fields.', 'error'); return; }

    const btn = document.getElementById('loginBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-spinner"></span> Signing in...';
    showLoading(true);

    try {
        const machineId = generateMachineId();
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, machine_id: machineId })
        });
        const data = await res.json();

        if (res.ok) {
            const storage = rememberMe ? localStorage : sessionStorage;
            storage.setItem('access_token', data.access_token);
            storage.setItem('refresh_token', data.refresh_token);
            storage.setItem('user', JSON.stringify(data.user));
            storage.setItem('machine_id', machineId);
            showToast('Login successful', 'Redirecting to dashboard...', 'success');
            setTimeout(() => { window.location.href = '/dashboard'; }, 600);
        } else {
            showAlert(data.error || 'Invalid credentials. Please try again.', 'error');
        }
    } catch (e) {
        showAlert('Connection error. Please check your network.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
        showLoading(false);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const firstName = document.getElementById('regFirstName').value.trim();
    const lastName = document.getElementById('regLastName').value.trim();
    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    if (!firstName || !lastName || !username || !email || !password) {
        showAlert('All fields are required.', 'error'); return;
    }
    if (username.length < 3) { showAlert('Username must be at least 3 characters.', 'error'); return; }
    if (password.length < 8) { showAlert('Password must be at least 8 characters.', 'error'); return; }
    if (password !== confirmPassword) { showAlert('Passwords do not match.', 'error'); return; }

    const btn = document.getElementById('registerBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-spinner"></span> Creating account...';
    showLoading(true);

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ first_name: firstName, last_name: lastName, username, email, password, machine_id: generateMachineId() })
        });
        const data = await res.json();

        if (res.ok) {
            showToast('Account created', 'You can now sign in.', 'success');
            showAlert('Registration successful! Please sign in.', 'success');
            setTimeout(() => switchTab('login'), 1500);
            document.getElementById('registerForm').reset();
            document.getElementById('strengthBar').className = 'meter-fill';
            document.getElementById('strengthText').textContent = '';
        } else {
            showAlert(data.error || 'Registration failed.', 'error');
        }
    } catch (e) {
        showAlert('Connection error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
        showLoading(false);
    }
}

function checkPasswordStrength(pw) {
    const bar = document.getElementById('strengthBar');
    const text = document.getElementById('strengthText');
    if (!pw) { bar.className = 'meter-fill'; text.textContent = ''; return; }
    let s = 0;
    if (pw.length >= 8) s++;
    if (pw.length >= 12) s++;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++;
    if (/\d/.test(pw)) s++;
    if (/[^a-zA-Z0-9]/.test(pw)) s++;
    const levels = ['', 'weak', 'fair', 'good', 'strong', 'strong'];
    const labels = ['', 'Weak', 'Fair', 'Good', 'Strong', 'Very strong'];
    bar.className = `meter-fill ${levels[s]}`;
    text.textContent = labels[s];
}

function togglePassword(id, btn) {
    const input = document.getElementById(id);
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    btn.innerHTML = isPassword
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
        : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
}

function showAlert(msg, type) {
    const c = document.getElementById('authAlert');
    c.innerHTML = `<div class="alert alert-${type}"><span class="alert-icon">${type === 'error' ? '⚠' : '✓'}</span><span class="alert-content">${msg}</span><button class="alert-close" onclick="hideAlert()">✕</button></div>`;
}

function hideAlert() { document.getElementById('authAlert').innerHTML = ''; }

function showToast(title, message, type) {
    const c = document.getElementById('toastContainer');
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    t.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ'}</span><div class="toast-body"><div class="toast-title">${title}</div><div class="toast-message">${message}</div></div><button class="toast-close" onclick="this.parentElement.remove()">✕</button><div class="toast-progress"></div>`;
    c.appendChild(t);
    setTimeout(() => { if (t.parentElement) t.remove(); }, 4000);
}

function showLoading(show) {
    const el = document.getElementById('loadingOverlay');
    if (show) el.classList.add('active'); else el.classList.remove('active');
}

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (token) {
        fetch(`${API_BASE}/auth/profile`, { headers: { Authorization: `Bearer ${token}` } })
            .then(r => { if (r.ok) window.location.href = '/dashboard'; else { localStorage.removeItem('access_token'); sessionStorage.removeItem('access_token'); } })
            .catch(() => {});
    }
});