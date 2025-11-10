from app import create_app
from app.models.usuario import Usuario

app = create_app('development')

with app.app_context():
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE USUARIOS ADMINISTRADORES")
    print("=" * 70)
    
    admins = Usuario.query.filter_by(rol='ADMINISTRADOR').all()
    
    if not admins:
        print("\n❌ No hay administradores en la base de datos\n")
    else:
        for admin in admins:
            print(f"\n✅ Admin encontrado:")
            print(f"   ID: {admin.id}")
            print(f"   Email: '{admin.email}'")
            print(f"   Nombre: {admin.nombre}")
            print(f"   Activo: {admin.activo}")
            print(f"   Password hash: {admin.password_hash[:30]}...")
    
    print("\n" + "=" * 70)
    print("📊 TODOS LOS USUARIOS EN LA BASE DE DATOS")
    print("=" * 70)
    
    todos = Usuario.query.all()
    for u in todos:
        print(f"Email: '{u.email}' | Rol: {u.rol} | Activo: {u.activo}")
    
    print("\n" + "=" * 70)
