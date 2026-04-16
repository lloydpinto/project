import os
import sys
import tempfile

# ── Path setup ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Resolve writable DB path ──
def _resolve_db_uri():
    env_url = os.environ.get('DATABASE_URL', '')
    if env_url:
        if env_url.startswith('postgres://'):
            env_url = env_url.replace('postgres://', 'postgresql://', 1)
        return env_url
    candidates = [
        os.path.join(BASE_DIR, 'authorized_partners.db'),
        os.path.join(os.path.dirname(BASE_DIR), 'authorized_partners.db'),
        os.path.join(tempfile.gettempdir(), 'authorized_partners.db'),
        '/tmp/authorized_partners.db',
    ]
    for path in candidates:
        try:
            folder = os.path.dirname(path) or '.'
            os.makedirs(folder, exist_ok=True)
            probe = os.path.join(folder, '.db_probe')
            with open(probe, 'w') as fh:
                fh.write('ok')
            os.remove(probe)
            print(f"[DB] Using: {path}")
            return f'sqlite:///{path}'
        except Exception as exc:
            print(f"[DB] Skipping {path}: {exc}")
    fallback = os.path.join(tempfile.gettempdir(), 'authorized_partners.db')
    return f'sqlite:///{fallback}'


DB_URI = _resolve_db_uri()

# ── Imports ──
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, create_refresh_token
)
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import json, uuid, secrets, hashlib
import platform as _platform
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
if not os.path.isdir(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

COMPANY_NAME  = os.environ.get('COMPANY_NAME', 'Authorized Partners')
FRONTEND_URL  = os.environ.get('FRONTEND_URL', 'http://localhost:5000')

print(f"[App] BASE_DIR    : {BASE_DIR}")
print(f"[App] FRONTEND    : {FRONTEND_DIR} (exists={os.path.isdir(FRONTEND_DIR)})")
print(f"[App] DB_URI      : {DB_URI}")
print(f"[App] COMPANY     : {COMPANY_NAME}")
print(f"[App] FRONTEND_URL: {FRONTEND_URL}")

# ── Flask App ──
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

# ── Config ──
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-change-me'),
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'dev-jwt-change-me'),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=8),
    SQLALCHEMY_DATABASE_URI=DB_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': ({'check_same_thread': False}
                         if DB_URI.startswith('sqlite') else {}),
    },
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    PRODUCTS_JSON_PATH=os.path.join(DATA_DIR, 'products.json'),
    # ── Mail ──
    MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
    MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true',
    MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true',
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME', ''),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD', ''),
    MAIL_DEFAULT_SENDER=(
        COMPANY_NAME,
        os.environ.get('MAIL_DEFAULT_SENDER',
                       os.environ.get('MAIL_USERNAME', ''))
    ),
    MAIL_MAX_EMAILS=None,
    MAIL_ASCII_ATTACHMENTS=False,
)

# ── Extensions ──
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
jwt   = JWTManager(app)
bcrypt = Bcrypt(app)
mail  = Mail(app)

# ── Database ──
DB_AVAILABLE = False
try:
    from database import db, init_db
    from models import User, LoginHistory, ProductCache
    init_db(app)
    DB_AVAILABLE = True
    print("[DB] Initialized OK")
except Exception as _err:
    print(f"[DB] Init failed: {_err}")


# ════════════════════════════════════════════════
#  UTILITY
# ════════════════════════════════════════════════

def _safe_num(val, default=0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _gen_machine_id():
    try:
        raw = f"{_platform.node()}-{_platform.system()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return str(uuid.uuid4())[:32]


def _products_path():
    return app.config.get('PRODUCTS_JSON_PATH',
                          os.path.join(DATA_DIR, 'products.json'))


def _ensure_products():
    path = _products_path()
    if not os.path.exists(path):
        default = {"Sheet1": [
            {"Sl.No": 1, "Make": "Sample Brand", "Model": "SB-001",
             "Description": "Sample product", "Quantity": 1, "Net Price": 1000.0}
        ]}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(default, fh, indent=2)


def load_products():
    _ensure_products()
    path = _products_path()
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {"Sheet1": []}
        if 'Sheet1' not in data:
            for k, v in data.items():
                if isinstance(v, list):
                    data = {'Sheet1': v}
                    break
            else:
                data = {'Sheet1': []}
        clean = []
        for row in data.get('Sheet1', []):
            if not isinstance(row, dict):
                continue
            make = str(row.get('Make', '') or '').strip()
            if not make:
                continue
            clean.append({
                'Sl.No': row.get('Sl.No'),
                'Make': make,
                'Model': str(row.get('Model', '') or '').strip(),
                'Description': str(row.get('Description', '') or '').strip() or None,
                'Quantity': _safe_num(row.get('Quantity'), 1),
                'Net Price': _safe_num(row.get('Net Price'), 0.0),
            })
        data['Sheet1'] = clean
        return data
    except Exception as exc:
        return {"Sheet1": [], "error": str(exc)}


def save_products(data):
    path = _products_path()
    backup = path + '.backup'
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            import shutil
            shutil.copy2(path, backup)
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        return True, "Saved"
    except Exception as exc:
        if os.path.exists(backup):
            import shutil
            shutil.copy2(backup, path)
        return False, str(exc)


# ════════════════════════════════════════════════
#  EMAIL HELPERS
# ════════════════════════════════════════════════

LOGO_URL = os.environ.get('LOGO_URL', '')

def _email_base(title, preview_text=''):
    """Returns the opening HTML for all emails."""
    logo_html = ''
    if LOGO_URL:
        logo_html = f'''
        <div style="text-align:center;margin-bottom:24px;">
            <img src="{LOGO_URL}" alt="{COMPANY_NAME}"
                 style="max-height:60px;max-width:200px;object-fit:contain;">
        </div>'''
    else:
        logo_html = f'''
        <div style="text-align:center;margin-bottom:24px;">
            <div style="display:inline-block;background:linear-gradient(135deg,#0f2027,#2c5364);
                        padding:12px 24px;border-radius:10px;">
                <span style="color:white;font-weight:800;font-size:18px;
                             letter-spacing:-0.02em;">{COMPANY_NAME}</span>
            </div>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f5f6f8;
             font-family:'Segoe UI',Arial,sans-serif;-webkit-font-smoothing:antialiased;">
<span style="display:none;max-height:0;overflow:hidden;">{preview_text}</span>

<!-- Wrapper -->
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:#f5f6f8;padding:40px 16px;">
  <tr>
    <td align="center">
      <!-- Card -->
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="max-width:560px;background:#ffffff;border-radius:16px;
                    box-shadow:0 4px 24px rgba(16,24,40,0.08);overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#0f2027 0%,#203a43 50%,#2c5364 100%);
                     padding:32px 40px 28px;">
            {logo_html}
            <h1 style="margin:0;color:white;font-size:22px;font-weight:800;
                       letter-spacing:-0.02em;text-align:center;">{title}</h1>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
'''


def _email_footer():
    return f'''
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#f8f9fb;padding:24px 40px;
                     border-top:1px solid #e5e7ec;text-align:center;">
            <p style="margin:0 0 8px;color:#8b91a0;font-size:13px;line-height:1.6;">
              This email was sent by <strong>{COMPANY_NAME}</strong>.
              If you did not request this, please ignore this email.
            </p>
            <p style="margin:0;color:#a3aab8;font-size:12px;">
              © {datetime.utcnow().year} {COMPANY_NAME}. All rights reserved.
            </p>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>'''


def send_password_reset_email(user, reset_token):
    """Send a professional password reset email with a clickable link."""
    reset_url = f"{FRONTEND_URL}/forgot-password?token={reset_token}&email={user.email}"
    expires_min = 60

    html_body = _email_base(
        title='Reset Your Password',
        preview_text='You requested a password reset. Click the button below.'
    ) + f'''
    <p style="margin:0 0 16px;color:#5a6070;font-size:16px;line-height:1.7;">
        Hi <strong style="color:#1a1d23;">{user.first_name}</strong>,
    </p>
    <p style="margin:0 0 24px;color:#5a6070;font-size:15px;line-height:1.7;">
        We received a request to reset the password for your
        <strong>{COMPANY_NAME}</strong> account.
        Click the button below to choose a new password.
    </p>

    <!-- Reset Button -->
    <div style="text-align:center;margin:32px 0;">
        <a href="{reset_url}"
           style="display:inline-block;background:linear-gradient(135deg,#1a5cf5,#1448e1);
                  color:white;text-decoration:none;font-size:16px;font-weight:700;
                  padding:16px 40px;border-radius:10px;
                  box-shadow:0 4px 16px rgba(26,92,245,0.35);letter-spacing:-0.01em;">
            Reset My Password
        </a>
    </div>

    <!-- Expiry Notice -->
    <div style="background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;
                padding:14px 18px;margin:24px 0;display:flex;align-items:flex-start;gap:10px;">
        <span style="font-size:18px;">⏰</span>
        <p style="margin:0;color:#92400e;font-size:14px;line-height:1.6;">
            This link will expire in <strong>{expires_min} minutes</strong>.
            After that you will need to request a new reset link.
        </p>
    </div>

    <!-- Fallback URL -->
    <p style="margin:24px 0 8px;color:#8b91a0;font-size:13px;line-height:1.6;">
        If the button above doesn't work, copy and paste this link into your browser:
    </p>
    <div style="background:#f5f6f8;border:1px solid #e5e7ec;border-radius:8px;
                padding:12px 16px;word-break:break-all;">
        <a href="{reset_url}"
           style="color:#1a5cf5;font-size:13px;text-decoration:none;">{reset_url}</a>
    </div>

    <p style="margin:24px 0 0;color:#8b91a0;font-size:13px;line-height:1.6;">
        If you didn't request a password reset, you can safely ignore this email —
        your password will not be changed.
    </p>
''' + _email_footer()

    # Plain-text fallback
    text_body = f"""Hi {user.first_name},

We received a request to reset the password for your {COMPANY_NAME} account.

Reset your password by visiting:
{reset_url}

This link expires in {expires_min} minutes.

If you did not request a password reset, ignore this email.

— {COMPANY_NAME} Team
"""

    try:
        msg = Message(
            subject=f'Reset your {COMPANY_NAME} password',
            recipients=[user.email],
            body=text_body,
            html=html_body,
        )
        mail.send(msg)
        print(f"[Mail] Reset email sent to {user.email}")
        return True
    except Exception as exc:
        print(f"[Mail] Failed to send to {user.email}: {exc}")
        return False


def send_welcome_email(user):
    """Send a welcome email after successful registration."""
    html_body = _email_base(
        title=f'Welcome to {COMPANY_NAME}!',
        preview_text=f'Your account has been created successfully.'
    ) + f'''
    <p style="margin:0 0 16px;color:#5a6070;font-size:16px;line-height:1.7;">
        Hi <strong style="color:#1a1d23;">{user.first_name} {user.last_name}</strong>,
    </p>
    <p style="margin:0 0 24px;color:#5a6070;font-size:15px;line-height:1.7;">
        Welcome to <strong>{COMPANY_NAME}</strong>!
        Your account has been created successfully.
        You can now log in and start managing your authorized partner catalog.
    </p>

    <!-- Account Details -->
    <div style="background:#f5f6f8;border:1px solid #e5e7ec;border-radius:10px;
                padding:20px 24px;margin:24px 0;">
        <h3 style="margin:0 0 14px;color:#1a1d23;font-size:15px;font-weight:700;">
            Your Account Details
        </h3>
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td style="padding:6px 0;color:#8b91a0;font-size:14px;width:40%;">Username</td>
                <td style="padding:6px 0;color:#1a1d23;font-size:14px;font-weight:600;">
                    {user.username}
                </td>
            </tr>
            <tr>
                <td style="padding:6px 0;color:#8b91a0;font-size:14px;">Email</td>
                <td style="padding:6px 0;color:#1a1d23;font-size:14px;font-weight:600;">
                    {user.email}
                </td>
            </tr>
        </table>
    </div>

    <!-- Login Button -->
    <div style="text-align:center;margin:28px 0;">
        <a href="{FRONTEND_URL}"
           style="display:inline-block;background:linear-gradient(135deg,#1a5cf5,#1448e1);
                  color:white;text-decoration:none;font-size:15px;font-weight:700;
                  padding:14px 36px;border-radius:10px;
                  box-shadow:0 4px 16px rgba(26,92,245,0.3);">
            Go to Login
        </a>
    </div>
''' + _email_footer()

    text_body = f"""Hi {user.first_name},

Welcome to {COMPANY_NAME}!
Your account has been created successfully.

Username: {user.username}
Email:    {user.email}

Login at: {FRONTEND_URL}

— {COMPANY_NAME} Team
"""

    try:
        msg = Message(
            subject=f'Welcome to {COMPANY_NAME}!',
            recipients=[user.email],
            body=text_body,
            html=html_body,
        )
        mail.send(msg)
        print(f"[Mail] Welcome email sent to {user.email}")
    except Exception as exc:
        print(f"[Mail] Welcome email failed: {exc}")


# ════════════════════════════════════════════════
#  SEED
# ════════════════════════════════════════════════

def _seed_users():
    if not DB_AVAILABLE:
        return
    try:
        with app.app_context():
            if User.query.count() == 0:
                users = [
                    User(id=str(uuid.uuid4()), username='admin',
                         email='admin@authorizedpartners.com',
                         password_hash=bcrypt.generate_password_hash('Admin@123').decode(),
                         first_name='System', last_name='Administrator',
                         role='admin', is_active=True),
                    User(id=str(uuid.uuid4()), username='demo',
                         email='demo@authorizedpartners.com',
                         password_hash=bcrypt.generate_password_hash('Demo@123').decode(),
                         first_name='Demo', last_name='User',
                         role='user', is_active=True),
                ]
                db.session.add_all(users)
                db.session.commit()
                print("[Seed] admin/Admin@123 | demo/Demo@123")
    except Exception as exc:
        print(f"[Seed] {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass


_seed_users()


# ════════════════════════════════════════════════
#  SERVE FRONTEND
# ════════════════════════════════════════════════

@app.route('/')
def serve_index():
    p = os.path.join(FRONTEND_DIR, 'index.html')
    return send_file(p) if os.path.exists(p) else jsonify({'message': 'API running'}), 200

@app.route('/dashboard')
def serve_dashboard():
    p = os.path.join(FRONTEND_DIR, 'dashboard.html')
    return send_file(p) if os.path.exists(p) else ('Not found', 404)

@app.route('/forgot-password')
def serve_forgot():
    p = os.path.join(FRONTEND_DIR, 'forgot_password.html')
    return send_file(p) if os.path.exists(p) else ('Not found', 404)

@app.route('/css/<path:fn>')
def serve_css(fn):
    d = os.path.join(FRONTEND_DIR, 'css')
    f = os.path.join(d, fn)
    return send_from_directory(d, fn) if os.path.exists(f) else ('', 404)

@app.route('/js/<path:fn>')
def serve_js(fn):
    d = os.path.join(FRONTEND_DIR, 'js')
    f = os.path.join(d, fn)
    return send_from_directory(d, fn) if os.path.exists(f) else ('', 404)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/<path:path>')
def catch_all(path):
    fp = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(fp):
        return send_file(fp)
    idx = os.path.join(FRONTEND_DIR, 'index.html')
    return send_file(idx) if os.path.exists(idx) else ('Not found', 404)


# ════════════════════════════════════════════════
#  HEALTH
# ════════════════════════════════════════════════

@app.route('/api/health')
def health():
    mail_cfg = bool(app.config.get('MAIL_USERNAME'))
    return jsonify({
        'status': 'ok',
        'db': DB_AVAILABLE,
        'mail_configured': mail_cfg,
        'frontend_exists': os.path.isdir(FRONTEND_DIR),
        'ts': datetime.utcnow().isoformat(),
    })


# ════════════════════════════════════════════════
#  AUTH — REGISTER
# ════════════════════════════════════════════════

@app.route('/api/auth/register', methods=['POST'])
def register():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.get_json(silent=True) or {}

    required = ['username', 'email', 'password', 'first_name', 'last_name']
    for field in required:
        if not str(data.get(field, '')).strip():
            return jsonify({'error': f'"{field}" is required'}), 400

    username   = data['username'].lower().strip()
    email      = data['email'].lower().strip()
    password   = data['password']
    first_name = data['first_name'].strip()
    last_name  = data['last_name'].strip()

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    try:
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409

        user = User(
            id=str(uuid.uuid4()),
            username=username, email=email,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
            first_name=first_name, last_name=last_name,
            role='user', is_active=True,
            machine_id=data.get('machine_id') or _gen_machine_id(),
        )
        db.session.add(user)
        db.session.commit()

        # Send welcome email (non-blocking)
        try:
            send_welcome_email(user)
        except Exception:
            pass

        print(f"[Register] {username} / {email}")
        return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201

    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        # Re-check duplicates
        try:
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already taken'}), 409
            if User.query.filter_by(email=email).first():
                return jsonify({'error': 'Email already registered'}), 409
        except Exception:
            pass
        return jsonify({'error': f'Registration failed: {exc}'}), 500


# ════════════════════════════════════════════════
#  AUTH — LOGIN
# ════════════════════════════════════════════════

@app.route('/api/auth/login', methods=['POST'])
def login():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503

    data       = request.get_json(silent=True) or {}
    username   = str(data.get('username', '')).lower().strip()
    password   = str(data.get('password', ''))
    machine_id = str(data.get('machine_id', ''))

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    try:
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        if not user.is_active:
            return jsonify({'error': 'Account deactivated. Contact admin.'}), 403
        if not bcrypt.check_password_hash(user.password_hash, password):
            _log_login(user.id, machine_id, 'failed')
            return jsonify({'error': 'Invalid credentials'}), 401

        user.last_login = datetime.utcnow()
        if machine_id:
            user.machine_id = machine_id
        _log_login(user.id, machine_id, 'success')

        access_token = create_access_token(
            identity=user.id,
            additional_claims={'username': user.username, 'role': user.role},
            expires_delta=timedelta(hours=8),
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30),
        )
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
        }), 200

    except Exception as exc:
        print(f"[Login] {exc}")
        return jsonify({'error': str(exc)}), 500


def _log_login(user_id, machine_id, status):
    try:
        entry = LoginHistory(
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            machine_id=machine_id, status=status,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


# ════════════════════════════════════════════════
#  AUTH — FORGOT PASSWORD  (sends real email)
# ════════════════════════════════════════════════

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503

    data  = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).lower().strip()

    if not email:
        return jsonify({'error': 'Email address is required'}), 400
    if '@' not in email:
        return jsonify({'error': 'Enter a valid email address'}), 400

    # Always return the same message to prevent email enumeration
    generic = {
        'message': (
            'If an account exists for that email address, '
            'a password reset link has been sent. '
            'Please check your inbox (and spam/junk folder).'
        )
    }

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify(generic), 200

        if not user.is_active:
            return jsonify(generic), 200

        # Generate token
        raw_token  = secrets.token_urlsafe(48)
        token_hash = bcrypt.generate_password_hash(raw_token).decode('utf-8')
        user.reset_token        = token_hash
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        # Send email
        email_sent = send_password_reset_email(user, raw_token)

        if not email_sent:
            # Mail not configured — return token for dev/demo mode
            mail_configured = bool(app.config.get('MAIL_USERNAME'))
            if not mail_configured:
                return jsonify({
                    'message': 'Email service not configured. Use the token below (development mode).',
                    'dev_token': raw_token,
                    'dev_mode': True,
                }), 200

        return jsonify(generic), 200

    except Exception as exc:
        print(f"[ForgotPwd] {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': 'An error occurred. Please try again.'}), 500


# ════════════════════════════════════════════════
#  AUTH — RESET PASSWORD
# ════════════════════════════════════════════════

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503

    data     = request.get_json(silent=True) or {}
    email    = str(data.get('email', '')).lower().strip()
    token    = str(data.get('reset_token', ''))
    new_pw   = str(data.get('new_password', ''))
    confirm  = str(data.get('confirm_password', ''))

    if not all([email, token, new_pw]):
        return jsonify({'error': 'All fields are required'}), 400
    if len(new_pw) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if confirm and new_pw != confirm:
        return jsonify({'error': 'Passwords do not match'}), 400

    try:
        user = User.query.filter_by(email=email).first()
        if not user or not user.reset_token:
            return jsonify({'error': 'Invalid or expired reset link. Please request a new one.'}), 400

        if user.reset_token_expiry < datetime.utcnow():
            user.reset_token        = None
            user.reset_token_expiry = None
            db.session.commit()
            return jsonify({'error': 'Reset link has expired. Please request a new one.'}), 400

        if not bcrypt.check_password_hash(user.reset_token, token):
            return jsonify({'error': 'Invalid reset link. Please request a new one.'}), 400

        user.password_hash      = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        user.reset_token        = None
        user.reset_token_expiry = None
        db.session.commit()
        print(f"[ResetPwd] Password reset for {email}")
        return jsonify({'message': 'Password reset successfully. You can now sign in.'}), 200

    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': str(exc)}), 500


# ════════════════════════════════════════════════
#  AUTH — PROFILE / CHANGE PASSWORD
# ════════════════════════════════════════════════

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503
    user = User.query.get(get_jwt_identity())
    return (jsonify({'user': user.to_dict()}) if user
            else (jsonify({'error': 'User not found'}), 404))


@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503
    data = request.get_json(silent=True) or {}
    try:
        user = User.query.get(get_jwt_identity())
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not bcrypt.check_password_hash(user.password_hash,
                                          data.get('current_password', '')):
            return jsonify({'error': 'Current password is incorrect'}), 401
        new_pw = data.get('new_password', '')
        if len(new_pw) < 8:
            return jsonify({'error': 'Min 8 characters required'}), 400
        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': str(exc)}), 500


# ════════════════════════════════════════════════
#  PRODUCTS
# ════════════════════════════════════════════════

@app.route('/api/products/makes', methods=['GET'])
@jwt_required()
def get_makes():
    try:
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'makes': [],
                            'total_items': 0, 'total_makes': 0}), 200
        items  = data['Sheet1']
        bucket = {}
        for item in items:
            m = item['Make']
            if m not in bucket:
                bucket[m] = {'name': m, 'count': 0, 'total_value': 0.0}
            bucket[m]['count'] += 1
            bucket[m]['total_value'] += (
                _safe_num(item['Net Price']) * _safe_num(item['Quantity'], 1)
            )
        for v in bucket.values():
            v['total_value'] = round(v['total_value'], 2)
        makes = sorted(bucket.values(), key=lambda x: x['name'].lower())
        return jsonify({'makes': makes, 'total_items': len(items),
                        'total_makes': len(makes)}), 200
    except Exception as exc:
        return jsonify({'error': str(exc), 'makes': [],
                        'total_items': 0, 'total_makes': 0}), 500


@app.route('/api/products/by-make/<path:make_name>', methods=['GET'])
@jwt_required()
def get_by_make(make_name):
    try:
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'products': [], 'count': 0}), 200
        filtered = [i for i in data['Sheet1']
                    if i['Make'].lower() == make_name.strip().lower()]
        total = sum(_safe_num(i['Net Price']) * _safe_num(i['Quantity'], 1)
                    for i in filtered)
        return jsonify({'make': make_name, 'products': filtered,
                        'count': len(filtered), 'total_value': round(total, 2)}), 200
    except Exception as exc:
        return jsonify({'error': str(exc), 'products': [], 'count': 0}), 500


@app.route('/api/products/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        q      = request.args.get('q', '').lower().strip()
        make_f = request.args.get('make', '').lower().strip()
        limit  = min(int(request.args.get('limit', 500)), 2000)
        data   = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'results': [], 'count': 0}), 200
        results = []
        for item in data['Sheet1']:
            if make_f and item['Make'].lower() != make_f:
                continue
            if q:
                blob = ' '.join(str(v or '') for v in item.values()).lower()
                if q not in blob:
                    continue
            results.append(item)
            if len(results) >= limit:
                break
        return jsonify({'results': results, 'count': len(results),
                        'query': q, 'truncated': len(results) >= limit}), 200
    except Exception as exc:
        return jsonify({'error': str(exc), 'results': [], 'count': 0}), 500


@app.route('/api/products/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'total_items': 0,
                            'total_makes': 0, 'total_value': 0, 'makes': []}), 200
        items = data['Sheet1']
        makes = sorted({i['Make'] for i in items})
        total = sum(_safe_num(i['Net Price']) * _safe_num(i['Quantity'], 1)
                    for i in items)
        return jsonify({'total_items': len(items), 'total_makes': len(makes),
                        'total_value': round(total, 2), 'makes': makes}), 200
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/products/update', methods=['POST'])
@jwt_required()
def update_products():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503
    user = User.query.get(get_jwt_identity())
    if not user or user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json(force=True)
        ok, msg = save_products(data)
        return jsonify({'message': msg}) if ok else (jsonify({'error': msg}), 500)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/cache/clear', methods=['DELETE'])
@jwt_required()
def clear_cache():
    if not DB_AVAILABLE:
        return jsonify({'message': 'Cache cleared'}), 200
    try:
        uid = get_jwt_identity()
        ProductCache.query.filter_by(
            user_id=uid, is_deleted=False
        ).update({'is_deleted': True})
        db.session.commit()
        return jsonify({'message': 'Cache cleared'}), 200
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': str(exc)}), 500


# ════════════════════════════════════════════════
#  ERROR HANDLERS
# ════════════════════════════════════════════════

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(e):
    idx = os.path.join(FRONTEND_DIR, 'index.html')
    return send_file(idx) if os.path.exists(idx) else jsonify({'error': 'Not found'}), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large (max 50 MB)'}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

@jwt.expired_token_loader
def expired(h, p):
    return jsonify({'error': 'Token expired', 'code': 'TOKEN_EXPIRED'}), 401

@jwt.invalid_token_loader
def invalid(e):
    return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401

@jwt.unauthorized_loader
def missing(e):
    return jsonify({'error': 'Auth required', 'code': 'MISSING_TOKEN'}), 401


# ════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    print(f"[App] Starting on :{port}  debug={debug}")
    app.run(debug=debug, host='0.0.0.0', port=port)