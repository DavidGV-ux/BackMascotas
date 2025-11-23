from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.cita import Cita
from app.models.mascota import Mascota
from app.models.usuario import Usuario
from app.database import db
from app.utils.decorators import admin_required

cita_bp = Blueprint('citas', __name__)

@cita_bp.route('', methods=['GET'])
@jwt_required()
def listar_citas():
    """Lista citas según el rol del usuario"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    # Filtros opcionales
    estado = request.args.get('estado')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    # Admin y veterinarios ven TODAS las citas
    if user.rol in ['ADMIN', 'ADMINISTRADOR', 'VETERINARIO']:
        query = Cita.query
    else:
        # Clientes solo ven sus propias citas
        query = Cita.query.filter_by(cliente_id=current_user_id)
    
    # Aplicar filtros
    if estado:
        query = query.filter_by(estado=estado)
    
    if fecha_desde:
        query = query.filter(Cita.fecha_hora >= datetime.fromisoformat(fecha_desde))
    
    if fecha_hasta:
        query = query.filter(Cita.fecha_hora <= datetime.fromisoformat(fecha_hasta))
    
    citas = query.order_by(Cita.fecha_hora.desc()).all()
    
    # Enriquecer con datos de mascota y cliente
    resultado = []
    for c in citas:
        cita_dict = c.to_dict()
        
        mascota = Mascota.query.get(c.mascota_id)
        cita_dict['mascota'] = mascota.to_dict() if mascota else None
        
        cliente = Usuario.query.get(c.cliente_id)
        if cliente:
            cita_dict['cliente'] = {
                'id': cliente.id,
                'nombre': cliente.nombre,
                'email': cliente.email,
                'telefono': cliente.telefono
            }
        
        resultado.append(cita_dict)
    
    return jsonify(resultado), 200

@cita_bp.route('', methods=['POST'])
@jwt_required()
def crear_cita():
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # Validaciones
    if not data.get('mascota_id') or not data.get('fecha_hora'):
        return jsonify({'msg': 'Mascota ID y fecha/hora son requeridos'}), 400
    
    # Verificar que la mascota pertenece al usuario (excepto admin)
    user = Usuario.query.get(current_user_id)
    
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    mascota = Mascota.query.get_or_404(data['mascota_id'])
    
    if user.rol not in ['ADMIN', 'ADMINISTRADOR']:
        if mascota.propietario_id != current_user_id:
            return jsonify({'msg': 'No puedes crear citas para mascotas que no te pertenecen'}), 403
    
    # Crear cita
    nueva_cita = Cita(
        mascota_id=data['mascota_id'],
        cliente_id=current_user_id,
        fecha_hora=datetime.fromisoformat(data['fecha_hora']),
        motivo=data.get('motivo'),
        observaciones=data.get('observaciones')
    )
    
    db.session.add(nueva_cita)
    db.session.commit()
    
    return jsonify({
        'msg': 'Cita creada exitosamente',
        'cita': nueva_cita.to_dict()
    }), 201

@cita_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def actualizar_cita(id):
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    cita = Cita.query.get_or_404(id)
    
    # Verificar permisos
    if cita.cliente_id != current_user_id and user.rol not in ['ADMIN', 'ADMINISTRADOR']:
        return jsonify({'msg': 'No autorizado'}), 403
    
    data = request.get_json()
    
    # Actualizar campos permitidos
    if 'fecha_hora' in data:
        cita.fecha_hora = datetime.fromisoformat(data['fecha_hora'])
    
    if 'motivo' in data:
        cita.motivo = data['motivo']
    
    if 'observaciones' in data:
        cita.observaciones = data['observaciones']
    
    # Solo admin puede cambiar estado
    if user.rol in ['ADMIN', 'ADMINISTRADOR'] and 'estado' in data:
        cita.estado = data['estado']
    
    # Solo admin puede asignar veterinario
    if user.rol in ['ADMIN', 'ADMINISTRADOR'] and 'veterinario_id' in data:
        cita.veterinario_id = data['veterinario_id']
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Cita actualizada exitosamente',
        'cita': cita.to_dict()
    }), 200

@cita_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def cancelar_cita(id):
    """Cancelar cita - Clientes pueden cancelar sus propias citas, veterinarios las que aceptaron, admin todas"""
    try:
        current_user_id = int(get_jwt_identity())
        user = Usuario.query.get(current_user_id)
        
        if not user:
            return jsonify({'msg': 'Usuario no encontrado'}), 404
        
        cita = Cita.query.get_or_404(id)
        
        # Verificar permisos
        es_cliente = cita.cliente_id == current_user_id
        es_veterinario_asignado = cita.veterinario_id == current_user_id
        es_admin = user.rol in ['ADMIN', 'ADMINISTRADOR']
        es_veterinario = user.rol == 'VETERINARIO'
        
        # Clientes solo pueden cancelar sus propias citas
        # Veterinarios pueden cancelar citas que aceptaron (donde son el veterinario asignado)
        # Admin puede cancelar todas las citas
        if not (es_cliente or (es_veterinario_asignado and es_veterinario) or es_admin):
            return jsonify({
                'msg': 'No autorizado. Solo puedes cancelar tus propias citas o las citas que aceptaste como veterinario'
            }), 403
        
        # Verificar que la cita no esté ya completada o cancelada
        if cita.estado in ['completada', 'cancelada']:
            return jsonify({
                'msg': f'No se puede cancelar una cita que ya está {cita.estado}'
            }), 400
        
        cita.estado = 'cancelada'
        db.session.commit()
        
        return jsonify({'msg': 'Cita cancelada exitosamente'}), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'msg': 'Error al cancelar la cita',
            'error': str(e)
        }), 500

@cita_bp.route('/calendario', methods=['GET'])
@jwt_required()
def calendario_citas():
    """Obtiene todas las citas en formato calendario"""
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    # Verificar que sea admin o veterinario
    if user.rol not in ['ADMIN', 'ADMINISTRADOR', 'VETERINARIO']:
        return jsonify({'msg': 'Acceso denegado. Solo administradores y veterinarios pueden acceder al calendario'}), 403
    
    # Obtener rango de fechas
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = Cita.query
    
    # Filtrar por rango de fechas
    if fecha_desde:
        query = query.filter(Cita.fecha_hora >= datetime.fromisoformat(fecha_desde))
    
    if fecha_hasta:
        query = query.filter(Cita.fecha_hora <= datetime.fromisoformat(fecha_hasta))
    
    citas = query.all()
    
    # Formato para calendario (FullCalendar)
    eventos = []
    for c in citas:
        mascota = Mascota.query.get(c.mascota_id)
        cliente = Usuario.query.get(c.cliente_id)
        
        eventos.append({
            'id': c.id,
            'title': f'{mascota.nombre} - {c.motivo or "Consulta"}' if mascota else c.motivo or "Consulta",
            'start': c.fecha_hora.isoformat() if c.fecha_hora else None,
            'backgroundColor': '#3788d8' if c.estado == 'confirmada' else '#ffa500',
            'borderColor': '#3788d8' if c.estado == 'confirmada' else '#ffa500',
            'extendedProps': {
                'mascota': mascota.nombre if mascota else 'Sin mascota',
                'cliente': cliente.nombre if cliente else 'Sin cliente',
                'estado': c.estado,
                'motivo': c.motivo
            }
        })
    
    return jsonify(eventos), 200

@cita_bp.route('/<int:id>/aceptar', methods=['PUT'])
@jwt_required()
def aceptar_cita(id):
    """
    Aceptar cita (solo veterinarios, NO administradores)
    """
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    # Solo veterinarios pueden aceptar citas (admin NO puede)
    if user.rol != 'VETERINARIO':
        return jsonify({'msg': 'Acceso denegado. Solo veterinarios pueden aceptar citas'}), 403
    
    cita = Cita.query.get_or_404(id)
    
    # Verificar que la cita esté pendiente
    if cita.estado != 'pendiente':
        return jsonify({'msg': 'Solo se pueden aceptar citas pendientes'}), 400
    
    # Aceptar la cita
    cita.estado = 'confirmada'
    cita.veterinario_id = current_user_id  # Asignar veterinario
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Cita aceptada exitosamente',
        'cita': cita.to_dict()
    }), 200

@cita_bp.route('/<int:id>/completar', methods=['PUT'])
@jwt_required()
def completar_cita(id):
    """
    Completar cita (solo veterinarios, NO administradores)
    """
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if not user:
        return jsonify({'msg': 'Usuario no encontrado'}), 404
    
    # Solo veterinarios pueden completar citas (admin NO puede)
    if user.rol != 'VETERINARIO':
        return jsonify({'msg': 'Acceso denegado. Solo veterinarios pueden completar citas'}), 403
    
    cita = Cita.query.get_or_404(id)
    
    # Verificar que la cita esté confirmada o pendiente
    if cita.estado not in ['pendiente', 'confirmada']:
        return jsonify({'msg': 'Solo se pueden completar citas confirmadas o pendientes'}), 400
    
    # Verificar que el veterinario sea el asignado (si ya está asignado)
    if cita.veterinario_id and cita.veterinario_id != current_user_id:
        return jsonify({'msg': 'Esta cita está asignada a otro veterinario'}), 403
    
    # Asignar veterinario si no lo tiene
    if not cita.veterinario_id:
        cita.veterinario_id = current_user_id
    
    # Marcar como completada
    cita.estado = 'completada'
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Cita completada exitosamente',
        'cita': cita.to_dict()
    }), 200
