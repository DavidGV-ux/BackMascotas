"""
Script para crear el usuario administrador inicial de forma segura.
Compatible con la configuración actualizada de Flask.
"""

import os
import sys
from getpass import getpass
from app import create_app
from app.database import db
from app.models.usuario import Usuario


def create_admin_user():
    """Crea el usuario administrador inicial"""
    
    # Crear aplicación Flask con configuración de desarrollo
    app = create_app('development')
    
    with app.app_context():
        # Mostrar información de la base de datos
        print("=" * 70)
        print("🔍 INFORMACIÓN DE BASE DE DATOS")
        print("=" * 70)
        print(f"URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Instance path: {app.instance_path}")
        print("=" * 70)
        
        # Importar todos los modelos para que SQLAlchemy los reconozca
        from app.models import usuario, mascota, cita, adopcion, historial_medico
        
        print("\n🔧 Verificando/creando tablas de base de datos...")
        
        # Crear todas las tablas si no existen
        try:
            db.create_all()
            print("✅ Tablas de base de datos verificadas/creadas")
        except Exception as e:
            print(f"❌ Error al crear tablas: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        # Mostrar usuarios existentes
        usuarios_existentes = Usuario.query.all()
        if usuarios_existentes:
            print(f"\n📊 Usuarios existentes en la base de datos: {len(usuarios_existentes)}")
            for u in usuarios_existentes:
                print(f"   - {u.email} | Rol: {u.rol} | Activo: {u.activo}")
        else:
            print("\n📊 No hay usuarios en la base de datos")
        
        # Verificar si ya existe un administrador
        admin_exists = Usuario.query.filter_by(rol='ADMINISTRADOR').first()
        
        if admin_exists:
            print("\n⚠️  Ya existe un usuario administrador en el sistema.")
            print(f"📧 Email: {admin_exists.email}")
            respuesta = input("¿Deseas crear otro administrador? (s/n): ")
            if respuesta.lower() != 's':
                print("❌ Operación cancelada.")
                return
        
        print("\n" + "=" * 70)
        print("🔐 CREAR USUARIO ADMINISTRADOR")
        print("=" * 70)
        
        # Solicitar datos de forma segura
        while True:
            email = input("\n📧 Email del administrador: ").strip().lower()
            if not email:
                print("❌ El email no puede estar vacío")
                continue
            
            # Verificar si el email ya existe
            if Usuario.query.filter_by(email=email).first():
                print("❌ Este email ya está registrado")
                continuar = input("¿Deseas actualizar este usuario? (s/n): ")
                if continuar.lower() == 's':
                    usuario_existente = Usuario.query.filter_by(email=email).first()
                    password = getpass("🔒 Nueva contraseña (mínimo 6 caracteres): ")
                    if len(password) < 6:
                        print("❌ La contraseña debe tener al menos 6 caracteres")
                        continue
                    
                    usuario_existente.set_password(password)
                    usuario_existente.rol = 'ADMINISTRADOR'
                    usuario_existente.activo = True
                    db.session.commit()
                    
                    print("\n✅ Usuario actualizado exitosamente!")
                    print(f"📧 Email: {email}")
                    print(f"🎭 Rol: ADMINISTRADOR")
                    return
                continue
            
            break
        
        nombre = input("👤 Nombre completo: ").strip()
        if not nombre:
            nombre = "Administrador"
        
        telefono = input("📞 Teléfono (opcional): ").strip() or None
        direccion = input("📍 Dirección (opcional): ").strip() or None
        
        # Solicitar contraseña de forma segura (oculta)
        while True:
            password = getpass("🔒 Contraseña (mínimo 6 caracteres): ")
            if len(password) < 6:
                print("❌ La contraseña debe tener al menos 6 caracteres")
                continue
            
            password_confirm = getpass("🔒 Confirmar contraseña: ")
            if password != password_confirm:
                print("❌ Las contraseñas no coinciden")
                continue
            
            break
        
        # Crear usuario administrador
        try:
            nuevo_admin = Usuario(
                email=email,
                nombre=nombre,
                telefono=telefono,
                direccion=direccion,
                rol='ADMINISTRADOR',
                activo=True
            )
            nuevo_admin.set_password(password)
            
            db.session.add(nuevo_admin)
            db.session.commit()
            
            print("\n" + "=" * 70)
            print("✅ Usuario administrador creado exitosamente!")
            print("=" * 70)
            print(f"📧 Email: {email}")
            print(f"👤 Nombre: {nombre}")
            print(f"🎭 Rol: ADMINISTRADOR")
            print(f"🔑 ID: {nuevo_admin.id}")
            print(f"✅ Activo: {nuevo_admin.activo}")
            print("\n⚠️  IMPORTANTE: Guarda estas credenciales de forma segura")
            print("=" * 70)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al crear administrador: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
