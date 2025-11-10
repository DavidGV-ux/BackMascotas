from app import create_app, db
from app.models.usuario import Usuario

app = create_app('development')

with app.app_context():
    print("\n" + "="*70)
    print("USUARIOS EN LA BASE DE DATOS")
    print("="*70 + "\n")
    
    usuarios = Usuario.query.all()
    
    for u in usuarios:
        print(f"📧 Email: {u.email}")
        print(f"   Nombre: {u.nombre}")
        print(f"   Rol: '{u.rol}' (longitud: {len(u.rol)})")
        print(f"   Activo: {u.activo}\n")
    
    print("="*70)
    email = input("\n¿Email del admin a corregir? (Enter para salir): ").strip().lower()
    
    if email:
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            print(f"\nRol actual: '{usuario.rol}'")
            usuario.rol = 'ADMINISTRADOR'
            db.session.commit()
            print(f"✅ Rol actualizado a: '{usuario.rol}'")
        else:
            print("❌ Usuario no encontrado")
