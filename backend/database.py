from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created/verified")
        except Exception as e:
            print(f"Database creation error: {e}")