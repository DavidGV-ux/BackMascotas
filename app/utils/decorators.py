from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.models.usuario import Usuario
from app.services.auth_service import AuthService

def admin_required(fn):
    """Decorator para requerir rol de administrador"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = Usuario.query.get(current_user_id)
        
        if not user or user.rol not in ['ADMIN', 'ADMINISTRADOR']:
            return jsonify({'msg': 'Acceso denegado. Se requiere rol de administrador'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def cliente_required(fn):
    """Decorator para requerir rol de cliente"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = Usuario.query.get(current_user_id)
        
        if not user or user.rol != 'CLIENTE':
            return jsonify({'msg': 'Acceso denegado. Se requiere rol de cliente'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def veterinario_required(fn):
    """Decorator para requerir rol de veterinario o administrador"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = Usuario.query.get(current_user_id)
        
        if not user or user.rol not in ['VETERINARIO', 'ADMINISTRADOR', 'ADMIN']:
            return jsonify({'msg': 'Acceso denegado. Se requiere rol de veterinario'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

def keycloak_required(fn):
    """Decorator para validar token de Keycloak"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'msg': 'Token requerido'}), 401
        
        token = auth_header.split(' ', 1)[1]
        try:
            kc = AuthService.get_keycloak_client()
            userinfo = kc.userinfo(token)
        except Exception:
            return jsonify({'msg': 'Token inválido o expirado'}), 401
        
        return fn(userinfo, *args, **kwargs)
    return wrapper
