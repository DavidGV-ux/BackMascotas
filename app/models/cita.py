# app/models/cita.py
from app.database import db
from datetime import datetime

class Cita(db.Model):
    __tablename__ = 'citas'
    
    id = db.Column(db.Integer, primary_key=True)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    veterinario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_hora = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, confirmada, cancelada, completada
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    mascota = db.relationship('Mascota', back_populates='citas')
    cliente = db.relationship('Usuario', foreign_keys=[cliente_id], back_populates='citas')
    veterinario = db.relationship('Usuario', foreign_keys=[veterinario_id], back_populates='citas_veterinario')
    # Agregar en la clase Cita:
    historial = db.relationship('HistorialMedico', back_populates='cita', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'mascota_id': self.mascota_id,
            'cliente_id': self.cliente_id,
            'veterinario_id': self.veterinario_id,
            'fecha_hora': self.fecha_hora.isoformat() if self.fecha_hora else None,
            'motivo': self.motivo,
            'estado': self.estado,
            'observaciones': self.observaciones,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
