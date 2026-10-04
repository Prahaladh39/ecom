import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask Session Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'school-marketplace-secret-key-class12-2026')
    
    # Upload Configurations (Up to 3 images per product)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # MySQL Database Settings (Change according to your local MySQL credentials)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')  # Set your MySQL root password here if any
    MYSQL_DB = os.environ.get('MYSQL_DB', 'school_ecom_db')
    
    # SQLite Fallback Settings (Guarantees app works smoothly even if MySQL server is not started)
    USE_SQLITE_FALLBACK = True
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'school_ecom.db')
