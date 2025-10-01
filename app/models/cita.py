from app.database import db
from datetime import datetime


class Cita(db.Model):
    __tablename__ = 'citas'
    
    id = db.Column(db.Integer, primary_key=True)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    veterinario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_hora = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='pendiente')
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones bidireccionales
    mascota = db.relationship('Mascota', back_populates='citas')
    cliente = db.relationship('Usuario', foreign_keys=[cliente_id], back_populates='citas')
    veterinario = db.relationship('Usuario', foreign_keys=[veterinario_id], back_populates='citas_veterinario')
    
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
