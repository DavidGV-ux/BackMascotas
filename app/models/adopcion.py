from app.database import db
from datetime import datetime


class Adopcion(db.Model):
    __tablename__ = 'adopciones'
    
    id = db.Column(db.Integer, primary_key=True)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pendiente')
    comentarios = db.Column(db.Text)
    fecha_aprobacion = db.Column(db.DateTime)
    administrador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Relaciones bidireccionales
    mascota = db.relationship('Mascota', back_populates='adopciones')
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], back_populates='solicitudes_adopcion')
    administrador = db.relationship('Usuario', foreign_keys=[administrador_id], back_populates='adopciones_gestionadas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'mascota_id': self.mascota_id,
            'solicitante_id': self.solicitante_id,
            'fecha_solicitud': self.fecha_solicitud.isoformat() if self.fecha_solicitud else None,
            'estado': self.estado,
            'comentarios': self.comentarios,
            'fecha_aprobacion': self.fecha_aprobacion.isoformat() if self.fecha_aprobacion else None,
            'administrador_id': self.administrador_id
        }
