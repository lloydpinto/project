import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

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
import platform as platform_module

# ===================== APP SETUP =====================

# Determine paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Fallback: if frontend is inside backend folder
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

print(f"BASE_DIR: {BASE_DIR}")
print(f"FRONTEND_DIR: {FRONTEND_DIR}")
print(f"Frontend exists: {os.path.exists(FRONTEND_DIR)}")

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=''
)

# ===================== CONFIGURATION =====================

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'dev-secret-key-change-in-production-min-32-chars'
)
app.config['JWT_SECRET_KEY'] = os.environ.get(
    'JWT_SECRET_KEY',
    'dev-jwt-secret-key-change-in-production-min-32-chars'
)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Database
db_url = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "authorized_partners.db")}')
# Fix for older Heroku postgres URLs
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

app.config['PRODUCTS_JSON_PATH'] = os.path.join(DATA_DIR, 'products.json')

# ===================== EXTENSIONS =====================

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Import models after app config
try:
    from database import db, init_db
    from models import User, LoginHistory, ProductCache
    init_db(app)
    DB_AVAILABLE = True
except Exception as e:
    print(f"DB init warning: {e}")
    DB_AVAILABLE = False

try:
    jwt = JWTManager(app)
except Exception as e:
    print(f"JWT init error: {e}")

try:
    bcrypt = Bcrypt(app)
except Exception as e:
    print(f"Bcrypt init error: {e}")

# ===================== UTILITY FUNCTIONS =====================

def generate_machine_id():
    try:
        info = f"{platform_module.node()}-{platform_module.system()}"
        return hashlib.sha256(info.encode()).hexdigest()[:32]
    except Exception:
        return str(uuid.uuid4())[:32]


def get_products_path():
    return app.config.get('PRODUCTS_JSON_PATH', os.path.join(DATA_DIR, 'products.json'))


def load_products_data():
    path = get_products_path()
    try:
        if not os.path.exists(path):
            print(f"Products file not found: {path}")
            _create_default_products(path)

        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read().strip()

        if not raw:
            return {"Sheet1": []}

        data = json.loads(raw)

        if not isinstance(data, dict):
            return {"Sheet1": []}

        # Normalize structure
        if 'Sheet1' not in data:
            for key, val in data.items():
                if isinstance(val, list):
                    data = {'Sheet1': val}
                    break
            else:
                data = {'Sheet1': []}

        if not isinstance(data['Sheet1'], list):
            data['Sheet1'] = []

        # Sanitize rows
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
                'Quantity': _safe_number(row.get('Quantity'), 1),
                'Net Price': _safe_number(row.get('Net Price'), 0.0)
            })

        data['Sheet1'] = clean
        return data

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return {"Sheet1": [], "error": f"JSON parse error: {str(e)}"}
    except Exception as e:
        print(f"Load products error: {e}")
        return {"Sheet1": [], "error": str(e)}


def _create_default_products(path):
    """Create a default products.json if it doesn't exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    default = {
        "Sheet1": [
            {
                "Sl.No": 1,
                "Make": "Sample Brand",
                "Model": "SB-001",
                "Description": "Sample product",
                "Quantity": 1,
                "Net Price": 1000.0
            }
        ]
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(default, f, indent=2)
    print(f"Created default products.json at {path}")


def save_products_data(data):
    path = get_products_path()
    backup = path + '.backup'
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            import shutil
            shutil.copy2(path, backup)

        if not isinstance(data, dict):
            return False, "Invalid structure"
        if 'Sheet1' not in data or not isinstance(data['Sheet1'], list):
            return False, "Missing Sheet1"

        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        return True, "Saved"
    except Exception as e:
        if os.path.exists(backup):
            import shutil
            shutil.copy2(backup, path)
        return False, str(e)


def _safe_number(val, default=0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def seed_default_users():
    if not DB_AVAILABLE:
        return
    try:
        with app.app_context():
            if User.query.count() == 0:
                admin = User(
                    id=str(uuid.uuid4()),
                    username='admin',
                    email='admin@authorizedpartners.com',
                    password_hash=bcrypt.generate_password_hash('Admin@123').decode('utf-8'),
                    first_name='System',
                    last_name='Administrator',
                    role='admin',
                    is_active=True
                )
                demo = User(
                    id=str(uuid.uuid4()),
                    username='demo',
                    email='demo@authorizedpartners.com',
                    password_hash=bcrypt.generate_password_hash('Demo@123').decode('utf-8'),
                    first_name='Demo',
                    last_name='User',
                    role='user',
                    is_active=True
                )
                db.session.add_all([admin, demo])
                db.session.commit()
                print("Default users seeded: admin/Admin@123 | demo/Demo@123")
    except Exception as e:
        print(f"Seed error: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass


# Seed on startup
seed_default_users()
os.makedirs(DATA_DIR, exist_ok=True)

# ===================== HEALTH CHECK =====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'frontend_path': FRONTEND_DIR,
        'frontend_exists': os.path.exists(FRONTEND_DIR),
        'db_available': DB_AVAILABLE
    }), 200

# ===================== SERVE FRONTEND =====================

@app.route('/')
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({
        'message': 'Authorized Partners API',
        'status': 'running',
        'frontend': 'not found - check deployment structure',
        'frontend_path': FRONTEND_DIR
    }), 200


@app.route('/dashboard')
def serve_dashboard():
    path = os.path.join(FRONTEND_DIR, 'dashboard.html')
    if os.path.exists(path):
        return send_file(path)
    return jsonify({'error': 'dashboard.html not found'}), 404


@app.route('/forgot-password')
def serve_forgot_password():
    path = os.path.join(FRONTEND_DIR, 'forgot_password.html')
    if os.path.exists(path):
        return send_file(path)
    return jsonify({'error': 'forgot_password.html not found'}), 404


@app.route('/css/<path:filename>')
def serve_css(filename):
    css_dir = os.path.join(FRONTEND_DIR, 'css')
    file_path = os.path.join(css_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(css_dir, filename)
    return jsonify({'error': f'CSS file {filename} not found'}), 404


@app.route('/js/<path:filename>')
def serve_js(filename):
    js_dir = os.path.join(FRONTEND_DIR, 'js')
    file_path = os.path.join(js_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(js_dir, filename)
    return jsonify({'error': f'JS file {filename} not found'}), 404


@app.route('/favicon.ico')
def favicon():
    return '', 204


# Catch-all for any other frontend routes
@app.route('/<path:path>')
def catch_all(path):
    # Try to serve the file directly
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)
    # Fall back to index.html for SPA routing
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({'error': f'Route /{path} not found'}), 404


# ===================== AUTH ENDPOINTS =====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        username = data['username'].lower().strip()
        email = data['email'].lower().strip()

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=bcrypt.generate_password_hash(data['password']).decode('utf-8'),
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            role='user',
            is_active=True,
            machine_id=data.get('machine_id', generate_machine_id())
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        username = data.get('username', '').lower().strip()
        password = data.get('password', '')
        machine_id = data.get('machine_id', '')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        if not user.is_active:
            return jsonify({'error': 'Account deactivated'}), 403
        if not bcrypt.check_password_hash(user.password_hash, password):
            try:
                log = LoginHistory(
                    user_id=user.id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:500],
                    machine_id=machine_id,
                    status='failed'
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                db.session.rollback()
            return jsonify({'error': 'Invalid credentials'}), 401

        user.last_login = datetime.utcnow()
        if machine_id:
            user.machine_id = machine_id

        try:
            log = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
                machine_id=machine_id,
                status='success'
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'username': user.username,
                'role': user.role,
                'machine_id': machine_id
            },
            expires_delta=timedelta(hours=8)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )

        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    try:
        data = request.get_json()
        email = (data or {}).get('email', '').lower().strip()
        if not email:
            return jsonify({'error': 'Email required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'If an account exists, a token was generated.'}), 200

        reset_token = secrets.token_urlsafe(32)
        user.reset_token = bcrypt.generate_password_hash(reset_token).decode('utf-8')
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        return jsonify({
            'message': 'Reset token generated.',
            'reset_token': reset_token,
            'note': 'In production, send this via email.',
            'expires_in': '1 hour'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    try:
        data = request.get_json() or {}
        email = data.get('email', '').lower().strip()
        reset_token = data.get('reset_token', '')
        new_password = data.get('new_password', '')

        if not all([email, reset_token, new_password]):
            return jsonify({'error': 'All fields required'}), 400
        if len(new_password) < 8:
            return jsonify({'error': 'Min 8 characters'}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.reset_token:
            return jsonify({'error': 'Invalid request'}), 400
        if user.reset_token_expiry < datetime.utcnow():
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            return jsonify({'error': 'Token expired'}), 400
        if not bcrypt.check_password_hash(user.reset_token, reset_token):
            return jsonify({'error': 'Invalid token'}), 400

        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return jsonify({'message': 'Password reset successfully.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    try:
        data = request.get_json() or {}
        user = User.query.get(get_jwt_identity())
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if not bcrypt.check_password_hash(user.password_hash, data.get('current_password', '')):
            return jsonify({'error': 'Current password incorrect'}), 401
        new_pw = data.get('new_password', '')
        if len(new_pw) < 8:
            return jsonify({'error': 'Min 8 characters'}), 400
        user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
        db.session.commit()
        return jsonify({'message': 'Password changed'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===================== PRODUCTS ENDPOINTS =====================

@app.route('/api/products/makes', methods=['GET'])
@jwt_required()
def get_makes():
    try:
        data = load_products_data()
        if data.get('error'):
            return jsonify({'error': data['error'], 'makes': [], 'total_items': 0, 'total_makes': 0}), 200

        items = data.get('Sheet1', [])
        makes_dict = {}
        for item in items:
            make = item.get('Make', '').strip()
            if not make:
                continue
            if make not in makes_dict:
                makes_dict[make] = {'name': make, 'count': 0, 'total_value': 0.0}
            makes_dict[make]['count'] += 1
            makes_dict[make]['total_value'] += (
                _safe_number(item.get('Net Price'), 0) *
                _safe_number(item.get('Quantity'), 1)
            )

        for m in makes_dict.values():
            m['total_value'] = round(m['total_value'], 2)

        makes_list = sorted(makes_dict.values(), key=lambda x: x['name'].lower())
        return jsonify({
            'makes': makes_list,
            'total_items': len(items),
            'total_makes': len(makes_list)
        }), 200
    except Exception as e:
        print(f"get_makes error: {e}")
        return jsonify({'error': str(e), 'makes': [], 'total_items': 0, 'total_makes': 0}), 500


@app.route('/api/products/by-make/<path:make_name>', methods=['GET'])
@jwt_required()
def get_products_by_make(make_name):
    try:
        data = load_products_data()
        if data.get('error'):
            return jsonify({'error': data['error'], 'products': [], 'count': 0}), 200

        items = data.get('Sheet1', [])
        filtered = [
            i for i in items
            if i.get('Make', '').strip().lower() == make_name.strip().lower()
        ]
        total_value = sum(
            _safe_number(i.get('Net Price'), 0) * _safe_number(i.get('Quantity'), 1)
            for i in filtered
        )
        return jsonify({
            'make': make_name,
            'products': filtered,
            'count': len(filtered),
            'total_value': round(total_value, 2)
        }), 200
    except Exception as e:
        print(f"get_products_by_make error: {e}")
        return jsonify({'error': str(e), 'products': [], 'count': 0}), 500


@app.route('/api/products/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        query = request.args.get('q', '').lower().strip()
        make_filter = request.args.get('make', '').lower().strip()
        limit = min(int(request.args.get('limit', 500)), 2000)

        data = load_products_data()
        if data.get('error'):
            return jsonify({'error': data['error'], 'results': [], 'count': 0}), 200

        items = data.get('Sheet1', [])
        results = []

        for item in items:
            if make_filter and item.get('Make', '').strip().lower() != make_filter:
                continue
            if query:
                searchable = ' '.join([
                    str(item.get('Sl.No', '') or ''),
                    str(item.get('Make', '') or ''),
                    str(item.get('Model', '') or ''),
                    str(item.get('Description', '') or ''),
                    str(item.get('Net Price', '') or ''),
                    str(item.get('Quantity', '') or '')
                ]).lower()
                if query not in searchable:
                    continue
            results.append(item)
            if len(results) >= limit:
                break

        return jsonify({
            'results': results,
            'count': len(results),
            'query': query,
            'truncated': len(results) >= limit
        }), 200
    except Exception as e:
        print(f"search error: {e}")
        return jsonify({'error': str(e), 'results': [], 'count': 0}), 500


@app.route('/api/products/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        data = load_products_data()
        if data.get('error'):
            return jsonify({
                'error': data['error'],
                'total_items': 0, 'total_makes': 0,
                'total_value': 0, 'makes': []
            }), 200

        items = data.get('Sheet1', [])
        makes = sorted(set(
            i.get('Make', '').strip()
            for i in items if i.get('Make', '').strip()
        ))
        total_value = sum(
            _safe_number(i.get('Net Price'), 0) * _safe_number(i.get('Quantity'), 1)
            for i in items
        )
        return jsonify({
            'total_items': len(items),
            'total_makes': len(makes),
            'total_value': round(total_value, 2),
            'makes': makes
        }), 200
    except Exception as e:
        print(f"stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/update', methods=['POST'])
@jwt_required()
def update_products():
    if not DB_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503
    user = User.query.get(get_jwt_identity())
    if not user or user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json(force=True)
        ok, msg = save_products_data(data)
        if ok:
            return jsonify({'message': msg}), 200
        return jsonify({'error': msg}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['DELETE'])
@jwt_required()
def clear_cache():
    if not DB_AVAILABLE:
        return jsonify({'message': 'Cache cleared (no DB)'}), 200
    try:
        user_id = get_jwt_identity()
        ProductCache.query.filter_by(
            user_id=user_id, is_deleted=False
        ).update({'is_deleted': True})
        db.session.commit()
        return jsonify({'message': 'Cache cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===================== ERROR HANDLERS =====================

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(e):
    # Try to serve index.html for SPA
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large (max 50MB)'}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(503)
def service_unavailable(e):
    return jsonify({'error': 'Service unavailable'}), 503


# ===================== JWT ERROR HANDLERS =====================

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token expired', 'code': 'TOKEN_EXPIRED'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Auth required', 'code': 'MISSING_TOKEN'}), 401


# ===================== RUN =====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    print(f"Starting server on port {port}, debug={debug}")
    print(f"Frontend: {FRONTEND_DIR}")
    app.run(debug=debug, host='0.0.0.0', port=port)