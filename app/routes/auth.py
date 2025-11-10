from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.usuario import Usuario
from app.database import db
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.validators import Validators
from app.utils.decorators import keycloak_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Normalizar email
    email = data.get('email', '').strip().lower()
    
    # Validaciones
    if not email or not data.get('password'):
        return jsonify({'msg': 'Email y contraseña son requeridos'}), 400
    
    if not Validators.validate_email(email):
        return jsonify({'msg': 'Email inválido'}), 400
    
    if not Validators.validate_password(data['password']):
        return jsonify({'msg': 'La contraseña debe tener al menos 8 caracteres'}), 400
    
    # Verificar si el email ya existe
    if Usuario.query.filter_by(email=email).first():
        return jsonify({'msg': 'El email ya está registrado'}), 400
    
    # Crear nuevo usuario
    nuevo_usuario = Usuario(
        email=email,
        nombre=data.get('nombre'),
        telefono=data.get('telefono'),
        direccion=data.get('direccion'),
        rol=data.get('rol', 'CLIENTE')
    )
    nuevo_usuario.set_password(data['password'])
    
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    return jsonify({
        'msg': 'Usuario registrado exitosamente',
        'usuario': nuevo_usuario.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Normalizar email
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    print(f"🔍 DEBUG: Email recibido: '{data.get('email')}'")
    print(f"🔍 DEBUG: Email normalizado: '{email}'")
    
    # Validaciones básicas
    if not email or not password:
        print("❌ DEBUG: Email o contraseña vacíos")
        return jsonify({'msg': 'Email y contraseña son requeridos'}), 400
    
    # Buscar usuario
    usuario = Usuario.query.filter_by(email=email).first()
    
    if not usuario:
        print(f"❌ DEBUG: Usuario no encontrado: '{email}'")
        # Mostrar todos los usuarios en la DB para debugging
        todos_usuarios = Usuario.query.all()
        print(f"📊 DEBUG: Total usuarios en DB: {len(todos_usuarios)}")
        for u in todos_usuarios:
            print(f"   - Email: '{u.email}' | Rol: {u.rol} | Activo: {u.activo}")
        return jsonify({'msg': 'Credenciales incorrectas'}), 401
    
    # Verificar contraseña
    print(f"🔐 DEBUG: Verificando contraseña para usuario: '{email}'")
    print(f"🔐 DEBUG: Password hash almacenado: {usuario.password_hash[:20]}...")
    
    if not usuario.check_password(password):
        print(f"❌ DEBUG: Contraseña incorrecta para usuario: '{email}'")
        return jsonify({'msg': 'Credenciales incorrectas'}), 401
    
    # Verificar si está activo
    if not usuario.activo:
        print(f"⚠️ DEBUG: Usuario inactivo: '{email}'")
        return jsonify({'msg': 'Usuario inactivo'}), 403
    
    # Generar token JWT
    access_token = create_access_token(identity=str(usuario.id))
    
    print(f"✅ DEBUG: Login exitoso para usuario: '{email}'")
    print(f"   - ID: {usuario.id}")
    print(f"   - Nombre: {usuario.nombre}")
    print(f"   - Rol: {usuario.rol}")
    
    return jsonify({
        'access_token': access_token,
        'usuario': usuario.to_dict()
    }), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'msg': 'Email es requerido'}), 400
    
    # Generar token de reseteo
    token = AuthService.create_reset_token(email)
    
    if not token:
        # Por seguridad, no revelar si el email existe
        return jsonify({'msg': 'Si el email existe, recibirás instrucciones'}), 200
    
    # Enviar email
    email_service = EmailService()
    email_service.send_reset_password_email(email, token)
    
    return jsonify({'msg': 'Si el email existe, recibirás instrucciones'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'msg': 'Token y nueva contraseña son requeridos'}), 400
    
    if not Validators.validate_password(new_password):
        return jsonify({'msg': 'La contraseña debe tener al menos 8 caracteres'}), 400
    
    # Resetear contraseña
    success = AuthService.reset_password(token, new_password)
    
    if not success:
        return jsonify({'msg': 'Token inválido o expirado'}), 400
    
    return jsonify({'msg': 'Contraseña actualizada exitosamente'}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = int(get_jwt_identity())
    usuario = Usuario.query.get(current_user_id)
    
    if not usuario:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    return jsonify(usuario.to_dict()), 200

# Keycloak endpoints
@auth_bp.route('/kc/login', methods=['POST'])
def keycloak_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'msg': 'Faltan credenciales'}), 400
    try:
        kc = AuthService.get_keycloak_client()
        token = kc.token(username, password)
        return jsonify({
            'access_token': token.get('access_token'),
            'refresh_token': token.get('refresh_token'),
            'expires_in': token.get('expires_in'),
            'token_type': token.get('token_type')
        }), 200
    except Exception as e:
        return jsonify({'msg': 'Credenciales inválidas o Keycloak no disponible', 'detalle': str(e)}), 401

@auth_bp.route('/kc/me', methods=['GET'])
@keycloak_required
def keycloak_me(userinfo):
    return jsonify(userinfo), 200
