# app/routes/historial.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.models.historial_medico import HistorialMedico
from app.models.mascota import Mascota
from app.models.usuario import Usuario
from app.models.cita import Cita
from app.database import db
from app.utils.decorators import admin_required

historial_bp = Blueprint('historial', __name__)

# Crear nueva consulta (solo veterinarios y admins)
@historial_bp.route('', methods=['POST'])
@jwt_required()
def crear_consulta():
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    # Solo veterinarios y administradores pueden crear consultas
    if user.rol not in ['VETERINARIO', 'ADMINISTRADOR']:
        return jsonify({'msg': 'Acceso denegado. Solo veterinarios pueden registrar consultas'}), 403
    
    data = request.get_json()
    
    if not data.get('mascota_id') or not data.get('motivo_consulta'):
        return jsonify({'msg': 'Mascota ID y motivo de consulta son requeridos'}), 400
    
    # Verificar que la mascota existe
    mascota = Mascota.query.get_or_404(data['mascota_id'])
    
    # Crear registro de historial
    nuevo_historial = HistorialMedico(
        mascota_id=data['mascota_id'],
        veterinario_id=current_user_id,
        cita_id=data.get('cita_id'),
        peso_actual=data.get('peso_actual'),
        temperatura=data.get('temperatura'),
        frecuencia_cardiaca=data.get('frecuencia_cardiaca'),
        frecuencia_respiratoria=data.get('frecuencia_respiratoria'),
        motivo_consulta=data['motivo_consulta'],
        diagnostico=data.get('diagnostico'),
        observaciones=data.get('observaciones'),
        vacunas_aplicadas=data.get('vacunas_aplicadas', False),
        vacunas_detalle=data.get('vacunas_detalle'),
        desparasitacion=data.get('desparasitacion', False),
        desparasitacion_detalle=data.get('desparasitacion_detalle'),
        cirugia=data.get('cirugia', False),
        cirugia_detalle=data.get('cirugia_detalle'),
        hospitalizacion=data.get('hospitalizacion', False),
        heridas_fisicas=data.get('heridas_fisicas', False),
        heridas_detalle=data.get('heridas_detalle'),
        enfermedades_detectadas=data.get('enfermedades_detectadas', False),
        enfermedades_detalle=data.get('enfermedades_detalle'),
        tratamiento_prescrito=data.get('tratamiento_prescrito'),
        medicamentos=data.get('medicamentos'),
        proxima_visita=datetime.fromisoformat(data['proxima_visita']) if data.get('proxima_visita') else None
    )
    
    db.session.add(nuevo_historial)
    
    # Si está asociado a una cita, marcar la cita como completada
    if data.get('cita_id'):
        cita = Cita.query.get(data['cita_id'])
        if cita:
            cita.estado = 'completada'
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Consulta registrada exitosamente',
        'historial': nuevo_historial.to_dict()
    }), 201


# Obtener historial completo de una mascota
@historial_bp.route('/mascota/<int:mascota_id>', methods=['GET'])
@jwt_required()
def ver_historial_mascota(mascota_id):
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    mascota = Mascota.query.get_or_404(mascota_id)
    
    # Solo el propietario, veterinarios y admins pueden ver el historial
    if user.rol == 'CLIENTE' and mascota.propietario_id != current_user_id:
        return jsonify({'msg': 'No autorizado'}), 403
    
    historial = HistorialMedico.query.filter_by(mascota_id=mascota_id).order_by(HistorialMedico.fecha_consulta.desc()).all()
    
    resultado = []
    for h in historial:
        historial_dict = h.to_dict()
        veterinario = Usuario.query.get(h.veterinario_id)
        historial_dict['veterinario'] = {
            'nombre': veterinario.nombre,
            'email': veterinario.email
        }
        resultado.append(historial_dict)
    
    return jsonify(resultado), 200


# Obtener consulta específica
@historial_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obtener_consulta(id):
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    historial = HistorialMedico.query.get_or_404(id)
    mascota = Mascota.query.get(historial.mascota_id)
    
    # Verificar permisos
    if user.rol == 'CLIENTE' and mascota.propietario_id != current_user_id:
        return jsonify({'msg': 'No autorizado'}), 403
    
    historial_dict = historial.to_dict()
    veterinario = Usuario.query.get(historial.veterinario_id)
    historial_dict['veterinario'] = {
        'nombre': veterinario.nombre,
        'email': veterinario.email
    }
    historial_dict['mascota'] = mascota.to_dict()
    
    return jsonify(historial_dict), 200


# Actualizar consulta (solo veterinario que la creó o admin)
@historial_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def actualizar_consulta(id):
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    historial = HistorialMedico.query.get_or_404(id)
    
    # Solo el veterinario que creó la consulta o un admin pueden editarla
    if historial.veterinario_id != current_user_id and user.rol != 'ADMINISTRADOR':
        return jsonify({'msg': 'No autorizado'}), 403
    
    data = request.get_json()
    
    # Actualizar campos
    if 'peso_actual' in data:
        historial.peso_actual = data['peso_actual']
    if 'temperatura' in data:
        historial.temperatura = data['temperatura']
    if 'frecuencia_cardiaca' in data:
        historial.frecuencia_cardiaca = data['frecuencia_cardiaca']
    if 'frecuencia_respiratoria' in data:
        historial.frecuencia_respiratoria = data['frecuencia_respiratoria']
    if 'motivo_consulta' in data:
        historial.motivo_consulta = data['motivo_consulta']
    if 'diagnostico' in data:
        historial.diagnostico = data['diagnostico']
    if 'observaciones' in data:
        historial.observaciones = data['observaciones']
    if 'vacunas_aplicadas' in data:
        historial.vacunas_aplicadas = data['vacunas_aplicadas']
    if 'vacunas_detalle' in data:
        historial.vacunas_detalle = data['vacunas_detalle']
    if 'desparasitacion' in data:
        historial.desparasitacion = data['desparasitacion']
    if 'desparasitacion_detalle' in data:
        historial.desparasitacion_detalle = data['desparasitacion_detalle']
    if 'cirugia' in data:
        historial.cirugia = data['cirugia']
    if 'cirugia_detalle' in data:
        historial.cirugia_detalle = data['cirugia_detalle']
    if 'hospitalizacion' in data:
        historial.hospitalizacion = data['hospitalizacion']
    if 'heridas_fisicas' in data:
        historial.heridas_fisicas = data['heridas_fisicas']
    if 'heridas_detalle' in data:
        historial.heridas_detalle = data['heridas_detalle']
    if 'enfermedades_detectadas' in data:
        historial.enfermedades_detectadas = data['enfermedades_detectadas']
    if 'enfermedades_detalle' in data:
        historial.enfermedades_detalle = data['enfermedades_detalle']
    if 'tratamiento_prescrito' in data:
        historial.tratamiento_prescrito = data['tratamiento_prescrito']
    if 'medicamentos' in data:
        historial.medicamentos = data['medicamentos']
    if 'proxima_visita' in data:
        historial.proxima_visita = datetime.fromisoformat(data['proxima_visita']) if data['proxima_visita'] else None
    
    db.session.commit()
    
    return jsonify({
        'msg': 'Consulta actualizada exitosamente',
        'historial': historial.to_dict()
    }), 200


# Listar consultas pendientes de completar (citas atendidas sin historial)
@historial_bp.route('/pendientes', methods=['GET'])
@jwt_required()
def consultas_pendientes():
    current_user_id = int(get_jwt_identity())
    user = Usuario.query.get(current_user_id)
    
    if user.rol not in ['VETERINARIO', 'ADMINISTRADOR']:
        return jsonify({'msg': 'Acceso denegado'}), 403
    
    # Buscar citas completadas sin historial médico
    citas = Cita.query.filter_by(estado='completada').filter(~Cita.historial.has()).all()
    
    resultado = []
    for c in citas:
        cita_dict = c.to_dict()
        mascota = Mascota.query.get(c.mascota_id)
        cita_dict['mascota'] = mascota.to_dict()
        resultado.append(cita_dict)
    
    return jsonify(resultado), 200
