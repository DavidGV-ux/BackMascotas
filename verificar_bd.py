import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'veterinaria.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Agregar campos de transferencia
        cursor.execute("ALTER TABLE adopciones ADD COLUMN mascota_transferida BOOLEAN DEFAULT 0")
        cursor.execute("ALTER TABLE adopciones ADD COLUMN fecha_transferencia DATETIME")
        conn.commit()
        print("✅ Campos agregados exitosamente")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️  Los campos ya existen")
        else:
            print(f"❌ Error: {e}")
    finally:
        conn.close()
else:
    print("❌ Base de datos no encontrada")
