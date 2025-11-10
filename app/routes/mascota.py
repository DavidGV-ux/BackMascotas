from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Mascota, Usuario, HistorialMedico, Adopcion
from app.database import db
from app.services.s3_service import S3Service
from app.utils.decorators import admin_required

mascota_bp = Blueprint('mascotas', __name__)


@mascota_bp.route('', methods=['GET'])
@jwt_required()
def get_mascotas():
    """Lista mascotas según el rol del usuario"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    # Admin ve TODAS las mascotas
    if user.rol in ['ADMIN', 'ADMINISTRADOR']:
        query = Mascota.query
    # Veterinarios ven todas
    elif user.rol == 'VETERINARIO':
        query = Mascota.query
    # Clientes solo ven sus propias mascotas
    else:
        query = Mascota.query.filter_by(propietario_id=current_user_id)
    
    # Filtros opcionales
    especie = request.args.get('especie')
    disponible_adopcion = request.args.get('disponible_adopcion')
    
    if especie:
        query = query.filter_by(especie=especie)
    
    if disponible_adopcion:
        query = query.filter_by(disponible_adopcion=(disponible_adopcion == 'true'))
    
    mascotas = query.all()
    return jsonify([m.to_dict() for m in mascotas]), 200


@mascota_bp.route('/todas', methods=['GET'])
@jwt_required()
def listar_todas_mascotas():
    """Listar TODAS las mascotas (solo para veterinarios y admins)"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if user.rol not in ['VETERINARIO', 'ADMINISTRADOR', 'ADMIN']:
        return jsonify({'msg': 'Acceso denegado. Solo veterinarios y administradores'}), 403
    
    mascotas = Mascota.query.all()
    resultado = []
    
    for m in mascotas:
        mascota_dict = m.to_dict()
        propietario = Usuario.query.get(m.propietario_id)
        if propietario:
            mascota_dict['propietario'] = {
                'nombre': propietario.nombre
            }
        resultado.append(mascota_dict)
    
    return jsonify(resultado), 200


@mascota_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obtener_mascota(id):
    """Obtener detalle completo de una mascota"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    mascota = Mascota.query.get_or_404(id)
    mascota_dict = mascota.to_dict()
    
    # Agregar información del propietario
    propietario = Usuario.query.get(mascota.propietario_id)
    if propietario:
        mascota_dict['propietario'] = {
            'id': propietario.id,
            'nombre': propietario.nombre,
            'email': propietario.email,
            'telefono': propietario.telefono,
            'direccion': propietario.direccion
        }
    
    # Si es propietario, veterinario o admin → incluir historial médico resumido
    es_propietario = mascota.propietario_id == current_user_id
    es_veterinario = user.rol in ['VETERINARIO', 'ADMINISTRADOR', 'ADMIN']
    
    if es_propietario or es_veterinario:
        # Obtener últimas 5 consultas
        historial = HistorialMedico.query.filter_by(mascota_id=id)\
            .order_by(HistorialMedico.fecha_consulta.desc())\
            .limit(5).all()
        
        mascota_dict['historial_medico'] = []
        for h in historial:
            vet = Usuario.query.get(h.veterinario_id)
            mascota_dict['historial_medico'].append({
                'id': h.id,
                'fecha_consulta': h.fecha_consulta.isoformat() if h.fecha_consulta else None,
                'motivo_consulta': h.motivo_consulta,
                'diagnostico': h.diagnostico,
                'veterinario': {
                    'nombre': vet.nombre,
                    'email': vet.email
                } if vet else None
            })
        
        # Contar total de consultas
        total_consultas = HistorialMedico.query.filter_by(mascota_id=id).count()
        mascota_dict['total_consultas'] = total_consultas
    
    # Si es mascota en adopción y NO es el propietario
    if mascota.disponible_adopcion and not es_propietario:
        # Verificar si hay solicitud pendiente del usuario actual
        solicitud = Adopcion.query.filter_by(
            mascota_id=id,
            solicitante_id=current_user_id,
            estado='pendiente'
        ).first()
        mascota_dict['solicitud_pendiente'] = solicitud is not None
    
    mascota_dict['es_propietario'] = es_propietario
    mascota_dict['puede_ver_historial'] = es_propietario or es_veterinario
    
    return jsonify(mascota_dict), 200


@mascota_bp.route('', methods=['POST'])
@jwt_required()
def create_mascota():
    """Crear nueva mascota"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    data = request.get_json()
    
    if not data.get('nombre'):
        return jsonify({'msg': 'El nombre es requerido'}), 400
    
    # Si es admin y especifica propietario_id
    if user.rol in ['ADMIN', 'ADMINISTRADOR'] and 'propietario_id' in data:
        propietario_id = data['propietario_id']
        propietario = Usuario.query.get(propietario_id)
        if not propietario:
            return jsonify({'msg': 'Propietario no encontrado'}), 404
    else:
        propietario_id = current_user_id
    
    nueva_mascota = Mascota(
        nombre=data['nombre'],
        especie=data.get('especie'),
        raza=data.get('raza'),
        edad=data.get('edad'),
        peso=data.get('peso'),
        color=data.get('color'),
        descripcion=data.get('descripcion'),
        propietario_id=propietario_id,
        disponible_adopcion=data.get('disponible_adopcion', False)
    )
    
    db.session.add(nueva_mascota)
    db.session.commit()
    
    return jsonify({
        'msg': 'Mascota creada exitosamente',
        'mascota': nueva_mascota.to_dict()
    }), 201


@mascota_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_mascota(id):
    """Actualizar mascota"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    mascota = Mascota.query.get_or_404(id)
    
    # Admin puede editar CUALQUIER mascota
    if user.rol in ['ADMIN', 'ADMINISTRADOR']:
        pass
    # Cliente solo puede editar SUS PROPIAS mascotas
    elif user.rol == 'CLIENTE':
        if mascota.propietario_id != current_user_id:
            return jsonify({'msg': 'No autorizado'}), 403
    # Veterinario solo puede editar mascotas QUE ÉL CREÓ
    elif user.rol == 'VETERINARIO':
        if mascota.propietario_id != current_user_id:
            return jsonify({'msg': 'No autorizado'}), 403
    else:
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
    
    # Solo admin puede cambiar el propietario
    if user.rol in ['ADMIN', 'ADMINISTRADOR'] and 'propietario_id' in data:
        nuevo_propietario_id = data['propietario_id']
        propietario = Usuario.query.get(nuevo_propietario_id)
        if not propietario:
            return jsonify({'msg': 'Propietario no encontrado'}), 404
        mascota.propietario_id = nuevo_propietario_id
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Mascota actualizada exitosamente',
        'mascota': mascota.to_dict()
    }), 200


@mascota_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_mascota(id):
    """Eliminar mascota"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    mascota = Mascota.query.get_or_404(id)
    
    if user.rol in ['ADMIN', 'ADMINISTRADOR']:
        pass
    elif mascota.propietario_id != current_user_id:
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
    """Subir foto de mascota"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    mascota = Mascota.query.get_or_404(id)
    
    if user.rol in ['ADMIN', 'ADMINISTRADOR']:
        pass
    elif mascota.propietario_id != current_user_id:
        return jsonify({'msg': 'No autorizado'}), 403
    
    if 'foto' not in request.files:
        return jsonify({'msg': 'No se encontró el archivo'}), 400
    
    file = request.files['foto']
    
    if file.filename == '':
        return jsonify({'msg': 'No se seleccionó ningún archivo'}), 400
    
    # Validar tipo de archivo
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
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


@mascota_bp.route('/<int:id>/asignar', methods=['PUT'])
@jwt_required()
@admin_required
def asignar_mascota(id):
    """Admin asigna una mascota a un cliente específico"""
    mascota = Mascota.query.get_or_404(id)
    data = request.get_json()
    
    nuevo_propietario_id = data.get('propietario_id')
    if not nuevo_propietario_id:
        return jsonify({'msg': 'propietario_id es requerido'}), 400
    
    nuevo_propietario = Usuario.query.get(nuevo_propietario_id)
    if not nuevo_propietario:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    if nuevo_propietario.rol != 'CLIENTE':
        return jsonify({'msg': 'Solo se puede asignar a clientes'}), 400
    
    mascota.propietario_id = nuevo_propietario_id
    db.session.commit()
    
    return jsonify({
        'msg': f'Mascota asignada a {nuevo_propietario.nombre}',
        'mascota': mascota.to_dict()
    }), 200
