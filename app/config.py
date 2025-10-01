import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Usar SQLite para desarrollo (sin problemas de contraseña)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///veterinaria.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    
    # S3
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
