from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.usuario import Usuario


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = Usuario.query.get(current_user_id)
        
        if not user or user.rol != 'ADMIN':
            return jsonify({'msg': 'Acceso denegado. Se requiere rol de administrador'}), 403
        
        return fn(*args, **kwargs)
    return wrapper


def cliente_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = Usuario.query.get(current_user_id)
        
        if not user or user.rol != 'CLIENTE':
            return jsonify({'msg': 'Acceso denegado. Se requiere rol de cliente'}), 403
        
        return fn(*args, **kwargs)
    return wrapper
