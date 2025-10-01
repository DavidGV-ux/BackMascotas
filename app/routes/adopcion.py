from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.adopcion import Adopcion
from app.models.mascota import Mascota
from app.models.usuario import Usuario
from app.database import db
from app.utils.decorators import admin_required
from app.services.email_service import EmailService

adopcion_bp = Blueprint('adopciones', __name__)

@adopcion_bp.route('/disponibles', methods=['GET'])
def mascotas_disponibles():
    mascotas = Mascota.query.filter_by(disponible_adopcion=True).all()
    return jsonify([m.to_dict() for m in mascotas]), 200

@adopcion_bp.route('/solicitar', methods=['POST'])
@jwt_required()
def solicitar_adopcion():
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    data = request.get_json()
    
    mascota_id = data.get('mascota_id')
    if not mascota_id:
        return jsonify({'msg': 'ID de mascota es requerido'}), 400
    
    # Verificar que la mascota existe y está disponible
    mascota = Mascota.query.get_or_404(mascota_id)
    if not mascota.disponible_adopcion:
        return jsonify({'msg': 'Esta mascota no está disponible para adopción'}), 400
    
    # Verificar que no exista una solicitud previa
    solicitud_existente = Adopcion.query.filter_by(
        mascota_id=mascota_id,
        solicitante_id=current_user_id,
        estado='pendiente'
    ).first()
    
    if solicitud_existente:
        return jsonify({'msg': 'Ya tienes una solicitud pendiente para esta mascota'}), 400
    
    # Crear solicitud
    nueva_solicitud = Adopcion(
        mascota_id=mascota_id,
        solicitante_id=current_user_id,
        comentarios=data.get('comentarios')
    )
    
    db.session.add(nueva_solicitud)
    db.session.commit()
    
    return jsonify({
        'msg': 'Solicitud de adopción creada exitosamente',
        'solicitud': nueva_solicitud.to_dict()
    }), 201

@adopcion_bp.route('/solicitudes', methods=['GET'])
@jwt_required()
@admin_required
def listar_solicitudes():
    estado = request.args.get('estado')
    
    query = Adopcion.query
    if estado:
        query = query.filter_by(estado=estado)
    
    solicitudes = query.all()
    
    # Enriquecer con datos de mascota y solicitante
    resultado = []
    for s in solicitudes:
        solicitud_dict = s.to_dict()
        solicitud_dict['mascota'] = Mascota.query.get(s.mascota_id).to_dict()
        solicitud_dict['solicitante'] = Usuario.query.get(s.solicitante_id).to_dict()
        resultado.append(solicitud_dict)
    
    return jsonify(resultado), 200

@adopcion_bp.route('/<int:id>/aprobar', methods=['PUT'])
@jwt_required()
@admin_required
def aprobar_adopcion(id):
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    adopcion = Adopcion.query.get_or_404(id)
    
    data = request.get_json()
    accion = data.get('accion')  # 'aprobar' o 'rechazar'
    
    if accion not in ['aprobar', 'rechazar']:
        return jsonify({'msg': 'Acción inválida'}), 400
    
    if accion == 'aprobar':
        adopcion.estado = 'aprobado'
        adopcion.fecha_aprobacion = datetime.utcnow()
        adopcion.administrador_id = current_user_id
        
        # Marcar mascota como no disponible
        mascota = Mascota.query.get(adopcion.mascota_id)
        mascota.disponible_adopcion = False
        
        # Rechazar otras solicitudes pendientes para esta mascota
        otras_solicitudes = Adopcion.query.filter_by(
            mascota_id=adopcion.mascota_id,
            estado='pendiente'
        ).filter(Adopcion.id != id).all()
        
        for otra in otras_solicitudes:
            otra.estado = 'rechazado'
    else:
        adopcion.estado = 'rechazado'
        adopcion.administrador_id = current_user_id
    
    db.session.commit()
    
    # Enviar notificación por email
    solicitante = Usuario.query.get(adopcion.solicitante_id)
    mascota = Mascota.query.get(adopcion.mascota_id)
    email_service = EmailService()
    email_service.send_adoption_notification(
        solicitante.email,
        mascota.nombre,
        adopcion.estado
    )
    
    return jsonify({
        'msg': f'Solicitud {adopcion.estado} exitosamente',
        'adopcion': adopcion.to_dict()
    }), 200

@adopcion_bp.route('/mis-solicitudes', methods=['GET'])
@jwt_required()
def mis_solicitudes():
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    solicitudes = Adopcion.query.filter_by(solicitante_id=current_user_id).all()
    
    # Enriquecer con datos de mascota
    resultado = []
    for s in solicitudes:
        solicitud_dict = s.to_dict()
        solicitud_dict['mascota'] = Mascota.query.get(s.mascota_id).to_dict()
        resultado.append(solicitud_dict)
    
    return jsonify(resultado), 200
