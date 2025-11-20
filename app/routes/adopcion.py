from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.adopcion import Adopcion
from app.models.mascota import Mascota
from app.models.usuario import Usuario
from app.database import db
from io import BytesIO
from app.utils.decorators import admin_required

# Importación lazy de reportlab para evitar errores si Pillow no está disponible
# NO importar aquí - hacerlo dentro de las funciones que lo necesitan

adopcion_bp = Blueprint('adopciones', __name__)

# ================== RUTAS PÚBLICAS (AUTENTICADAS) ==================

@adopcion_bp.route('/disponibles', methods=['GET'])
@jwt_required()
def mascotas_disponibles():
    """Lista todas las mascotas disponibles para adopción"""
    mascotas = Mascota.query.filter_by(disponible_adopcion=True).all()
    
    resultado = []
    for m in mascotas:
        mascota_dict = m.to_dict()
        
        # Agregar información del propietario
        propietario = Usuario.query.get(m.propietario_id)
        if propietario:
            mascota_dict['propietario'] = {
                'id': propietario.id,
                'nombre': propietario.nombre,
                'telefono': propietario.telefono,
                'email': propietario.email,
                'direccion': propietario.direccion
            }
        
        # Verificar si el usuario ya solicitó esta mascota
        current_user_id = int(get_jwt_identity())
        solicitud_existente = Adopcion.query.filter_by(
            mascota_id=m.id,
            solicitante_id=current_user_id,
            estado='pendiente'
        ).first()
        
        mascota_dict['solicitud_pendiente'] = solicitud_existente is not None
        
        resultado.append(mascota_dict)
    
    return jsonify(resultado), 200


@adopcion_bp.route('/solicitar', methods=['POST'])
@jwt_required()
def solicitar_adopcion():
    """Enviar solicitud de adopción"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    mascota_id = data.get('mascota_id')
    
    if not mascota_id:
        return jsonify({'msg': 'ID de mascota es requerido'}), 400
    
    mascota = Mascota.query.get_or_404(mascota_id)
    
    # Verificar que la mascota esté disponible
    if not mascota.disponible_adopcion:
        return jsonify({'msg': 'Esta mascota no está disponible para adopción'}), 400
    
    # No permitir adoptar propia mascota
    if mascota.propietario_id == current_user_id:
        return jsonify({'msg': 'No puedes solicitar adoptar tu propia mascota'}), 400
    
    # Verificar solicitud existente pendiente
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
        'msg': 'Solicitud de adopción enviada exitosamente',
        'solicitud': nueva_solicitud.to_dict()
    }), 201


@adopcion_bp.route('/mis-solicitudes', methods=['GET'])
@jwt_required()
def mis_solicitudes():
    """Ver solicitudes que YO envié"""
    current_user_id = int(get_jwt_identity())
    
    solicitudes = Adopcion.query.filter_by(solicitante_id=current_user_id).order_by(Adopcion.fecha_solicitud.desc()).all()
    
    resultado = []
    for s in solicitudes:
        solicitud_dict = s.to_dict()
        
        # Agregar info de la mascota
        mascota = Mascota.query.get(s.mascota_id)
        if mascota:
            solicitud_dict['mascota'] = mascota.to_dict()
            
            # Agregar propietario de la mascota
            propietario = Usuario.query.get(mascota.propietario_id)
            if propietario:
                solicitud_dict['propietario_mascota'] = {
                    'id': propietario.id,
                    'nombre': propietario.nombre,
                    'email': propietario.email
                }
        
        resultado.append(solicitud_dict)
    
    return jsonify(resultado), 200


@adopcion_bp.route('/solicitudes-recibidas', methods=['GET'])
@jwt_required()
def solicitudes_recibidas():
    """Ver solicitudes de adopción para MIS mascotas"""
    current_user_id = int(get_jwt_identity())
    
    # Obtener mis mascotas
    mis_mascotas = Mascota.query.filter_by(propietario_id=current_user_id).all()
    mascota_ids = [m.id for m in mis_mascotas]
    
    if not mascota_ids:
        return jsonify([]), 200
    
    # Obtener solicitudes para mis mascotas
    solicitudes = Adopcion.query.filter(Adopcion.mascota_id.in_(mascota_ids)).order_by(Adopcion.fecha_solicitud.desc()).all()
    
    resultado = []
    for s in solicitudes:
        solicitud_dict = s.to_dict()
        
        # Agregar info de la mascota
        mascota = Mascota.query.get(s.mascota_id)
        if mascota:
            solicitud_dict['mascota'] = mascota.to_dict()
        
        # Agregar info del solicitante
        solicitante = Usuario.query.get(s.solicitante_id)
        if solicitante:
            solicitud_dict['solicitante'] = {
                'id': solicitante.id,
                'nombre': solicitante.nombre,
                'email': solicitante.email,
                'telefono': solicitante.telefono
            }
        
        resultado.append(solicitud_dict)
    
    return jsonify(resultado), 200


@adopcion_bp.route('/<int:id>/responder', methods=['PUT'])
@jwt_required()
def responder_solicitud(id):
    """Propietario aprueba/rechaza solicitud para SU mascota"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    solicitud = Adopcion.query.get_or_404(id)
    mascota = Mascota.query.get(solicitud.mascota_id)
    
    # Verificar permisos: Solo propietario de la mascota o admin
    if mascota.propietario_id != current_user_id and user.rol not in ['ADMIN', 'ADMINISTRADOR']:
        return jsonify({'msg': 'No autorizado. Solo el propietario puede responder solicitudes'}), 403
    
    data = request.get_json()
    nuevo_estado = data.get('estado')  # 'aprobada' o 'rechazada'
    
    if nuevo_estado not in ['aprobada', 'rechazada']:
        return jsonify({'msg': 'Estado inválido. Debe ser aprobada o rechazada'}), 400
    
    solicitud.estado = nuevo_estado
    solicitud.fecha_respuesta = datetime.utcnow()
    solicitud.respuesta_admin = data.get('respuesta')
    
    # Si se aprueba, marcar mascota como no disponible
    if nuevo_estado == 'aprobada':
        mascota.disponible_adopcion = False
        
        # Rechazar automáticamente otras solicitudes pendientes
        otras_solicitudes = Adopcion.query.filter(
            Adopcion.mascota_id == solicitud.mascota_id,
            Adopcion.id != solicitud.id,
            Adopcion.estado == 'pendiente'
        ).all()
        
        for otra in otras_solicitudes:
            otra.estado = 'rechazada'
            otra.fecha_respuesta = datetime.utcnow()
            otra.respuesta_admin = 'Solicitud rechazada automáticamente (mascota ya adoptada)'
    
    db.session.commit()
    
    return jsonify({
        'msg': f'Solicitud {nuevo_estado} exitosamente',
        'solicitud': solicitud.to_dict()
    }), 200


@adopcion_bp.route('/<int:id>/cancelar', methods=['PUT'])
@jwt_required()
def cancelar_solicitud(id):
    """Solicitante cancela su propia solicitud pendiente"""
    current_user_id = int(get_jwt_identity())
    
    solicitud = Adopcion.query.get_or_404(id)
    
    # Verificar que sea el solicitante
    if solicitud.solicitante_id != current_user_id:
        return jsonify({'msg': 'No autorizado. Solo puedes cancelar tus propias solicitudes'}), 403
    
    # Solo se puede cancelar si está pendiente
    if solicitud.estado != 'pendiente':
        return jsonify({'msg': f'No se puede cancelar una solicitud {solicitud.estado}'}), 400
    
    solicitud.estado = 'cancelada'
    solicitud.fecha_respuesta = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Solicitud cancelada exitosamente',
        'solicitud': solicitud.to_dict()
    }), 200


# ================== RUTAS ADMIN ==================

@adopcion_bp.route('/todas', methods=['GET'])
@jwt_required()
@admin_required
def todas_las_solicitudes():
    """Admin ve TODAS las solicitudes"""
    estado = request.args.get('estado')  # Filtro opcional
    
    query = Adopcion.query
    
    if estado:
        query = query.filter_by(estado=estado)
    
    solicitudes = query.order_by(Adopcion.fecha_solicitud.desc()).all()
    
    resultado = []
    for s in solicitudes:
        solicitud_dict = s.to_dict()
        
        # Agregar info completa
        mascota = Mascota.query.get(s.mascota_id)
        if mascota:
            solicitud_dict['mascota'] = mascota.to_dict()
            
            propietario = Usuario.query.get(mascota.propietario_id)
            if propietario:
                solicitud_dict['propietario_mascota'] = {
                    'id': propietario.id,
                    'nombre': propietario.nombre,
                    'email': propietario.email
                }
        
        solicitante = Usuario.query.get(s.solicitante_id)
        if solicitante:
            solicitud_dict['solicitante'] = {
                'id': solicitante.id,
                'nombre': solicitante.nombre,
                'email': solicitante.email,
                'telefono': solicitante.telefono
            }
        
        resultado.append(solicitud_dict)
    
    return jsonify(resultado), 200


@adopcion_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required
def eliminar_solicitud(id):
    """Admin elimina una solicitud"""
    solicitud = Adopcion.query.get_or_404(id)
    
    db.session.delete(solicitud)
    db.session.commit()
    
    return jsonify({'msg': 'Solicitud eliminada exitosamente'}), 200


@adopcion_bp.route('/pendientes', methods=['GET'])
@jwt_required()
@admin_required
def adopciones_pendientes():
    """Lista todas las solicitudes pendientes (para admin)"""
    solicitudes = Adopcion.query.filter_by(estado='pendiente').order_by(Adopcion.fecha_solicitud.desc()).all()
    
    resultado = []
    for s in solicitudes:
        solicitud_dict = s.to_dict()
        
        mascota = Mascota.query.get(s.mascota_id)
        solicitud_dict['mascota'] = mascota.to_dict() if mascota else None
        
        solicitante = Usuario.query.get(s.solicitante_id)
        if solicitante:
            solicitud_dict['solicitante'] = {
                'id': solicitante.id,
                'nombre': solicitante.nombre,
                'email': solicitante.email,
                'telefono': solicitante.telefono
            }
        
        resultado.append(solicitud_dict)
    
    return jsonify(resultado), 200


@adopcion_bp.route('/<int:id>/revisar', methods=['PUT'])
@jwt_required()
@admin_required
def revisar_adopcion(id):
    """Admin aprueba/rechaza solicitud"""
    current_user_id = int(get_jwt_identity())
    solicitud = Adopcion.query.get_or_404(id)
    
    data = request.get_json()
    nuevo_estado = data.get('estado')
    
    if nuevo_estado not in ['aprobada', 'rechazada']:
        return jsonify({'msg': 'Estado inválido'}), 400
    
    solicitud.estado = nuevo_estado
    solicitud.administrador_id = current_user_id
    solicitud.fecha_respuesta = datetime.utcnow()
    solicitud.respuesta_admin = data.get('respuesta')
    
    # Si se aprueba, marcar mascota como no disponible
    if nuevo_estado == 'aprobada':
        mascota = Mascota.query.get(solicitud.mascota_id)
        if mascota:
            mascota.disponible_adopcion = False
    
    db.session.commit()
    
    return jsonify({
        'msg': f'Solicitud {nuevo_estado} exitosamente',
        'solicitud': solicitud.to_dict()
    }), 200


# ================== GENERAR PDF ==================

@adopcion_bp.route('/pdf/<int:mascota_id>', methods=['GET'])
@jwt_required()
def generar_pdf(mascota_id):
    """Genera PDF con información de la mascota para adopción"""
    # Lazy import de reportlab para evitar errores si Pillow no está disponible
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except (ImportError, ModuleNotFoundError) as e:
        return jsonify({
            'msg': 'Error al generar PDF: reportlab no está disponible',
            'detalle': str(e)
        }), 503
    
    mascota = Mascota.query.get_or_404(mascota_id)
    propietario = Usuario.query.get(mascota.propietario_id)
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Título
    p.setFont("Helvetica-Bold", 24)
    p.drawString(100, height - 100, "🐾 Información de Adopción")
    
    # Información de la mascota
    y = height - 150
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, y, f"{mascota.nombre}")
    
    y -= 30
    p.setFont("Helvetica", 12)
    info = [
        f"Especie: {mascota.especie or 'No especificada'}",
        f"Raza: {mascota.raza or 'No especificada'}",
        f"Edad: {mascota.edad or 'No especificada'} años",
        f"Peso: {mascota.peso or 'No especificado'} kg",
        f"Color: {mascota.color or 'No especificado'}",
        "",
        "Descripción:",
        f"{mascota.descripcion or 'Sin descripción'}",
        "",
        "Contacto del Propietario:",
        f"Nombre: {propietario.nombre}",
        f"Teléfono: {propietario.telefono}",
        f"Email: {propietario.email}",
        f"Dirección: {propietario.direccion}"
    ]
    
    for line in info:
        p.drawString(100, y, line)
        y -= 20
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, 50, f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    p.drawString(100, 35, "Veterinaria Software - Sistema de Adopciones")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'adopcion_{mascota.nombre}.pdf',
        mimetype='application/pdf'
    )

@adopcion_bp.route('/<int:solicitud_id>/transferir', methods=['PUT'])
@jwt_required()
def transferir_mascota(solicitud_id):
    """
    Transferir mascota al adoptante (solo propietario o admin)
    """
    current_user_id = int(get_jwt_identity())
    current_user = Usuario.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    # Buscar solicitud
    solicitud = Adopcion.query.get(solicitud_id)
    
    if not solicitud:
        return jsonify({'msg': 'Solicitud no encontrada'}), 404
    
    # Verificar que la solicitud esté aprobada
    if solicitud.estado != 'aprobada':
        return jsonify({'msg': 'Solo se pueden transferir mascotas de solicitudes aprobadas'}), 400
    
    # Verificar que no se haya transferido ya
    if solicitud.mascota_transferida:
        return jsonify({'msg': 'Esta mascota ya fue transferida'}), 400
    
    # Obtener mascota
    mascota = Mascota.query.get(solicitud.mascota_id)
    
    if not mascota:
        return jsonify({'msg': 'Mascota no encontrada'}), 404
    
    # Verificar permisos: solo el propietario o admin pueden transferir
    es_propietario = mascota.propietario_id == current_user_id
    es_admin = current_user.rol in ['ADMIN', 'ADMINISTRADOR']
    
    if not (es_propietario or es_admin):
        return jsonify({'msg': 'No tienes permisos para transferir esta mascota'}), 403
    
    try:
        # Transferir mascota al adoptante
        antiguo_propietario_id = mascota.propietario_id
        mascota.propietario_id = solicitud.solicitante_id
        
        # Cambiar estado de adopción a False
        mascota.en_adopcion = False
        
        # Marcar solicitud como transferida
        solicitud.mascota_transferida = True
        solicitud.fecha_transferencia = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'msg': 'Mascota transferida exitosamente',
            'solicitud': solicitud.to_dict(),
            'mascota': mascota.to_dict(),
            'antiguo_propietario_id': antiguo_propietario_id,
            'nuevo_propietario_id': mascota.propietario_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Error al transferir mascota: {str(e)}'}), 500
