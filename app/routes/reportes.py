# app/routes/reportes.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.mascota import Mascota
from app.models.cita import Cita
from app.models.adopcion import Adopcion
from app.models.usuario import Usuario
from app.database import db
from app.utils.decorators import admin_required

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
@admin_required
def estadisticas_generales():
    """Dashboard con estadísticas generales"""
    
    # Contar totales
    total_mascotas = Mascota.query.count()
    total_clientes = Usuario.query.filter_by(rol='CLIENTE').count()
    total_veterinarios = Usuario.query.filter_by(rol='VETERINARIO').count()
    total_citas = Cita.query.count()
    citas_pendientes = Cita.query.filter_by(estado='pendiente').count()
    citas_completadas = Cita.query.filter_by(estado='completada').count()
    
    # Adopciones
    total_adopciones = Adopcion.query.count()
    adopciones_pendientes = Adopcion.query.filter_by(estado='pendiente').count()
    adopciones_aprobadas = Adopcion.query.filter_by(estado='aprobada').count()
    
    # Mascotas por especie
    mascotas_por_especie = db.session.query(
        Mascota.especie, 
        db.func.count(Mascota.id)
    ).group_by(Mascota.especie).all()
    
    return jsonify({
        'usuarios': {
            'clientes': total_clientes,
            'veterinarios': total_veterinarios,
            'total': total_clientes + total_veterinarios
        },
        'mascotas': {
            'total': total_mascotas,
            'por_especie': [{'especie': e, 'cantidad': c} for e, c in mascotas_por_especie]
        },
        'citas': {
            'total': total_citas,
            'pendientes': citas_pendientes,
            'completadas': citas_completadas
        },
        'adopciones': {
            'total': total_adopciones,
            'pendientes': adopciones_pendientes,
            'aprobadas': adopciones_aprobadas
        }
    }), 200


@reportes_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def dashboard():
    """Datos para el dashboard del administrador"""
    return estadisticas_generales()
