from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.mascota import Mascota
from app.models.usuario import Usuario
from app.database import db
from app.services.s3_service import S3Service
from app.utils.decorators import admin_required


mascota_bp = Blueprint('mascotas', __name__)


@mascota_bp.route('', methods=['GET'])
def get_mascotas():
    # Filtros opcionales
    especie = request.args.get('especie')
    disponible_adopcion = request.args.get('disponible_adopcion')
    
    query = Mascota.query
    
    if especie:
        query = query.filter_by(especie=especie)
    
    if disponible_adopcion:
        query = query.filter_by(disponible_adopcion=disponible_adopcion == 'true')
    
    mascotas = query.all()
    return jsonify([m.to_dict() for m in mascotas]), 200


@mascota_bp.route('', methods=['POST'])
@jwt_required()
def create_mascota():
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    data = request.get_json()
    
    if not data.get('nombre'):
        return jsonify({'msg': 'El nombre es requerido'}), 400
    
    nueva_mascota = Mascota(
        nombre=data['nombre'],
        especie=data.get('especie'),
        raza=data.get('raza'),
        edad=data.get('edad'),
        peso=data.get('peso'),
        color=data.get('color'),
        descripcion=data.get('descripcion'),
        propietario_id=current_user_id,
        disponible_adopcion=data.get('disponible_adopcion', False)
    )
    
    db.session.add(nueva_mascota)
    db.session.commit()
    
    return jsonify({
        'msg': 'Mascota creada exitosamente',
        'mascota': nueva_mascota.to_dict()
    }), 201


@mascota_bp.route('/<int:id>', methods=['GET'])
def get_mascota(id):
    mascota = Mascota.query.get_or_404(id)
    return jsonify(mascota.to_dict()), 200


@mascota_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_mascota(id):
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    mascota = Mascota.query.get_or_404(id)
    
    # Verificar permisos
    user = Usuario.query.get(current_user_id)
    if mascota.propietario_id != current_user_id and user.rol != 'ADMIN':
        return jsonify({'msg': 'No autorizado'}), 403
    
    data = request.get_json()
    
    # Actualizar campos
    mascota.nombre = data.get('nombre', mascota.nombre)
    mascota.especie = data.get('especie', mascota.especie)
    mascota.raza = data.get('raza', mascota.raza)
    mascota.edad = data.get('edad', mascota.edad)
    mascota.peso = data.get('peso', mascota.peso)
    mascota.color = data.get('color', mascota.color)
    mascota.descripcion = data.get('descripcion', mascota.descripcion)
    mascota.disponible_adopcion = data.get('disponible_adopcion', mascota.disponible_adopcion)
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Mascota actualizada exitosamente',
        'mascota': mascota.to_dict()
    }), 200


@mascota_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_mascota(id):
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    mascota = Mascota.query.get_or_404(id)
    
    # Verificar permisos
    user = Usuario.query.get(current_user_id)
    if mascota.propietario_id != current_user_id and user.rol != 'ADMIN':
        return jsonify({'msg': 'No autorizado'}), 403
    
    # Eliminar foto de S3 si existe
    if mascota.foto_url:
        s3_service = S3Service()
        s3_service.delete_file(mascota.foto_url)
    
    db.session.delete(mascota)
    db.session.commit()
    
    return jsonify({'msg': 'Mascota eliminada exitosamente'}), 200


@mascota_bp.route('/<int:id>/fotos', methods=['POST'])
@jwt_required()
def upload_foto(id):
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    mascota = Mascota.query.get_or_404(id)
    
    # Verificar permisos
    user = Usuario.query.get(current_user_id)
    if mascota.propietario_id != current_user_id and user.rol != 'ADMIN':
        return jsonify({'msg': 'No autorizado'}), 403
    
    if 'foto' not in request.files:
        return jsonify({'msg': 'No se encontró el archivo'}), 400
    
    file = request.files['foto']
    
    if file.filename == '':
        return jsonify({'msg': 'No se seleccionó ningún archivo'}), 400
    
    # Validar tipo de archivo
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'msg': 'Tipo de archivo no permitido'}), 400
    
    # Subir a S3
    s3_service = S3Service()
    foto_url = s3_service.upload_file(file, folder='mascotas')
    
    if not foto_url:
        return jsonify({'msg': 'Error al subir la foto'}), 500
    
    # Eliminar foto anterior si existe
    if mascota.foto_url:
        s3_service.delete_file(mascota.foto_url)
    
    mascota.foto_url = foto_url
    db.session.commit()
    
    return jsonify({
        'msg': 'Foto subida exitosamente',
        'foto_url': foto_url
    }), 200
