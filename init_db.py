from dotenv import load_dotenv
import os

# ⚠️ CARGAR VARIABLES ANTES DE IMPORTAR ANYTHING
# Cargar explícitamente config.env para desarrollo local
load_dotenv('config.env')

# Ahora importar el resto
from app import create_app
from app.database import db
from app.models import Usuario, Mascota, Cita, Adopcion

# Verificar que se cargaron las variables
print("=" * 70)
print("VERIFICACIÓN DE VARIABLES DE ENTORNO")
print("=" * 70)
print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_HOST: {os.getenv('DB_HOST')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"DB_PASSWORD: {'***' if os.getenv('DB_PASSWORD') else 'NO DEFINIDA'}")
print("=" * 70)
print()

app = create_app('development')

try:
    with app.app_context():
        # Prueba de conexión a la base de datos antes de crear tablas
        from sqlalchemy import text
        from app.database import db
        print("🔌 Probando conexión a la base de datos...")
        db.session.execute(text("SELECT 1"))
        print("✅ Conexión exitosa")
        print("📦 Creando tablas...")
        db.create_all()
        print("✅ Tablas creadas")
        
        # Crear usuarios de prueba
        admin = Usuario(
            email='admin@test.com',
            nombre='Administrador',
            rol='ADMIN',
            activo=True
        )
        admin.set_password('admin123')
        
        cliente = Usuario(
            email='cliente@test.com',
            nombre='Cliente Prueba',
            rol='CLIENTE',
            activo=True
        )
        cliente.set_password('cliente123')
        
        db.session.add(admin)
        db.session.add(cliente)
        db.session.commit()
        
        print("✅ Usuarios creados:")
        print("   📧 admin@test.com / admin123")
        print("   📧 cliente@test.com / cliente123")

except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
