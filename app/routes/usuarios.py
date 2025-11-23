# app/routes/usuarios.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.usuario import Usuario
from app.database import db
from app.utils.decorators import admin_required

usuarios_bp = Blueprint('usuarios', __name__)

# Listar todos los usuarios (solo admin)
@usuarios_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([u.to_dict() for u in usuarios]), 200


# Crear veterinario (solo admin)
@usuarios_bp.route('/crear-veterinario', methods=['POST'])
@jwt_required()
@admin_required
def crear_veterinario():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password') or not data.get('nombre'):
        return jsonify({'msg': 'Email, password y nombre son requeridos'}), 400
    
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'msg': 'El email ya está registrado'}), 400
    
    nuevo_veterinario = Usuario(
        email=data['email'],
        nombre=data['nombre'],
        telefono=data.get('telefono'),
        direccion=data.get('direccion'),
        rol='VETERINARIO'
    )
    nuevo_veterinario.set_password(data['password'])
    
    db.session.add(nuevo_veterinario)
    db.session.commit()
    
    return jsonify({
        'msg': 'Veterinario creado exitosamente',
        'usuario': nuevo_veterinario.to_dict()
    }), 201


# Obtener roles disponibles
@usuarios_bp.route('/roles-disponibles', methods=['GET'])
@jwt_required()
@admin_required
def roles_disponibles():
    """Retorna la lista de roles disponibles para selección"""
    roles = [
        {'value': 'CLIENTE', 'label': 'Cliente'},
        {'value': 'VETERINARIO', 'label': 'Veterinario'},
        {'value': 'ADMINISTRADOR', 'label': 'Administrador'}
    ]
    return jsonify(roles), 200


# Actualizar rol de usuario (solo admin)
@usuarios_bp.route('/<int:id>/cambiar-rol', methods=['PUT'])
@jwt_required()
@admin_required
def cambiar_rol(id):
    """Cambiar rol de usuario con validación estricta"""
    usuario = Usuario.query.get_or_404(id)
    data = request.get_json()
    
    nuevo_rol = data.get('rol')
    
    # Validar que el rol esté presente
    if not nuevo_rol:
        return jsonify({'msg': 'El campo "rol" es requerido'}), 400
    
    # Validar que el rol sea uno de los permitidos
    roles_permitidos = ['CLIENTE', 'VETERINARIO', 'ADMINISTRADOR']
    if nuevo_rol not in roles_permitidos:
        return jsonify({
            'msg': f'Rol inválido. Los roles permitidos son: {", ".join(roles_permitidos)}',
            'roles_disponibles': roles_permitidos
        }), 400
    
    # Validar que no se esté cambiando el rol del mismo usuario admin
    current_user_id = int(get_jwt_identity())
    if usuario.id == current_user_id and nuevo_rol != 'ADMINISTRADOR':
        return jsonify({'msg': 'No puedes cambiar tu propio rol de administrador'}), 400
    
    # Guardar rol anterior para el mensaje
    rol_anterior = usuario.rol
    usuario.rol = nuevo_rol
    db.session.commit()
    
    return jsonify({
        'msg': f'Rol actualizado exitosamente de {rol_anterior} a {nuevo_rol}',
        'usuario': usuario.to_dict(),
        'rol_anterior': rol_anterior,
        'rol_nuevo': nuevo_rol
    }), 200
