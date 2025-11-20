# app/__init__.py
import os
import sys
import logging
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config import config
from .database import db


# Configurar logging para Lambda y local
if os.environ.get('LAMBDA_TASK_ROOT'):
    # En Lambda, usar el logger de Python
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
else:
    # Local: debug más detallado
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


logger = logging.getLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    """Factory para crear instancia de Flask"""

    # Detectar si estamos en Lambda
    is_lambda = os.environ.get('LAMBDA_TASK_ROOT') is not None

    # Configurar directorio de instancia
    # En Lambda, no necesitamos instance_path si usamos /tmp directamente
    if is_lambda:
        # En Lambda, no usar instance_path ya que Flask puede tener problemas con rutas
        app = Flask(__name__)
        logger.info("Inicializando Flask en modo Lambda")
    else:
        # Local: usar la carpeta instance/ del proyecto
        instance_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        app = Flask(__name__, instance_path=instance_dir)
        logger.info(f"Inicializando Flask en modo local - instance_path: {instance_dir}")

    # Load configuration
    if not config_name:
        # Auto-detectar configuración basada en entorno
        if is_lambda:
            config_name = 'production'
        else:
            config_name = 'development'

    app.config.from_object(config[config_name])

    # ==================== CONFIGURACIÓN DE CORS ====================
    # Obtener orígenes permitidos desde variables de entorno o usar defaults
    cors_origins_env = os.getenv('CORS_ORIGINS', '')
    if cors_origins_env:
        allowed_origins = cors_origins_env.split(',')
    else:
        # Default origins si no hay variable de entorno
        allowed_origins = [
            'http://frontmascotas.s3-website.us-east-2.amazonaws.com',
            'http://localhost:4200',
            'http://127.0.0.1:4200'
        ]

    logger.info(f"🌐 CORS configurado para orígenes: {allowed_origins}")

    # Configurar CORS con flask-cors
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # Manejar preflight requests manualmente (doble protección)
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            origin = request.headers.get('Origin')
            if origin in allowed_origins or '*' in allowed_origins:
                response = jsonify({"message": "OK"})
                response.headers.add("Access-Control-Allow-Origin", origin)
                response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,X-Requested-With")
                response.headers.add("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS,PATCH")
                response.headers.add("Access-Control-Max-Age", "3600")
                response.headers.add("Access-Control-Allow-Credentials", "true")
                return response, 200

    # Agregar headers CORS a todas las respuestas (triple protección)
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin in allowed_origins or '*' in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    # ==================== FIN CONFIGURACIÓN DE CORS ====================

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

        # Crear tablas solo si no existen (evitar errores en Lambda)
        try:
            # Verificar conexión antes de crear tablas (solo para MySQL/PostgreSQL)
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            logger.info(f"🔗 Intentando conectar a: {db_uri[:50]}..." if db_uri else "⚠️ No hay DATABASE_URL configurada")

            if db_uri and not db_uri.startswith('sqlite'):
                try:
                    # Test connection
                    with db.engine.connect() as conn:
                        conn.execute(db.text("SELECT 1"))
                    logger.info("✅ Conexión a base de datos verificada")

                    # Crear tablas
                    db.create_all()
                    logger.info(f"✅ Base de datos inicializada: {db_uri[:50]}...")
                except Exception as conn_error:
                    error_msg = str(conn_error)
                    logger.error(f"❌ ERROR: No se pudo conectar a la base de datos: {error_msg}")
                    logger.error(f"   URI: {db_uri[:80]}...")
                    # No hacer raise, permitir que la app inicie pero los endpoints de DB fallarán
                    logger.warning("   ⚠️ La aplicación continuará pero los endpoints de DB fallarán hasta que se corrija la conexión")
            else:
                # SQLite o sin configuración
                if db_uri:
                    db.create_all()
                    logger.info(f"✅ Base de datos SQLite inicializada")
                else:
                    logger.warning("⚠️ No hay configuración de base de datos. La aplicación puede fallar en endpoints de DB")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ ERROR inesperado al inicializar la base de datos: {error_msg}", exc_info=True)
            # No hacer raise para evitar que la app falle completamente
            logger.warning("   ⚠️ La aplicación continuará pero puede fallar en endpoints de DB")

    # Manejar errores globales
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Error interno: {str(error)}", exc_info=True)
        return jsonify({
            "error": "Internal Server Error",
            "message": "Ha ocurrido un error interno"
        }), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Not Found",
            "message": "Recurso no encontrado"
        }), 404

    # Rutas de health check
    @app.get('/')
    def index():
        try:
            return jsonify({
                "status": "ok",
                "message": "Veterinaria API",
                "environment": "lambda" if is_lambda else "local"
            }), 200
        except Exception as e:
            logger.error(f"Error en endpoint /: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.get('/health')
    def health_check():
        try:
            # Verificar conexión a base de datos
            db_status = "ok"
            try:
                db.session.execute(db.text("SELECT 1"))
            except Exception as e:
                db_status = f"error: {str(e)}"
                logger.warning(f"DB health check failed: {str(e)}")

            return jsonify({
                "status": "ok",
                "database": db_status,
                "environment": "lambda" if is_lambda else "local"
            }), 200
        except Exception as e:
            logger.error(f"Error en health check: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "message": str(e)}), 500

    logger.info("✅ Aplicación Flask inicializada correctamente")
    return app