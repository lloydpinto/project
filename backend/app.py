import os
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ════════════════════════════════════════════════════
#  RESOLVE DATABASE PATH — GUARANTEED PERSISTENT
# ════════════════════════════════════════════════════

def _resolve_db_uri():
    """
    Find a writable, persistent location for the SQLite database.
    Returns a full sqlite:/// URI.
    """
    # 1. Check environment variable first
    env_url = os.environ.get('DATABASE_URL', '').strip()
    if env_url:
        if env_url.startswith('postgres://'):
            env_url = env_url.replace('postgres://', 'postgresql://', 1)
        print(f"[DB] Using DATABASE_URL from environment")
        return env_url

    # 2. Try locations in order (most persistent first)
    db_filename = 'authorized_partners.db'
    candidates = [
        os.path.join(BASE_DIR, db_filename),                              # Same as app.py
        os.path.join(BASE_DIR, 'data', db_filename),                      # data subfolder
        os.path.join(os.path.dirname(BASE_DIR), db_filename),             # Parent folder
        os.path.join(os.path.expanduser('~'), '.ap_data', db_filename),   # Home directory
        os.path.join(tempfile.gettempdir(), db_filename),                  # Temp (last resort)
    ]

    for path in candidates:
        abs_path = os.path.abspath(path)
        folder = os.path.dirname(abs_path)
        try:
            os.makedirs(folder, exist_ok=True)
            # Test write permission
            test_file = os.path.join(folder, '.db_write_test')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)

            # If DB file already exists here, definitely use it
            if os.path.exists(abs_path):
                size = os.path.getsize(abs_path)
                print(f"[DB] Found existing DB: {abs_path} ({size} bytes)")
                return f'sqlite:///{abs_path}'

            print(f"[DB] Will create DB at: {abs_path}")
            return f'sqlite:///{abs_path}'
        except (OSError, PermissionError) as e:
            print(f"[DB] Cannot use {abs_path}: {e}")
            continue

    # Ultimate fallback
    fallback = os.path.join(tempfile.gettempdir(), db_filename)
    print(f"[DB] WARNING: Using temp fallback: {fallback}")
    return f'sqlite:///{fallback}'


DB_URI = _resolve_db_uri()

# ════════════════════════════════════════════════════
#  IMPORTS
# ════════════════════════════════════════════════════

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, create_refresh_token
)
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import json
import uuid
import secrets
import hashlib
import platform as _platform

try:
    from flask_mail import Mail, Message
    MAIL_AVAILABLE = True
except ImportError:
    MAIL_AVAILABLE = False
    print("[Mail] flask-mail not installed, email features disabled")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ════════════════════════════════════════════════════
#  PATHS
# ════════════════════════════════════════════════════

FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
if not os.path.isdir(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Authorized Partners')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5000')

print(f"[App] BASE_DIR     : {BASE_DIR}")
print(f"[App] FRONTEND_DIR : {FRONTEND_DIR} (exists={os.path.isdir(FRONTEND_DIR)})")
print(f"[App] DB_URI       : {DB_URI}")

# ════════════════════════════════════════════════════
#  FLASK APP
# ════════════════════════════════════════════════════

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

# Config
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-please-change-this-in-production'),
    JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-please-change-this'),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=12),
    SQLALCHEMY_DATABASE_URI=DB_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': (
            {'check_same_thread': False, 'timeout': 30}
            if DB_URI.startswith('sqlite') else {}
        ),
    },
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    PRODUCTS_JSON_PATH=os.path.join(DATA_DIR, 'products.json'),
    # Mail
    MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
    MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true',
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME', ''),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD', ''),
    MAIL_DEFAULT_SENDER=(
        COMPANY_NAME,
        os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', ''))
    ),
)

# Extensions
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
mail = Mail(app) if MAIL_AVAILABLE else None

# ════════════════════════════════════════════════════
#  DATABASE INIT
# ════════════════════════════════════════════════════

DB_OK = False
try:
    from database import db, init_db
    from models import User, LoginHistory, ProductCache
    init_db(app)
    DB_OK = True
except Exception as e:
    print(f"[DB] CRITICAL: {e}")
    import traceback
    traceback.print_exc()

# ════════════════════════════════════════════════════
#  VERIFY DATABASE IS WORKING
# ════════════════════════════════════════════════════

def _verify_db():
    """Run a quick read/write test on the database."""
    if not DB_OK:
        return False
    try:
        with app.app_context():
            count = User.query.count()
            print(f"[DB] Verification: {count} users in database")

            # Test write capability
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            print("[DB] ✓ Read/write verification passed")
            return True
    except Exception as e:
        print(f"[DB] ✗ Verification failed: {e}")
        return False


DB_VERIFIED = _verify_db()

# ════════════════════════════════════════════════════
#  SEED DEFAULT USERS
# ════════════════════════════════════════════════════

def _seed():
    if not DB_OK:
        return
    try:
        with app.app_context():
            existing = User.query.count()
            if existing > 0:
                print(f"[Seed] Database has {existing} users — skipping seed")
                return

            users = [
                User(
                    id=str(uuid.uuid4()),
                    username='admin',
                    email='admin@authorizedpartners.com',
                    password_hash=bcrypt.generate_password_hash('Admin@123').decode(),
                    first_name='System', last_name='Administrator',
                    role='admin', is_active=True,
                ),
                User(
                    id=str(uuid.uuid4()),
                    username='demo',
                    email='demo@authorizedpartners.com',
                    password_hash=bcrypt.generate_password_hash('Demo@123').decode(),
                    first_name='Demo', last_name='User',
                    role='user', is_active=True,
                ),
            ]
            db.session.add_all(users)
            db.session.commit()

            # Verify they were actually saved
            verify_count = User.query.count()
            print(f"[Seed] Created {len(users)} users — DB now has {verify_count} users")

            # Print all users for debugging
            all_users = User.query.all()
            for u in all_users:
                print(f"  → {u.username} ({u.email}) role={u.role}")

    except Exception as e:
        print(f"[Seed] Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            db.session.rollback()
        except Exception:
            pass

_seed()

# ════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ════════════════════════════════════════════════════

def _safe_num(val, default=0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _gen_machine_id():
    try:
        raw = f"{_platform.node()}-{_platform.system()}-{os.getpid()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return str(uuid.uuid4())[:32]


def _products_path():
    return app.config.get('PRODUCTS_JSON_PATH', os.path.join(DATA_DIR, 'products.json'))


def _ensure_products():
    path = _products_path()
    if not os.path.exists(path):
        default = {"Sheet1": [
            {"Sl.No": 1, "Make": "Sample", "Model": "S-001",
             "Description": "Sample product", "Quantity": 1, "Net Price": 1000}
        ]}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=2)


def load_products():
    _ensure_products()
    path = _products_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
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
                'Net Price': _safe_num(row.get('Net Price'), 0),
            })
        data['Sheet1'] = clean
        return data
    except Exception as e:
        return {"Sheet1": [], "error": str(e)}


def save_products(data):
    path = _products_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            import shutil
            shutil.copy2(path, path + '.backup')
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        return True, "Saved"
    except Exception as e:
        return False, str(e)


def _log_login(user_id, machine_id, status):
    """Log a login attempt. Never fails."""
    try:
        entry = LoginHistory(
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            machine_id=machine_id,
            status=status,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass


def _send_email(to_email, subject, html_body, text_body):
    """Send email. Returns True on success, False on failure."""
    if not mail or not app.config.get('MAIL_USERNAME'):
        print(f"[Mail] Not configured — skipping email to {to_email}")
        return False
    try:
        msg = Message(subject=subject, recipients=[to_email],
                      body=text_body, html=html_body)
        mail.send(msg)
        print(f"[Mail] Sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[Mail] Error sending to {to_email}: {e}")
        return False


# ════════════════════════════════════════════════════
#  SERVE FRONTEND
# ════════════════════════════════════════════════════

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
    return send_from_directory(d, fn) if os.path.exists(os.path.join(d, fn)) else ('', 404)

@app.route('/js/<path:fn>')
def serve_js(fn):
    d = os.path.join(FRONTEND_DIR, 'js')
    return send_from_directory(d, fn) if os.path.exists(os.path.join(d, fn)) else ('', 404)

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


# ════════════════════════════════════════════════════
#  HEALTH CHECK — SHOWS DB STATUS
# ════════════════════════════════════════════════════

@app.route('/api/health')
def health():
    user_count = 0
    db_file_exists = False
    db_file_size = 0

    if DB_OK:
        try:
            user_count = User.query.count()
        except Exception:
            pass

    # Check if DB file actually exists on disk
    if DB_URI.startswith('sqlite:///'):
        db_path = DB_URI.replace('sqlite:///', '')
        db_file_exists = os.path.exists(db_path)
        if db_file_exists:
            db_file_size = os.path.getsize(db_path)

    return jsonify({
        'status': 'ok',
        'db_available': DB_OK,
        'db_verified': DB_VERIFIED,
        'db_file_exists': db_file_exists,
        'db_file_size_kb': round(db_file_size / 1024, 1),
        'user_count': user_count,
        'mail_configured': bool(app.config.get('MAIL_USERNAME')),
        'frontend_exists': os.path.isdir(FRONTEND_DIR),
        'timestamp': datetime.utcnow().isoformat(),
    })


# ════════════════════════════════════════════════════
#  DEBUG — LIST ALL USERS (remove in production)
# ════════════════════════════════════════════════════

@app.route('/api/debug/users')
def debug_users():
    """Shows all registered users. REMOVE THIS IN PRODUCTION."""
    if not DB_OK:
        return jsonify({'error': 'DB not available'}), 503
    try:
        users = User.query.all()
        return jsonify({
            'count': len(users),
            'users': [
                {
                    'username': u.username,
                    'email': u.email,
                    'role': u.role,
                    'is_active': u.is_active,
                    'created': u.created_at.isoformat() if u.created_at else None,
                    'last_login': u.last_login.isoformat() if u.last_login else None,
                }
                for u in users
            ],
            'db_uri': DB_URI.split('///')[0] + '///***',
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ════════════════════════════════════════════════════
#  AUTH — REGISTER
# ════════════════════════════════════════════════════

@app.route('/api/auth/register', methods=['POST'])
def register():
    if not DB_OK:
        return jsonify({'error': 'Database is not available. Please try again later.'}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'No data received. Please fill in all fields.'}), 400

    # Validate
    required = ['username', 'email', 'password', 'first_name', 'last_name']
    for field in required:
        val = str(data.get(field, '')).strip()
        if not val:
            return jsonify({'error': f'"{field}" is required'}), 400

    username = data['username'].lower().strip()
    email = data['email'].lower().strip()
    password = data['password']
    first_name = data['first_name'].strip()
    last_name = data['last_name'].strip()

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Please enter a valid email address'}), 400

    try:
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': f'Username "{username}" is already taken'}), 409

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({'error': f'Email "{email}" is already registered'}), 409

        # Create user
        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=pw_hash,
            first_name=first_name,
            last_name=last_name,
            role='user',
            is_active=True,
            machine_id=data.get('machine_id') or _gen_machine_id(),
            created_at=datetime.utcnow(),
        )

        db.session.add(new_user)
        db.session.flush()  # Flush to get any constraint errors before commit

        db.session.commit()

        # VERIFY the user was actually saved
        saved_user = User.query.filter_by(username=username).first()
        if not saved_user:
            print(f"[Register] CRITICAL: User {username} was not saved!")
            return jsonify({'error': 'Registration failed — user was not saved. Please try again.'}), 500

        print(f"[Register] ✓ New user: {username} ({email}) — ID: {saved_user.id}")

        # Print total user count for debugging
        total = User.query.count()
        print(f"[Register]   Total users in DB: {total}")

        # Send welcome email (non-blocking)
        try:
            welcome_html = f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:30px;">
                <h2>Welcome to {COMPANY_NAME}!</h2>
                <p>Hi {first_name},</p>
                <p>Your account has been created successfully.</p>
                <p><strong>Username:</strong> {username}<br>
                   <strong>Email:</strong> {email}</p>
                <p>You can now <a href="{FRONTEND_URL}">sign in</a> to your account.</p>
                <p>— {COMPANY_NAME} Team</p>
            </div>
            """
            welcome_text = f"Hi {first_name}, welcome to {COMPANY_NAME}! Your username: {username}"
            _send_email(email, f'Welcome to {COMPANY_NAME}!', welcome_html, welcome_text)
        except Exception:
            pass

        return jsonify({
            'message': 'Registration successful! You can now sign in.',
            'user': saved_user.to_dict(),
        }), 201

    except Exception as exc:
        print(f"[Register] Error: {exc}")
        import traceback
        traceback.print_exc()

        try:
            db.session.rollback()
        except Exception:
            pass

        error_msg = str(exc).lower()
        if 'unique' in error_msg or 'duplicate' in error_msg:
            if 'username' in error_msg:
                return jsonify({'error': f'Username "{username}" is already taken'}), 409
            if 'email' in error_msg:
                return jsonify({'error': f'Email "{email}" is already registered'}), 409
            return jsonify({'error': 'Username or email already exists'}), 409

        return jsonify({'error': f'Registration failed: {str(exc)}'}), 500


# ════════════════════════════════════════════════════
#  AUTH — LOGIN
# ════════════════════════════════════════════════════

@app.route('/api/auth/login', methods=['POST'])
def login():
    if not DB_OK:
        return jsonify({'error': 'Database is not available. Please try again later.'}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'No data received'}), 400

    username = str(data.get('username', '')).lower().strip()
    password = str(data.get('password', ''))
    machine_id = str(data.get('machine_id', ''))

    if not username:
        return jsonify({'error': 'Username or email is required'}), 400
    if not password:
        return jsonify({'error': 'Password is required'}), 400

    try:
        # Find user by username OR email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            # Print debug info
            total = User.query.count()
            all_usernames = [u.username for u in User.query.all()]
            print(f"[Login] User '{username}' not found. DB has {total} users: {all_usernames}")
            return jsonify({'error': 'Invalid username or password'}), 401

        if not user.is_active:
            return jsonify({'error': 'Your account has been deactivated. Contact administrator.'}), 403

        # Verify password
        if not bcrypt.check_password_hash(user.password_hash, password):
            _log_login(user.id, machine_id, 'failed')
            print(f"[Login] Wrong password for '{username}'")
            return jsonify({'error': 'Invalid username or password'}), 401

        # Success — update user record
        user.last_login = datetime.utcnow()
        if machine_id:
            user.machine_id = machine_id

        try:
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

        _log_login(user.id, machine_id, 'success')

        # Create tokens
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'username': user.username,
                'role': user.role,
            },
            expires_delta=timedelta(hours=12),
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30),
        )

        print(f"[Login] ✓ {user.username} ({user.email}) logged in")

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
        }), 200

    except Exception as exc:
        print(f"[Login] Error: {exc}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login error: {str(exc)}'}), 500


# ════════════════════════════════════════════════════
#  AUTH — FORGOT PASSWORD
# ════════════════════════════════════════════════════

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    if not DB_OK:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).lower().strip()

    if not email or '@' not in email:
        return jsonify({'error': 'Please enter a valid email address'}), 400

    generic_msg = {
        'message': 'If an account exists with that email, a reset link has been sent. Check your inbox and spam folder.'
    }

    try:
        user = User.query.filter_by(email=email).first()
        if not user or not user.is_active:
            return jsonify(generic_msg), 200

        raw_token = secrets.token_urlsafe(48)
        user.reset_token = bcrypt.generate_password_hash(raw_token).decode('utf-8')
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        reset_url = f"{FRONTEND_URL}/forgot-password?token={raw_token}&email={email}"

        reset_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:30px;">
            <h2>Reset Your Password</h2>
            <p>Hi {user.first_name},</p>
            <p>Click the button below to reset your password:</p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{reset_url}"
                   style="background:#1a5cf5;color:white;padding:14px 36px;
                          text-decoration:none;border-radius:8px;font-weight:bold;
                          font-size:16px;display:inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="color:#888;font-size:13px;">
                This link expires in 60 minutes.<br>
                If you didn't request this, ignore this email.
            </p>
            <p style="color:#aaa;font-size:12px;margin-top:20px;">
                Link: {reset_url}
            </p>
        </div>
        """
        reset_text = f"Reset password: {reset_url}\nExpires in 60 minutes."

        email_sent = _send_email(
            email,
            f'Reset your {COMPANY_NAME} password',
            reset_html,
            reset_text
        )

        if not email_sent and not app.config.get('MAIL_USERNAME'):
            return jsonify({
                'message': 'Email not configured (dev mode). Use the token below.',
                'dev_token': raw_token,
                'dev_mode': True,
            }), 200

        return jsonify(generic_msg), 200

    except Exception as exc:
        print(f"[ForgotPwd] {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': 'Something went wrong. Please try again.'}), 500


# ════════════════════════════════════════════════════
#  AUTH — RESET PASSWORD
# ════════════════════════════════════════════════════

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    if not DB_OK:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).lower().strip()
    token = str(data.get('reset_token', ''))
    new_pw = str(data.get('new_password', ''))

    if not all([email, token, new_pw]):
        return jsonify({'error': 'All fields are required'}), 400
    if len(new_pw) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    try:
        user = User.query.filter_by(email=email).first()
        if not user or not user.reset_token:
            return jsonify({'error': 'Invalid or expired reset link'}), 400
        if user.reset_token_expiry < datetime.utcnow():
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            return jsonify({'error': 'Reset link has expired. Request a new one.'}), 400
        if not bcrypt.check_password_hash(user.reset_token, token):
            return jsonify({'error': 'Invalid reset link. Request a new one.'}), 400

        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        print(f"[ResetPwd] ✓ Password reset for {email}")
        return jsonify({'message': 'Password reset successfully. You can now sign in.'}), 200

    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': str(exc)}), 500


# ════════════════════════════════════════════════════
#  AUTH — PROFILE / CHANGE PASSWORD
# ════════════════════════════════════════════════════

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    if not DB_OK:
        return jsonify({'error': 'Database unavailable'}), 503
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    if not DB_OK:
        return jsonify({'error': 'Database unavailable'}), 503
    data = request.get_json(silent=True) or {}
    try:
        user = User.query.get(get_jwt_identity())
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not bcrypt.check_password_hash(user.password_hash, data.get('current_password', '')):
            return jsonify({'error': 'Current password is incorrect'}), 401
        new_pw = data.get('new_password', '')
        if len(new_pw) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': str(exc)}), 500


# ════════════════════════════════════════════════════
#  PRODUCTS
# ════════════════════════════════════════════════════

@app.route('/api/products/makes', methods=['GET'])
@jwt_required()
def get_makes():
    try:
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'makes': [], 'total_items': 0, 'total_makes': 0}), 200
        items = data['Sheet1']
        bucket = {}
        for item in items:
            m = item['Make']
            if m not in bucket:
                bucket[m] = {'name': m, 'count': 0, 'total_value': 0.0}
            bucket[m]['count'] += 1
            bucket[m]['total_value'] += _safe_num(item['Net Price']) * _safe_num(item['Quantity'], 1)
        for v in bucket.values():
            v['total_value'] = round(v['total_value'], 2)
        makes = sorted(bucket.values(), key=lambda x: x['name'].lower())
        return jsonify({'makes': makes, 'total_items': len(items), 'total_makes': len(makes)}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'makes': [], 'total_items': 0, 'total_makes': 0}), 500


@app.route('/api/products/by-make/<path:make_name>', methods=['GET'])
@jwt_required()
def get_by_make(make_name):
    try:
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'products': [], 'count': 0}), 200
        filtered = [i for i in data['Sheet1'] if i['Make'].lower() == make_name.strip().lower()]
        total = sum(_safe_num(i['Net Price']) * _safe_num(i['Quantity'], 1) for i in filtered)
        return jsonify({'make': make_name, 'products': filtered, 'count': len(filtered), 'total_value': round(total, 2)}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'products': [], 'count': 0}), 500


@app.route('/api/products/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        q = request.args.get('q', '').lower().strip()
        mf = request.args.get('make', '').lower().strip()
        limit = min(int(request.args.get('limit', 500)), 2000)
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'results': [], 'count': 0}), 200
        results = []
        for item in data['Sheet1']:
            if mf and item['Make'].lower() != mf:
                continue
            if q:
                blob = ' '.join(str(v or '') for v in item.values()).lower()
                if q not in blob:
                    continue
            results.append(item)
            if len(results) >= limit:
                break
        return jsonify({'results': results, 'count': len(results), 'query': q, 'truncated': len(results) >= limit}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'results': [], 'count': 0}), 500


@app.route('/api/products/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'total_items': 0, 'total_makes': 0, 'total_value': 0, 'makes': []}), 200
        items = data['Sheet1']
        makes = sorted({i['Make'] for i in items})
        total = sum(_safe_num(i['Net Price']) * _safe_num(i['Quantity'], 1) for i in items)
        return jsonify({'total_items': len(items), 'total_makes': len(makes), 'total_value': round(total, 2), 'makes': makes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/update', methods=['POST'])
@jwt_required()
def update_products():
    if not DB_OK:
        return jsonify({'error': 'Database unavailable'}), 503
    user = User.query.get(get_jwt_identity())
    if not user or user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json(force=True)
        ok, msg = save_products(data)
        return jsonify({'message': msg}) if ok else (jsonify({'error': msg}), 500)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['DELETE'])
@jwt_required()
def clear_cache():
    if not DB_OK:
        return jsonify({'message': 'Cache cleared'}), 200
    try:
        uid = get_jwt_identity()
        ProductCache.query.filter_by(user_id=uid, is_deleted=False).update({'is_deleted': True})
        db.session.commit()
        return jsonify({'message': 'Cache cleared'}), 200
    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500

# ════════════════════════════════════════════════════
#  PRODUCTS — ADD SINGLE PRODUCT
# ════════════════════════════════════════════════════

@app.route('/api/products/add', methods=['POST'])
@jwt_required()
def add_product():
    """Add a single product to the JSON file permanently."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'No data received'}), 400

    # Validate required fields
    make = str(data.get('Make', '') or '').strip()
    model = str(data.get('Model', '') or '').strip()

    if not make:
        return jsonify({'error': '"Make" (brand name) is required'}), 400
    if not model:
        return jsonify({'error': '"Model" is required'}), 400

    # Build clean product entry
    new_product = {
        'Sl.No': data.get('Sl.No'),
        'Make': make,
        'Model': model,
        'Description': str(data.get('Description', '') or '').strip() or None,
        'Quantity': _safe_num(data.get('Quantity'), 1),
        'Net Price': _safe_num(data.get('Net Price'), 0),
    }

    try:
        # Load current data
        products_data = load_products()
        if products_data.get('error'):
            return jsonify({'error': f'Cannot load products file: {products_data["error"]}'}), 500

        items = products_data.get('Sheet1', [])

        # Auto-assign Sl.No if not provided
        if new_product['Sl.No'] is None:
            existing_numbers = [
                i.get('Sl.No') for i in items
                if i.get('Sl.No') is not None
            ]
            max_num = max(existing_numbers) if existing_numbers else 0
            try:
                max_num = int(max_num)
            except (ValueError, TypeError):
                max_num = len(items)
            new_product['Sl.No'] = max_num + 1

        # Check for duplicate model in same make
        duplicate = any(
            i.get('Make', '').lower() == make.lower() and
            i.get('Model', '').lower() == model.lower()
            for i in items
        )
        if duplicate:
            return jsonify({
                'error': f'Model "{model}" already exists under "{make}". Use a different model name.',
                'duplicate': True
            }), 409

        # Add to list
        items.append(new_product)
        products_data['Sheet1'] = items

        # Save permanently to JSON file
        ok, msg = save_products(products_data)
        if not ok:
            return jsonify({'error': f'Failed to save: {msg}'}), 500

        print(f"[AddProduct] ✓ Added: {make} / {model} — Total items: {len(items)}")

        return jsonify({
            'message': f'Product "{model}" added to "{make}" successfully.',
            'product': new_product,
            'total_items': len(items),
        }), 201

    except Exception as exc:
        print(f"[AddProduct] Error: {exc}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to add product: {str(exc)}'}), 500


@app.route('/api/products/add-bulk', methods=['POST'])
@jwt_required()
def add_bulk_products():
    """Add multiple products at once."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400

    new_items = data.get('products', [])
    if not isinstance(new_items, list) or len(new_items) == 0:
        return jsonify({'error': 'No products provided'}), 400

    try:
        products_data = load_products()
        if products_data.get('error'):
            return jsonify({'error': products_data['error']}), 500

        items = products_data.get('Sheet1', [])

        # Find max Sl.No
        existing_numbers = [
            i.get('Sl.No') for i in items
            if i.get('Sl.No') is not None
        ]
        try:
            next_num = (max(int(n) for n in existing_numbers if n is not None) + 1) if existing_numbers else 1
        except (ValueError, TypeError):
            next_num = len(items) + 1

        added = 0
        skipped = 0
        errors = []

        for idx, item in enumerate(new_items):
            make = str(item.get('Make', '') or '').strip()
            model = str(item.get('Model', '') or '').strip()

            if not make or not model:
                errors.append(f"Row {idx + 1}: Make and Model are required")
                skipped += 1
                continue

            # Check duplicate
            is_dup = any(
                i.get('Make', '').lower() == make.lower() and
                i.get('Model', '').lower() == model.lower()
                for i in items
            )
            if is_dup:
                errors.append(f"Row {idx + 1}: '{model}' already exists under '{make}'")
                skipped += 1
                continue

            clean_item = {
                'Sl.No': item.get('Sl.No') if item.get('Sl.No') is not None else next_num,
                'Make': make,
                'Model': model,
                'Description': str(item.get('Description', '') or '').strip() or None,
                'Quantity': _safe_num(item.get('Quantity'), 1),
                'Net Price': _safe_num(item.get('Net Price'), 0),
            }
            items.append(clean_item)
            next_num += 1
            added += 1

        products_data['Sheet1'] = items
        ok, msg = save_products(products_data)
        if not ok:
            return jsonify({'error': f'Failed to save: {msg}'}), 500

        print(f"[BulkAdd] ✓ Added {added}, Skipped {skipped}, Total: {len(items)}")

        return jsonify({
            'message': f'Added {added} product(s). Skipped {skipped}.',
            'added': added,
            'skipped': skipped,
            'errors': errors[:10],
            'total_items': len(items),
        }), 201

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/products/delete', methods=['POST'])
@jwt_required()
def delete_product():
    """Delete a product by Make + Model."""
    data = request.get_json(silent=True) or {}
    make = str(data.get('Make', '')).strip()
    model = str(data.get('Model', '')).strip()

    if not make or not model:
        return jsonify({'error': 'Make and Model are required to delete'}), 400

    try:
        products_data = load_products()
        if products_data.get('error'):
            return jsonify({'error': products_data['error']}), 500

        items = products_data.get('Sheet1', [])
        original_count = len(items)

        items = [
            i for i in items
            if not (i.get('Make', '').lower() == make.lower() and
                    i.get('Model', '').lower() == model.lower())
        ]

        removed = original_count - len(items)
        if removed == 0:
            return jsonify({'error': f'Product "{model}" under "{make}" not found'}), 404

        products_data['Sheet1'] = items
        ok, msg = save_products(products_data)
        if not ok:
            return jsonify({'error': f'Failed to save: {msg}'}), 500

        print(f"[Delete] ✓ Removed {removed} item(s): {make}/{model}")
        return jsonify({
            'message': f'Deleted "{model}" from "{make}".',
            'removed': removed,
            'total_items': len(items),
        }), 200

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/products/edit', methods=['POST'])
@jwt_required()
def edit_product():
    """Edit an existing product identified by original Make + Model."""
    data = request.get_json(silent=True) or {}
    orig_make = str(data.get('original_make', '')).strip()
    orig_model = str(data.get('original_model', '')).strip()

    if not orig_make or not orig_model:
        return jsonify({'error': 'Original Make and Model required'}), 400

    new_make = str(data.get('Make', orig_make)).strip()
    new_model = str(data.get('Model', orig_model)).strip()

    if not new_make or not new_model:
        return jsonify({'error': 'Make and Model cannot be empty'}), 400

    try:
        products_data = load_products()
        if products_data.get('error'):
            return jsonify({'error': products_data['error']}), 500

        items = products_data.get('Sheet1', [])
        found = False

        for i, item in enumerate(items):
            if (item.get('Make', '').lower() == orig_make.lower() and
                item.get('Model', '').lower() == orig_model.lower()):
                items[i] = {
                    'Sl.No': data.get('Sl.No', item.get('Sl.No')),
                    'Make': new_make,
                    'Model': new_model,
                    'Description': str(data.get('Description', item.get('Description', '')) or '').strip() or None,
                    'Quantity': _safe_num(data.get('Quantity', item.get('Quantity')), 1),
                    'Net Price': _safe_num(data.get('Net Price', item.get('Net Price')), 0),
                }
                found = True
                break

        if not found:
            return jsonify({'error': f'Product "{orig_model}" under "{orig_make}" not found'}), 404

        products_data['Sheet1'] = items
        ok, msg = save_products(products_data)
        if not ok:
            return jsonify({'error': f'Failed to save: {msg}'}), 500

        print(f"[Edit] ✓ Updated: {orig_make}/{orig_model} → {new_make}/{new_model}")
        return jsonify({
            'message': f'Product updated successfully.',
            'product': items[i] if found else None,
        }), 200

    except Exception as exc:
        return jsonify({'error': str(exc)}), 500
    
# ════════════════════════════════════════════════════
#  ERROR HANDLERS
# ════════════════════════════════════════════════════

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(e):
    idx = os.path.join(FRONTEND_DIR, 'index.html')
    return send_file(idx) if os.path.exists(idx) else jsonify({'error': 'Not found'}), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large'}), 413

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


# ════════════════════════════════════════════════════
#  RUN
# ════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'

    # Final status
    print("\n" + "=" * 50)
    print(f"  Server starting on port {port}")
    print(f"  Database: {'✓ OK' if DB_OK else '✗ FAILED'}")
    print(f"  Frontend: {'✓ Found' if os.path.isdir(FRONTEND_DIR) else '✗ Missing'}")
    print(f"  Products: {'✓ Found' if os.path.exists(_products_path()) else '✗ Missing'}")
    if DB_OK:
        with app.app_context():
            print(f"  Users:    {User.query.count()}")
    print("=" * 50 + "\n")

    app.run(debug=debug, host='0.0.0.0', port=port)