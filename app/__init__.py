from flask import Flask
from flask_jwt_extended import JWTManager
from .config import get_config
from .database import db

def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    
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
    
    @app.get("/health")
    def health_check():
        return {"status": "ok"}, 200
    
    return app
