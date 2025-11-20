import os
from pathlib import Path
from dotenv import load_dotenv

# Obtener la ruta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Solo cargar .env si no estamos en Lambda
if not os.environ.get('LAMBDA_TASK_ROOT'):
    load_dotenv(BASE_DIR / 'config.env')

class Config:
    # Forzar uso de la carpeta instance/
    INSTANCE_PATH = BASE_DIR / 'instance'
    
    # Crear la carpeta instance si no existe (solo si no estamos en Lambda)
    if not os.environ.get('LAMBDA_TASK_ROOT'):
        INSTANCE_PATH.mkdir(exist_ok=True)
    
    # Base de datos - Solo Supabase PostgreSQL en Lambda, SQLite en local como fallback
    _is_lambda = os.environ.get('LAMBDA_TASK_ROOT') is not None
    
    # Obtener DATABASE_URL (Supabase PostgreSQL)
    _database_url = os.environ.get('DATABASE_URL', '').strip()
    
    # Si DATABASE_URL tiene el placeholder [YOUR-PASSWORD], tratarlo como vacío
    if '[YOUR-PASSWORD]' in _database_url or '[PASSWORD]' in _database_url:
        _database_url = ''
    
    # Si la URL es PostgreSQL pero no especifica driver, usar pg8000 (puro Python, funciona en Lambda)
    if _database_url and _database_url.startswith('postgresql://') and '+pg8000' not in _database_url and '+psycopg' not in _database_url and '+psycopg2' not in _database_url:
        # Cambiar postgresql:// a postgresql+pg8000://
        _database_url = _database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    # Si tiene psycopg2 en la URL, cambiarlo a pg8000
    elif _database_url and '+psycopg2' in _database_url:
        _database_url = _database_url.replace('postgresql+psycopg2://', 'postgresql+pg8000://', 1)
    elif _database_url and '+psycopg://' in _database_url:
        _database_url = _database_url.replace('postgresql+psycopg://', 'postgresql+pg8000://', 1)
    
    # En Lambda: REQUERIR DATABASE_URL (Supabase)
    if _is_lambda:
        if not _database_url or not _database_url.startswith('postgresql'):
            raise ValueError(
                "❌ ERROR: DATABASE_URL (Supabase PostgreSQL) es REQUERIDA en Lambda. "
                "Configura DATABASE_URL en zappa_settings.json con tu URL de Supabase."
            )
    # Local: usar DATABASE_URL si existe, o SQLite como fallback para desarrollo
    else:
        if not _database_url:
            # Fallback a SQLite para desarrollo local
            _database_url = f'sqlite:///{INSTANCE_PATH}/veterinaria.db'
    
    SQLALCHEMY_DATABASE_URI = _database_url
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu-secret-key-super-segura')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
