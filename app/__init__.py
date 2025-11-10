# app/__init__.py
import os
import logging
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config import config
from .database import db

logging.basicConfig(level=logging.DEBUG)

def create_app(config_name: str = None) -> Flask:
    """Factory para crear instancia de Flask"""
    
    # ✅ ELIMINAR ESTA LÍNEA PROBLEMÁTICA:
    # instance_dir = os.path.join(gettempdir(), 'instance')
    
    # ✅ USAR ESTA EN SU LUGAR (usa la misma ubicación que config.py):
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
    
    app = Flask(__name__, instance_path=instance_dir)
    
    # Load configuration
    if not config_name:
        config_name = 'development'  # Default
    
    app.config.from_object(config[config_name])
    
    # ========== CONFIGURAR CORS ==========
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:4200", "http://127.0.0.1:4200"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Manejar preflight requests manualmente
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"message": "OK"})
            response.headers.add("Access-Control-Allow-Origin", "http://localhost:4200")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
            response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
            return response, 200
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    with app.app_context():
        # Importar blueprints
        from .routes import (
            auth_bp, 
            mascota_bp, 
            adopcion_bp,
            cita_bp, 
            historial_bp, 
            usuarios_bp,
            reportes_bp
        )
        
        # Registrar blueprints
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(mascota_bp, url_prefix='/mascotas')
        app.register_blueprint(adopcion_bp, url_prefix='/adopciones')
        app.register_blueprint(cita_bp, url_prefix='/citas')
        app.register_blueprint(historial_bp, url_prefix='/historial')
        app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
        app.register_blueprint(reportes_bp, url_prefix='/reportes')
        
        # ✅ ELIMINAR ESTA CONDICIÓN, SIEMPRE CREAR TABLAS:
        # db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        # if isinstance(db_uri, str) and db_uri.startswith('sqlite:///tmp'):
        
        # Importar modelos para crear tablas
        from .models import (
            usuario, 
            mascota, 
            adopcion,
            cita, 
            HistorialMedico
        )  # noqa: F401
        
        db.create_all()  # ✅ Siempre crear tablas
        print(f"✅ Base de datos creada en: {app.instance_path}")
    
    # Rutas de health check
    @app.get('/')
    def index():
        return {"status": "ok", "message": "Veterinaria API"}, 200
    
    @app.get('/health')
    def health_check():
        return {"status": "ok"}, 200
    
    return app
