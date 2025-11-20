"""
Script para crear usuarios administradores en AWS Lambda.

Métodos de ejecución:

1. Crear admin por defecto:
   zappa invoke dev 'init_admin_lambda.init_admin'

2. Crear admin personalizado:
   zappa invoke dev 'init_admin_lambda.create_admin' --raw '{"email":"admin@test.com","password":"123456","nombre":"Admin Test"}'

3. Crear múltiples admins:
   zappa invoke dev 'init_admin_lambda.create_admin' --raw '{"email":"admin1@test.com","password":"123456","nombre":"Admin 1"}'
   zappa invoke dev 'init_admin_lambda.create_admin' --raw '{"email":"admin2@test.com","password":"123456","nombre":"Admin 2"}'

4. Listar todos los usuarios:
   zappa invoke dev 'init_admin_lambda.list_users'

5. Actualizar contraseña de admin:
   zappa invoke dev 'init_admin_lambda.update_admin_password' --raw '{"email":"admin@test.com","password":"nueva123"}'
"""

from run import app
import json

def init_admin():
    """Inicializa el primer usuario administrador con credenciales por defecto"""
    with app.app_context():
        from app.database import db
        from app.models.usuario import Usuario
        
        # Importar todos los modelos
        from app.models import usuario, mascota, cita, adopcion, historial_medico
        
        print("=" * 70)
        print("🔧 INICIALIZANDO ADMINISTRADOR EN LAMBDA")
        print("=" * 70)
        print(f"Base de datos: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')[:50]}...")
        
        # Crear tablas si no existen
        try:
            db.create_all()
            print("✅ Tablas verificadas/creadas")
        except Exception as e:
            print(f"⚠️ Error al crear tablas: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Verificar si ya existe un administrador
        existing_admin = Usuario.query.filter_by(rol='ADMINISTRADOR').first()
        admin_email = None
        
        if existing_admin:
            print(f"\n✅ Ya existe un administrador:")
            print(f"   - Email: {existing_admin.email}")
            print(f"   - Nombre: {existing_admin.nombre}")
            print(f"   - Activo: {existing_admin.activo}")
            
            # Actualizar contraseña a la predeterminada
            print(f"\n🔄 Actualizando contraseña...")
            existing_admin.set_password('admin123')
            existing_admin.activo = True
            db.session.commit()
            print(f"✅ Contraseña actualizada a 'admin123'")
            admin_email = existing_admin.email
            
        else:
            print(f"\n📝 Creando nuevo administrador...")
            
            # Crear administrador por defecto
            nuevo_admin = Usuario(
                email='admin@veterinaria.com',
                nombre='Administrador',
                rol='ADMINISTRADOR',
                activo=True
            )
            nuevo_admin.set_password('admin123')
            
            db.session.add(nuevo_admin)
            db.session.commit()
            
            print(f"✅ Administrador creado exitosamente!")
            print(f"   - Email: admin@veterinaria.com")
            print(f"   - Password: admin123")
            print(f"   - Rol: ADMINISTRADOR")
            admin_email = nuevo_admin.email
        
        # Listar todos los usuarios
        print("\n" + "=" * 70)
        print("📊 TODOS LOS USUARIOS:")
        print("=" * 70)
        todos = Usuario.query.all()
        for u in todos:
            print(f"   - {u.email} | {u.nombre} | {u.rol} | Activo: {u.activo}")
        print(f"\nTotal: {len(todos)} usuarios")
        print("=" * 70)
        
        return {
            'status': 'success',
            'message': 'Administrador inicializado correctamente',
            'admin_email': admin_email
        }

def create_admin(email=None, password=None, nombre=None, telefono=None, direccion=None):
    """
    Crea un nuevo usuario administrador con parámetros personalizados.
    
    Args:
        email: Email del administrador (requerido)
        password: Contraseña (mínimo 6 caracteres)
        nombre: Nombre completo (opcional, por defecto 'Administrador')
        telefono: Teléfono (opcional)
        direccion: Dirección (opcional)
    
    Returns:
        dict: Resultado de la operación
    """
    with app.app_context():
        from app.database import db
        from app.models.usuario import Usuario
        
        # Importar todos los modelos
        from app.models import usuario, mascota, cita, adopcion, historial_medico
        
        print("=" * 70)
        print("🔧 CREANDO ADMINISTRADOR PERSONALIZADO")
        print("=" * 70)
        
        # Valores por defecto
        email = email or 'admin@veterinaria.com'
        password = password or 'admin123'
        nombre = nombre or 'Administrador'
        
        # Validaciones
        if not email:
            return {'status': 'error', 'message': 'El email es requerido'}
        
        if len(password) < 6:
            return {'status': 'error', 'message': 'La contraseña debe tener al menos 6 caracteres'}
        
        # Crear tablas si no existen
        try:
            db.create_all()
            print("✅ Tablas verificadas/creadas")
        except Exception as e:
            print(f"⚠️ Error al crear tablas: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': f'Error al crear tablas: {str(e)}'}
        
        # Verificar si el email ya existe
        existing_user = Usuario.query.filter_by(email=email).first()
        
        if existing_user:
            print(f"\n⚠️ El usuario '{email}' ya existe")
            print(f"   - Rol actual: {existing_user.rol}")
            print(f"   - Actualizando a ADMINISTRADOR...")
            
            existing_user.rol = 'ADMINISTRADOR'
            existing_user.set_password(password)
            existing_user.nombre = nombre
            existing_user.activo = True
            if telefono:
                existing_user.telefono = telefono
            if direccion:
                existing_user.direccion = direccion
            
            db.session.commit()
            
            print(f"✅ Usuario actualizado exitosamente!")
            print(f"   - Email: {email}")
            print(f"   - Password: {password}")
            print(f"   - Rol: ADMINISTRADOR")
            
            return {
                'status': 'success',
                'message': 'Usuario actualizado a administrador',
                'usuario': {
                    'email': existing_user.email,
                    'nombre': existing_user.nombre,
                    'rol': existing_user.rol,
                    'activo': existing_user.activo
                }
            }
        
        # Crear nuevo administrador
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
            
            print(f"✅ Administrador creado exitosamente!")
            print(f"   - Email: {email}")
            print(f"   - Password: {password}")
            print(f"   - Nombre: {nombre}")
            print(f"   - Rol: ADMINISTRADOR")
            
            return {
                'status': 'success',
                'message': 'Administrador creado exitosamente',
                'usuario': {
                    'email': nuevo_admin.email,
                    'nombre': nuevo_admin.nombre,
                    'rol': nuevo_admin.rol,
                    'activo': nuevo_admin.activo,
                    'id': nuevo_admin.id
                }
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al crear administrador: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': f'Error al crear administrador: {str(e)}'}

def list_users():
    """Lista todos los usuarios en la base de datos"""
    with app.app_context():
        from app.database import db
        from app.models.usuario import Usuario
        
        # Importar todos los modelos
        from app.models import usuario, mascota, cita, adopcion, historial_medico
        
        print("=" * 70)
        print("📊 LISTADO DE USUARIOS")
        print("=" * 70)
        
        try:
            todos = Usuario.query.all()
            
            if not todos:
                print("❌ No hay usuarios en la base de datos")
                return {'status': 'success', 'total': 0, 'usuarios': []}
            
            usuarios_list = []
            for u in todos:
                usuario_info = {
                    'id': u.id,
                    'email': u.email,
                    'nombre': u.nombre,
                    'rol': u.rol,
                    'activo': u.activo,
                    'telefono': u.telefono,
                    'fecha_registro': u.fecha_registro.isoformat() if u.fecha_registro else None
                }
                usuarios_list.append(usuario_info)
                print(f"   - ID: {u.id} | Email: {u.email} | Nombre: {u.nombre} | Rol: {u.rol} | Activo: {u.activo}")
            
            print(f"\nTotal: {len(todos)} usuarios")
            print("=" * 70)
            
            return {
                'status': 'success',
                'total': len(todos),
                'usuarios': usuarios_list
            }
            
        except Exception as e:
            print(f"❌ Error al listar usuarios: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': f'Error al listar usuarios: {str(e)}'}

def update_admin_password(email, password):
    """
    Actualiza la contraseña de un usuario administrador.
    
    Args:
        email: Email del administrador
        password: Nueva contraseña (mínimo 6 caracteres)
    
    Returns:
        dict: Resultado de la operación
    """
    with app.app_context():
        from app.database import db
        from app.models.usuario import Usuario
        
        print("=" * 70)
        print("🔧 ACTUALIZANDO CONTRASEÑA DE ADMINISTRADOR")
        print("=" * 70)
        
        if not email:
            return {'status': 'error', 'message': 'El email es requerido'}
        
        if len(password) < 6:
            return {'status': 'error', 'message': 'La contraseña debe tener al menos 6 caracteres'}
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            return {'status': 'error', 'message': f'Usuario con email {email} no encontrado'}
        
        usuario.set_password(password)
        usuario.activo = True
        
        # Si no es admin, actualizar rol
        if usuario.rol != 'ADMINISTRADOR':
            usuario.rol = 'ADMINISTRADOR'
        
        db.session.commit()
        
        print(f"✅ Contraseña actualizada exitosamente!")
        print(f"   - Email: {email}")
        print(f"   - Nueva contraseña: {password}")
        print(f"   - Rol: {usuario.rol}")
        
        return {
            'status': 'success',
            'message': 'Contraseña actualizada exitosamente',
            'usuario': {
                'email': usuario.email,
                'rol': usuario.rol
            }
        }

if __name__ == '__main__':
    result = init_admin()
    print(f"\n✅ Resultado: {result}")

