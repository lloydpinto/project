import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # Database - Using SQLite for development, MySQL for production
    # For online database, use MySQL/PostgreSQL connection string
    # Example MySQL: 'mysql+pymysql://user:password@host:port/dbname'
    # Example PostgreSQL: 'postgresql://user:password@host:port/dbname'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///authorized_partners.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail settings for password reset
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@authorizedpartners.com')

    # Data file path
    PRODUCTS_JSON_PATH = os.path.join(os.path.dirname(__file__), 'data', 'products.json')