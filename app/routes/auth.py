from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.usuario import Usuario
from app.database import db
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.utils.validators import Validators


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validaciones
    if not data.get('email') or not data.get('password'):
        return jsonify({'msg': 'Email y contraseña son requeridos'}), 400
    
    if not Validators.validate_email(data['email']):
        return jsonify({'msg': 'Email inválido'}), 400
    
    if not Validators.validate_password(data['password']):
        return jsonify({'msg': 'La contraseña debe tener al menos 8 caracteres'}), 400
    
    # Verificar si el email ya existe
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'msg': 'El email ya está registrado'}), 400
    
    # Crear nuevo usuario
    nuevo_usuario = Usuario(
        email=data['email'],
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
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'msg': 'Email y contraseña son requeridos'}), 400
    
    usuario = Usuario.query.filter_by(email=data['email']).first()
    
    if not usuario or not usuario.check_password(data['password']):
        return jsonify({'msg': 'Credenciales incorrectas'}), 401
    
    if not usuario.activo:
        return jsonify({'msg': 'Usuario inactivo'}), 403
    
    # Crear token JWT - CONVERTIR ID A STRING ✅
    access_token = create_access_token(identity=str(usuario.id))
    
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
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    usuario = Usuario.query.get(current_user_id)
    
    if not usuario:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    return jsonify(usuario.to_dict()), 200
