import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'hirehub-secret-key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/hirehub')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'hirehub')
    MONGO_REQUIRED = os.getenv('MONGO_REQUIRED', 'true').lower() == 'true'
    DEFAULT_ADMIN_EMAIL = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@hirehub.local')
    DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'uploads', 'resumes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8
    JSON_SORT_KEYS = False
