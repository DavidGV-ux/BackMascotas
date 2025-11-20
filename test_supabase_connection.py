"""
Script para probar la conexión a Supabase desde Lambda
Ejecutar con: zappa invoke dev --raw 'exec(open("test_supabase_connection.py").read())'
"""

import os
from urllib.parse import quote_plus

# Obtener DATABASE_URL
database_url = os.environ.get('DATABASE_URL', '')
print(f"🔗 DATABASE_URL configurada: {database_url[:60]}...")

if not database_url:
    print("❌ ERROR: DATABASE_URL no está configurada")
    exit(1)

# Verificar si tiene corchetes o placeholders
if '[YOUR-PASSWORD]' in database_url or '[PASSWORD]' in database_url:
    print("❌ ERROR: DATABASE_URL tiene placeholder de contraseña")
    print("   Debes reemplazar [YOUR-PASSWORD] con tu contraseña real")
    exit(1)

# Probar conexión
try:
    from sqlalchemy import create_engine, text
    
    print(f"🔌 Intentando conectar a Supabase...")
    engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ Conexión exitosa!")
        print(f"   PostgreSQL version: {version[:60]}...")
        
        # Probar crear una tabla de prueba
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        print(f"✅ Tabla de prueba creada correctamente")
        
except Exception as e:
    print(f"❌ ERROR al conectar: {str(e)}")
    print(f"   Tipo de error: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ Todo funciona correctamente!")

