import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with guaranteed persistence."""
    db.init_app(app)

    # Extract the actual file path from SQLite URI
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            print(f"[DB] Directory ensured: {db_dir}")
        print(f"[DB] Full path: {db_path}")

    with app.app_context():
        try:
            # Import all models so tables are registered
            from models import User, LoginHistory, ProductCache

            db.create_all()

            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"[DB] Tables found: {tables}")

            if 'users' not in tables:
                print("[DB] WARNING: 'users' table not found!")
                db.create_all()
                tables = inspector.get_table_names()
                print(f"[DB] Tables after retry: {tables}")

            print("[DB] ✓ Initialized successfully")
        except Exception as e:
            print(f"[DB] ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            raise