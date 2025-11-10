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
    
    # Crear la carpeta instance si no existe
    INSTANCE_PATH.mkdir(exist_ok=True)
    
    # Base de datos en instance/veterinaria.db
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/veterinaria.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'tu-secret-key-super-segura')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Keycloak Configuration
    KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL')
    KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM')
    KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID')
    KEYCLOAK_CLIENT_SECRET = os.getenv('KEYCLOAK_CLIENT_SECRET')
    
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
