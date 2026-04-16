import os
import tempfile


def get_db_path():
    """
    Get a guaranteed writable database path.
    Tries multiple locations in order of preference.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # List of candidate paths to try
    candidates = [
        # 1. Same folder as app.py (local development)
        os.path.join(base_dir, 'authorized_partners.db'),
        # 2. Parent folder
        os.path.join(os.path.dirname(base_dir), 'authorized_partners.db'),
        # 3. /tmp directory (always writable on any server)
        os.path.join(tempfile.gettempdir(), 'authorized_partners.db'),
        # 4. Absolute /tmp
        '/tmp/authorized_partners.db',
    ]

    for path in candidates:
        try:
            folder = os.path.dirname(path)
            os.makedirs(folder, exist_ok=True)
            # Test write access
            test_file = os.path.join(folder, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✓ Database path: {path}")
            return path
        except (OSError, PermissionError) as e:
            print(f"✗ Cannot write to {path}: {e}")
            continue

    # Last resort
    fallback = os.path.join(tempfile.gettempdir(), 'authorized_partners.db')
    print(f"⚠ Using fallback DB path: {fallback}")
    return fallback


class Config:
    # Security
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'dev-secret-key-please-change-in-production-min-32-chars'
    )
    JWT_SECRET_KEY = os.environ.get(
        'JWT_SECRET_KEY',
        'dev-jwt-key-please-change-in-production-min-32-chars'
    )

    # Database
    _env_db = os.environ.get('DATABASE_URL', '')
    if _env_db:
        # Fix Heroku postgres:// -> postgresql://
        if _env_db.startswith('postgres://'):
            _env_db = _env_db.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = _env_db
    else:
        _db_path = get_db_path()
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{_db_path}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'check_same_thread': False} if 'sqlite' in os.environ.get('DATABASE_URL', 'sqlite') else {}
    }

    # File Upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    PRODUCTS_JSON_PATH = os.path.join(DATA_DIR, 'products.json')