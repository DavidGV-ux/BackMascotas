import os
from dotenv import load_dotenv

# Solo cargar .env si no estamos en Lambda
if not os.environ.get('LAMBDA_TASK_ROOT'):
    # Cargar variables desde config.env explícitamente en entorno local
    load_dotenv('config.env')


class Config:
    # Para Lambda, usar SQLite temporal o RDS
    db_uri = os.getenv('DATABASE_URL')
    
    if not db_uri:
        # Si no hay DATABASE_URL, construir desde componentes
        if os.getenv('DB_HOST'):
            from urllib.parse import quote_plus
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = quote_plus(os.getenv('DB_PASSWORD', ''))
            db_host = os.getenv('DB_HOST', 'localhost')
            db_name = os.getenv('DB_NAME', 'veterinaria_db')
            db_uri = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}/{db_name}"
        else:
            # Fallback a SQLite (solo para desarrollo)
            db_uri = 'sqlite:///veterinaria.db'
    
    SQLALCHEMY_DATABASE_URI = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 1,
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    
    S3_BUCKET_PHOTOS = os.getenv('S3_BUCKET_PHOTOS')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config(config_name=None):
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'default': DevelopmentConfig
    }
    return configs.get(config_name or 'default', DevelopmentConfig)
