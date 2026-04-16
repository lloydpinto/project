from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, create_refresh_token
)
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import json
import os
import uuid
import secrets
import hashlib
import platform

from config import Config
from database import db, init_db
from models import User, LoginHistory, ProductCache

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
init_db(app)

# ===================== UTILITY =====================

def generate_machine_id():
    info = f"{platform.node()}-{platform.system()}-{platform.machine()}-{platform.processor()}"
    return hashlib.sha256(info.encode()).hexdigest()[:32]

def load_products_data():
    try:
        path = app.config.get(
            'PRODUCTS_JSON_PATH',
            os.path.join(os.path.dirname(__file__), 'data', 'products.json')
        )
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading products: {e}")
    return {"Sheet1": []}

def save_products_data(data):
    try:
        path = app.config.get(
            'PRODUCTS_JSON_PATH',
            os.path.join(os.path.dirname(__file__), 'data', 'products.json')
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving: {e}")
        return False

def seed_default_users():
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
            print("Default users created: admin/Admin@123 | demo/Demo@123")

seed_default_users()

# ===================== SERVE FRONTEND =====================

@app.route('/')
def serve_login():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(app.static_folder, 'dashboard.html')

@app.route('/forgot-password')
def serve_forgot_password():
    return send_from_directory(app.static_folder, 'forgot_password.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(app.static_folder, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

# ===================== AUTH ENDPOINTS =====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        required = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        if User.query.filter_by(username=data['username'].lower().strip()).first():
            return jsonify({'error': 'Username already exists'}), 409

        if User.query.filter_by(email=data['email'].lower().strip()).first():
            return jsonify({'error': 'Email already registered'}), 409

        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        user = User(
            id=str(uuid.uuid4()),
            username=data['username'].lower().strip(),
            email=data['email'].lower().strip(),
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
    try:
        data = request.get_json()
        username = data.get('username', '').lower().strip()
        password = data.get('password', '')
        machine_id = data.get('machine_id', '')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account is deactivated. Contact administrator.'}), 403

        if not bcrypt.check_password_hash(user.password_hash, password):
            log = LoginHistory(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500],
                machine_id=machine_id,
                status='failed'
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'error': 'Invalid credentials'}), 401

        user.last_login = datetime.utcnow()
        if machine_id:
            user.machine_id = machine_id

        log = LoginHistory(
            user_id=user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500],
            machine_id=machine_id,
            status='success'
        )
        db.session.add(log)
        db.session.commit()

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
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({
                'message': 'If an account exists with that email, a token has been generated.'
            }), 200

        reset_token = secrets.token_urlsafe(32)
        user.reset_token = bcrypt.generate_password_hash(reset_token).decode('utf-8')
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        return jsonify({
            'message': 'Reset token generated successfully.',
            'reset_token': reset_token,
            'note': 'In production, this token is sent via email.',
            'expires_in': '1 hour'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        reset_token = data.get('reset_token', '')
        new_password = data.get('new_password', '')

        if not all([email, reset_token, new_password]):
            return jsonify({'error': 'All fields are required'}), 400

        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        user = User.query.filter_by(email=email).first()

        if not user or not user.reset_token:
            return jsonify({'error': 'Invalid reset request'}), 400

        if user.reset_token_expiry < datetime.utcnow():
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            return jsonify({'error': 'Token has expired. Please request a new one.'}), 400

        if not bcrypt.check_password_hash(user.reset_token, reset_token):
            return jsonify({'error': 'Invalid reset token'}), 400

        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        return jsonify({'message': 'Password reset successfully. You can now sign in.'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()}), 200


@app.route('/api/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        data = request.get_json()
        user = User.query.get(get_jwt_identity())

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not bcrypt.check_password_hash(user.password_hash, data.get('current_password', '')):
            return jsonify({'error': 'Current password is incorrect'}), 401

        new_password = data.get('new_password', '')
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400

        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===================== PRODUCTS ENDPOINTS =====================

@app.route('/api/products/makes', methods=['GET'])
@jwt_required()
def get_makes():
    try:
        data = load_products_data()
        items = data.get('Sheet1', [])
        makes_dict = {}

        for item in items:
            make = item.get('Make', '')
            if not make:
                continue
            if make not in makes_dict:
                makes_dict[make] = {
                    'name': make,
                    'count': 0,
                    'total_value': 0.0
                }
            makes_dict[make]['count'] += 1
            price = item.get('Net Price', 0) or 0
            qty = item.get('Quantity', 1) or 1
            makes_dict[make]['total_value'] += price * qty

        makes_list = list(makes_dict.values())

        return jsonify({
            'makes': makes_list,
            'total_items': len(items),
            'total_makes': len(makes_list)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/by-make/<make_name>', methods=['GET'])
@jwt_required()
def get_products_by_make(make_name):
    try:
        data = load_products_data()
        items = data.get('Sheet1', [])
        filtered = [
            i for i in items
            if i.get('Make', '').lower() == make_name.lower()
        ]
        total_value = sum(
            (i.get('Net Price', 0) or 0) * (i.get('Quantity', 1) or 1)
            for i in filtered
        )
        return jsonify({
            'make': make_name,
            'products': filtered,
            'count': len(filtered),
            'total_value': round(total_value, 2)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        query = request.args.get('q', '').lower().strip()
        make_filter = request.args.get('make', '').lower().strip()

        data = load_products_data()
        items = data.get('Sheet1', [])
        results = []

        for item in items:
            if make_filter and item.get('Make', '').lower() != make_filter:
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

        return jsonify({
            'results': results,
            'count': len(results),
            'query': query
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        data = load_products_data()
        items = data.get('Sheet1', [])
        makes = set(i.get('Make', '') for i in items if i.get('Make'))
        total_value = sum(
            (i.get('Net Price', 0) or 0) * (i.get('Quantity', 1) or 1)
            for i in items
        )
        return jsonify({
            'total_items': len(items),
            'total_makes': len(makes),
            'total_value': round(total_value, 2),
            'makes': list(makes)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/update', methods=['POST'])
@jwt_required()
def update_products():
    user = User.query.get(get_jwt_identity())
    if not user or user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json()
        if save_products_data(data):
            return jsonify({'message': 'Products updated successfully'}), 200
        return jsonify({'error': 'Failed to save'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cache/clear', methods=['DELETE'])
@jwt_required()
def clear_cache():
    try:
        user_id = get_jwt_identity()
        ProductCache.query.filter_by(
            user_id=user_id, is_deleted=False
        ).update({'is_deleted': True})
        db.session.commit()
        return jsonify({'message': 'Cache cleared successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===================== ERROR HANDLERS =====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization required', 'code': 'MISSING_TOKEN'}), 401


# ===================== RUN =====================

if __name__ == '__main__':
    os.makedirs(
        os.path.join(os.path.dirname(__file__), 'data'),
        exist_ok=True
    )
    app.run(debug=True, host='0.0.0.0', port=5000)