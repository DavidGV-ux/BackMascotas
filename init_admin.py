from app import create_app
from app.database import db
from app.models.usuario import Usuario
import os

app = create_app('development')

with app.app_context():
    print("=" * 70)
    print("🔍 CONFIGURACIÓN DE BASE DE DATOS")
    print("=" * 70)
    print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Instance Path: {app.instance_path}")
    
    # Verificar si el archivo existe
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///'):
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not db_path.startswith('/'):  # Ruta relativa
            full_path = os.path.join(os.getcwd(), db_path)
            print(f"Ruta completa BD: {full_path}")
            print(f"Archivo existe: {os.path.exists(full_path)}")
    
    print("=" * 70)
    
    # Crear todas las tablas si no existen
    db.create_all()
    print("✅ Tablas creadas/verificadas")
    
    # Buscar usuario admin
    admin = Usuario.query.filter_by(email='l@gmail.com').first()
    
    if admin:
        print(f"\n✅ Usuario 'l@gmail.com' YA EXISTE")
        print(f"   - ID: {admin.id}")
        print(f"   - Rol: '{admin.rol}'")
        print(f"   - Activo: {admin.activo}")
        
        # Actualizar si es necesario
        if admin.rol != 'ADMINISTRADOR':
            print(f"   ⚠️ Actualizando rol de '{admin.rol}' a 'ADMINISTRADOR'")
            admin.rol = 'ADMINISTRADOR'
        
        # Actualizar contraseña
        print("   🔄 Actualizando contraseña a '000000'")
        admin.set_password('000000')
        admin.activo = True
        
        db.session.commit()
        print("   ✅ Usuario actualizado")
        
    else:
        print(f"\n❌ Usuario 'l@gmail.com' NO EXISTE. Creando...")
        
        nuevo_admin = Usuario(
            email='l@gmail.com',
            nombre='Admin L',
            rol='ADMINISTRADOR',
            activo=True
        )
        nuevo_admin.set_password('000000')
        
        db.session.add(nuevo_admin)
        db.session.commit()
        
        print("✅ Usuario admin creado exitosamente!")
        print(f"   - Email: l@gmail.com")
        print(f"   - Password: 000000")
        print(f"   - Rol: ADMINISTRADOR")
    
    print("\n" + "=" * 70)
    print("📊 TODOS LOS USUARIOS EN ESTA BASE DE DATOS:")
    print("=" * 70)
    
    todos = Usuario.query.all()
    if not todos:
        print("❌ No hay usuarios en esta BD")
    else:
        for u in todos:
            print(f"ID: {u.id} | Email: '{u.email}' | Rol: '{u.rol}' | Activo: {u.activo}")
    
    print("=" * 70)
    print(f"Total: {len(todos)} usuarios")
    print("=" * 70)
