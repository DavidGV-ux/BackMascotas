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
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    user = Usuario.query.get(current_user_id)
    
    # Filtros opcionales
    estado = request.args.get('estado')
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    # Admin ve todas las citas, cliente solo las suyas
    if user.rol == 'ADMIN':
        query = Cita.query
    else:
        query = Cita.query.filter_by(cliente_id=current_user_id)
    
    # Aplicar filtros
    if estado:
        query = query.filter_by(estado=estado)
    
    if fecha_desde:
        query = query.filter(Cita.fecha_hora >= datetime.fromisoformat(fecha_desde))
    
    if fecha_hasta:
        query = query.filter(Cita.fecha_hora <= datetime.fromisoformat(fecha_hasta))
    
    citas = query.order_by(Cita.fecha_hora.desc()).all()
    
    # Enriquecer con datos de mascota
    resultado = []
    for c in citas:
        cita_dict = c.to_dict()
        cita_dict['mascota'] = Mascota.query.get(c.mascota_id).to_dict()
        resultado.append(cita_dict)
    
    return jsonify(resultado), 200

@cita_bp.route('', methods=['POST'])
@jwt_required()
def crear_cita():
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    data = request.get_json()
    
    # Validaciones
    if not data.get('mascota_id') or not data.get('fecha_hora'):
        return jsonify({'msg': 'Mascota ID y fecha/hora son requeridos'}), 400
    
    # Verificar que la mascota pertenece al usuario
    mascota = Mascota.query.get_or_404(data['mascota_id'])
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
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    user = Usuario.query.get(current_user_id)
    cita = Cita.query.get_or_404(id)
    
    # Verificar permisos
    if cita.cliente_id != current_user_id and user.rol != 'ADMIN':
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
    if user.rol == 'ADMIN' and 'estado' in data:
        cita.estado = data['estado']
    
    # Solo admin puede asignar veterinario
    if user.rol == 'ADMIN' and 'veterinario_id' in data:
        cita.veterinario_id = data['veterinario_id']
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Cita actualizada exitosamente',
        'cita': cita.to_dict()
    }), 200

@cita_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def cancelar_cita(id):
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    user = Usuario.query.get(current_user_id)
    cita = Cita.query.get_or_404(id)
    
    # Verificar permisos
    if cita.cliente_id != current_user_id and user.rol != 'ADMIN':
        return jsonify({'msg': 'No autorizado'}), 403
    
    cita.estado = 'cancelada'
    db.session.commit()
    
    return jsonify({'msg': 'Cita cancelada exitosamente'}), 200

@cita_bp.route('/calendario', methods=['GET'])
@jwt_required()
def calendario_citas():
    current_user_id = int(get_jwt_identity())  # ✅ Corregido
    user = Usuario.query.get(current_user_id)
    
    # Obtener rango de fechas
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    # Admin ve todas, cliente solo las suyas
    if user.rol == 'ADMIN':
        query = Cita.query
    else:
        query = Cita.query.filter_by(cliente_id=current_user_id)
    
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
        eventos.append({
            'id': c.id,
            'title': f'{mascota.nombre} - {c.motivo or "Consulta"}',
            'start': c.fecha_hora.isoformat(),
            'backgroundColor': '#3788d8' if c.estado == 'confirmada' else '#ffa500',
            'borderColor': '#3788d8' if c.estado == 'confirmada' else '#ffa500',
            'extendedProps': {
                'mascota': mascota.nombre,
                'estado': c.estado,
                'motivo': c.motivo
            }
        })
    
    return jsonify(eventos), 200
