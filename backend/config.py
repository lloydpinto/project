import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 28800  # 8 hours

    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///authorized_partners.db')
    # Fix Heroku postgres:// -> postgresql://
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PRODUCTS_JSON_PATH = os.path.join(BASE_DIR, 'data', 'products.json')