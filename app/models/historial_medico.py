# app/models/historial_medico.py
from app.database import db
from datetime import datetime

class HistorialMedico(db.Model):
    __tablename__ = 'historial_medico'
    
    id = db.Column(db.Integer, primary_key=True)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    veterinario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'))
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Información básica
    peso_actual = db.Column(db.Float)
    temperatura = db.Column(db.Float)
    frecuencia_cardiaca = db.Column(db.Integer)
    frecuencia_respiratoria = db.Column(db.Integer)
    
    # Motivo y diagnóstico
    motivo_consulta = db.Column(db.Text, nullable=False)
    diagnostico = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    
    # Checklist booleanos
    vacunas_aplicadas = db.Column(db.Boolean, default=False)
    desparasitacion = db.Column(db.Boolean, default=False)
    cirugia = db.Column(db.Boolean, default=False)
    hospitalizacion = db.Column(db.Boolean, default=False)
    heridas_fisicas = db.Column(db.Boolean, default=False)
    enfermedades_detectadas = db.Column(db.Boolean, default=False)
    
    # Detalles de checklist
    vacunas_detalle = db.Column(db.Text)
    desparasitacion_detalle = db.Column(db.String(200))
    cirugia_detalle = db.Column(db.Text)
    heridas_detalle = db.Column(db.Text)
    enfermedades_detalle = db.Column(db.Text)
    
    # Tratamiento y seguimiento
    tratamiento_prescrito = db.Column(db.Text)
    medicamentos = db.Column(db.Text)
    proxima_visita = db.Column(db.DateTime)
    
    # Relaciones
    mascota = db.relationship('Mascota', back_populates='historial_medico')
    veterinario = db.relationship('Usuario', foreign_keys=[veterinario_id])
    cita = db.relationship('Cita', back_populates='historial')
    
    def to_dict(self):
        return {
            'id': self.id,
            'mascota_id': self.mascota_id,
            'veterinario_id': self.veterinario_id,
            'cita_id': self.cita_id,
            'fecha_consulta': self.fecha_consulta.isoformat() if self.fecha_consulta else None,
            'peso_actual': self.peso_actual,
            'temperatura': self.temperatura,
            'frecuencia_cardiaca': self.frecuencia_cardiaca,
            'frecuencia_respiratoria': self.frecuencia_respiratoria,
            'motivo_consulta': self.motivo_consulta,
            'diagnostico': self.diagnostico,
            'observaciones': self.observaciones,
            'vacunas_aplicadas': self.vacunas_aplicadas,
            'vacunas_detalle': self.vacunas_detalle,
            'desparasitacion': self.desparasitacion,
            'desparasitacion_detalle': self.desparasitacion_detalle,
            'cirugia': self.cirugia,
            'cirugia_detalle': self.cirugia_detalle,
            'hospitalizacion': self.hospitalizacion,
            'heridas_fisicas': self.heridas_fisicas,
            'heridas_detalle': self.heridas_detalle,
            'enfermedades_detectadas': self.enfermedades_detectadas,
            'enfermedades_detalle': self.enfermedades_detalle,
            'tratamiento_prescrito': self.tratamiento_prescrito,
            'medicamentos': self.medicamentos,
            'proxima_visita': self.proxima_visita.isoformat() if self.proxima_visita else None
        }
