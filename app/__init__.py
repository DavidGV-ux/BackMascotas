import os
import logging
from tempfile import gettempdir
from flask import Flask
from flask_jwt_extended import JWTManager
from .config import get_config
from .database import db

logging.basicConfig(level=logging.DEBUG)


def create_app(config_name: str | None = None) -> Flask:
    # Ensure Flask instance path points to a writable location on Lambda
    instance_dir = os.path.join(gettempdir(), 'instance')
    app = Flask(__name__, instance_path=instance_dir)
    
    # Load configuration
    app.config.from_object(get_config(config_name))
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)  # AÑADIR ESTA LÍNEA
    
    # Register blueprints
    with app.app_context():
        from .routes import auth_bp, mascota_bp, adopcion_bp, cita_bp
        app.register_blueprint(auth_bp, url_prefix="/auth")
        app.register_blueprint(mascota_bp, url_prefix="/mascotas")
        app.register_blueprint(adopcion_bp, url_prefix="/adopciones")
        app.register_blueprint(cita_bp, url_prefix="/citas")
        
        # Auto-init DB on Lambda when using ephemeral SQLite in /tmp
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if isinstance(db_uri, str) and db_uri.startswith('sqlite:////tmp'):
            # Ensure models are imported before create_all
            from .models import usuario, mascota, adopcion, cita  # noqa: F401
            db.create_all()
    
    # Ruta raíz para Lambda health check
    @app.get("/")
    def index():
        return {"status": "ok", "message": "Veterinaria API"}, 200
    
    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200
    
    return app
