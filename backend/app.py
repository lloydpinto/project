import os
import sys
import tempfile

# ── Make sure the backend folder is always on the Python path ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ── Determine writable DB path BEFORE importing Flask extensions ──
def _resolve_db_uri():
    """Return a SQLite URI using the first writable location."""
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
            print(f"[DB] Using path: {path}")
            return f'sqlite:///{path}'
        except Exception as exc:
            print(f"[DB] Skipping {path}: {exc}")

    fallback = os.path.join(tempfile.gettempdir(), 'authorized_partners.db')
    print(f"[DB] Fallback: {fallback}")
    return f'sqlite:///{fallback}'


DB_URI = _resolve_db_uri()

# ── Imports ──
from flask import (Flask, request, jsonify, send_from_directory,
                   send_file)
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                jwt_required, get_jwt_identity,
                                create_refresh_token)
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import json
import uuid
import secrets
import hashlib
import platform as _platform

# ── Paths ──
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
if not os.path.isdir(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

print(f"[App] BASE_DIR     : {BASE_DIR}")
print(f"[App] FRONTEND_DIR : {FRONTEND_DIR}  (exists={os.path.isdir(FRONTEND_DIR)})")
print(f"[App] DATA_DIR     : {DATA_DIR}")
print(f"[App] DB_URI       : {DB_URI}")

# ── Flask App ──
app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=''
)

# ── Config ──
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-change-in-production-min-32-chars')
app.config['JWT_SECRET_KEY'] = os.environ.get(
    'JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production-min-32-chars')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': (
        {'check_same_thread': False} if DB_URI.startswith('sqlite') else {}
    ),
}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['PRODUCTS_JSON_PATH'] = os.path.join(DATA_DIR, 'products.json')

# ── Extensions ──
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# ── Database ──
DB_AVAILABLE = False
try:
    from database import db, init_db
    from models import User, LoginHistory, ProductCache
    init_db(app)
    DB_AVAILABLE = True
    print("[DB] Initialized successfully")
except Exception as _db_err:
    print(f"[DB] Init error: {_db_err}")


# ═══════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════

def _safe_num(val, default=0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _generate_machine_id():
    try:
        raw = f"{_platform.node()}-{_platform.system()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return str(uuid.uuid4())[:32]


def _products_path():
    return app.config.get('PRODUCTS_JSON_PATH',
                          os.path.join(DATA_DIR, 'products.json'))


def _ensure_products_file():
    path = _products_path()
    if not os.path.exists(path):
        default = {
            "Sheet1": [
                {
                    "Sl.No": 1,
                    "Make": "Sample Brand",
                    "Model": "SB-001",
                    "Description": "Sample product — replace with your data",
                    "Quantity": 1,
                    "Net Price": 1000.0
                }
            ]
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(default, fh, indent=2)
        print(f"[Products] Created default file at {path}")


def load_products():
    _ensure_products_file()
    path = _products_path()
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            raw = fh.read().strip()
        if not raw:
            return {"Sheet1": []}
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {"Sheet1": []}
        if 'Sheet1' not in data:
            for k, v in data.items():
                if isinstance(v, list):
                    data = {'Sheet1': v}
                    break
            else:
                data = {'Sheet1': []}
        if not isinstance(data['Sheet1'], list):
            data['Sheet1'] = []

        clean = []
        for row in data['Sheet1']:
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
    except json.JSONDecodeError as exc:
        return {"Sheet1": [], "error": f"JSON error: {exc}"}
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


# ── Seed default users ──
def _seed_users():
    if not DB_AVAILABLE:
        return
    try:
        with app.app_context():
            if User.query.count() == 0:
                users = [
                    User(
                        id=str(uuid.uuid4()),
                        username='admin',
                        email='admin@authorizedpartners.com',
                        password_hash=bcrypt.generate_password_hash(
                            'Admin@123').decode('utf-8'),
                        first_name='System', last_name='Administrator',
                        role='admin', is_active=True,
                    ),
                    User(
                        id=str(uuid.uuid4()),
                        username='demo',
                        email='demo@authorizedpartners.com',
                        password_hash=bcrypt.generate_password_hash(
                            'Demo@123').decode('utf-8'),
                        first_name='Demo', last_name='User',
                        role='user', is_active=True,
                    ),
                ]
                db.session.add_all(users)
                db.session.commit()
                print("[Seed] Default users created  admin/Admin@123  demo/Demo@123")
    except Exception as exc:
        print(f"[Seed] Error: {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass


_seed_users()

# ═══════════════════════════════════════════════
#  SERVE FRONTEND
# ═══════════════════════════════════════════════

@app.route('/')
def serve_index():
    p = os.path.join(FRONTEND_DIR, 'index.html')
    return send_file(p) if os.path.exists(p) else (
        jsonify({'message': 'API running', 'frontend': 'not found'}), 200)


@app.route('/dashboard')
def serve_dashboard():
    p = os.path.join(FRONTEND_DIR, 'dashboard.html')
    return send_file(p) if os.path.exists(p) else ('dashboard not found', 404)


@app.route('/forgot-password')
def serve_forgot():
    p = os.path.join(FRONTEND_DIR, 'forgot_password.html')
    return send_file(p) if os.path.exists(p) else ('forgot_password not found', 404)


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


# ═══════════════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════════════

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'ok',
        'db_available': DB_AVAILABLE,
        'db_uri': DB_URI.split('///')[0] + '///***',   # hide path
        'frontend_exists': os.path.isdir(FRONTEND_DIR),
        'products_file': os.path.exists(_products_path()),
        'ts': datetime.utcnow().isoformat(),
    })


# ═══════════════════════════════════════════════
#  AUTH  ─  REGISTER
# ═══════════════════════════════════════════════

@app.route('/api/auth/register', methods=['POST'])
def register():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable. Try again later.'}), 503

    data = request.get_json(silent=True) or {}

    # Validate required fields
    required = ['username', 'email', 'password', 'first_name', 'last_name']
    for field in required:
        if not str(data.get(field, '')).strip():
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
    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    try:
        # Check duplicates
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
            first_name=first_name,
            last_name=last_name,
            role='user',
            is_active=True,
            machine_id=data.get('machine_id') or _generate_machine_id(),
        )
        db.session.add(user)
        db.session.commit()
        print(f"[Register] New user: {username}")
        return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201

    except Exception as exc:
        print(f"[Register] Error: {exc}")
        try:
            db.session.rollback()
        except Exception:
            pass
        # Re-check if it's really a duplicate (race condition)
        try:
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already taken'}), 409
            if User.query.filter_by(email=email).first():
                return jsonify({'error': 'Email already registered'}), 409
        except Exception:
            pass
        return jsonify({'error': f'Registration failed: {str(exc)}'}), 500


# ═══════════════════════════════════════════════
#  AUTH  ─  LOGIN
# ═══════════════════════════════════════════════

@app.route('/api/auth/login', methods=['POST'])
def login():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable. Try again later.'}), 503

    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).lower().strip()
    password = str(data.get('password', ''))
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
            additional_claims={
                'username': user.username,
                'role': user.role,
            },
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
        print(f"[Login] Error: {exc}")
        return jsonify({'error': str(exc)}), 500


def _log_login(user_id, machine_id, status):
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


# ═══════════════════════════════════════════════
#  AUTH  ─  FORGOT / RESET PASSWORD
# ═══════════════════════════════════════════════

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).lower().strip()
    if not email:
        return jsonify({'error': 'Email required'}), 400
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'If that account exists, a token was generated.'}), 200
        token = secrets.token_urlsafe(32)
        user.reset_token = bcrypt.generate_password_hash(token).decode('utf-8')
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return jsonify({
            'message': 'Token generated.',
            'reset_token': token,
            'note': 'In production, send via email.',
            'expires_in': '1 hour',
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).lower().strip()
    token = str(data.get('reset_token', ''))
    new_pw = str(data.get('new_password', ''))
    if not all([email, token, new_pw]):
        return jsonify({'error': 'All fields required'}), 400
    if len(new_pw) < 8:
        return jsonify({'error': 'Min 8 characters'}), 400
    try:
        user = User.query.filter_by(email=email).first()
        if not user or not user.reset_token:
            return jsonify({'error': 'Invalid request'}), 400
        if user.reset_token_expiry < datetime.utcnow():
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            return jsonify({'error': 'Token expired'}), 400
        if not bcrypt.check_password_hash(user.reset_token, token):
            return jsonify({'error': 'Invalid token'}), 400
        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return jsonify({'message': 'Password reset successfully.'}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500


# ═══════════════════════════════════════════════
#  AUTH  ─  PROFILE / CHANGE PASSWORD
# ═══════════════════════════════════════════════

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database unavailable'}), 503
    user = User.query.get(get_jwt_identity())
    return (jsonify({'user': user.to_dict()}) if user
            else jsonify({'error': 'User not found'}), 404)


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
            return jsonify({'error': 'Current password incorrect'}), 401
        new_pw = data.get('new_password', '')
        if len(new_pw) < 8:
            return jsonify({'error': 'Min 8 characters'}), 400
        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        db.session.commit()
        return jsonify({'message': 'Password changed'}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500


# ═══════════════════════════════════════════════
#  PRODUCTS
# ═══════════════════════════════════════════════

@app.route('/api/products/makes', methods=['GET'])
@jwt_required()
def get_makes():
    try:
        data = load_products()
        if data.get('error'):
            return jsonify({'error': data['error'], 'makes': [],
                            'total_items': 0, 'total_makes': 0}), 200
        items = data['Sheet1']
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
                        'count': len(filtered),
                        'total_value': round(total, 2)}), 200
    except Exception as exc:
        return jsonify({'error': str(exc), 'products': [], 'count': 0}), 500


@app.route('/api/products/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        q = request.args.get('q', '').lower().strip()
        make_f = request.args.get('make', '').lower().strip()
        limit = min(int(request.args.get('limit', 500)), 2000)
        data = load_products()
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
        return jsonify({'message': msg}) if ok else jsonify({'error': msg}), 500
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/cache/clear', methods=['DELETE'])
@jwt_required()
def clear_cache():
    if not DB_AVAILABLE:
        return jsonify({'message': 'Cache cleared (no DB)'}), 200
    try:
        uid = get_jwt_identity()
        ProductCache.query.filter_by(
            user_id=uid, is_deleted=False
        ).update({'is_deleted': True})
        db.session.commit()
        return jsonify({'message': 'Cache cleared'}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500


# ═══════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════

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


# ═══════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    print(f"[App] Starting on port {port}  debug={debug}")
    app.run(debug=debug, host='0.0.0.0', port=port)