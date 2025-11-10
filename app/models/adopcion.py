from app.database import db
from datetime import datetime

class Adopcion(db.Model):
    __tablename__ = 'adopciones'
    
    id = db.Column(db.Integer, primary_key=True)
    mascota_id = db.Column(db.Integer, db.ForeignKey('mascotas.id'), nullable=False)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    administrador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, aprobada, rechazada, cancelada
    comentarios = db.Column(db.Text, nullable=True)
    respuesta_admin = db.Column(db.Text, nullable=True)
    
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_respuesta = db.Column(db.DateTime, nullable=True)
    
    # ✅ NUEVO: Campo para saber si la mascota fue transferida
    mascota_transferida = db.Column(db.Boolean, default=False)
    fecha_transferencia = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    mascota = db.relationship('Mascota', backref=db.backref('solicitudes_adopcion', overlaps="adopciones"))
    solicitante = db.relationship(
        'Usuario', 
        foreign_keys=[solicitante_id], 
        backref=db.backref('solicitudes_enviadas', overlaps="solicitudes_adopcion")
    )
    administrador = db.relationship(
        'Usuario', 
        foreign_keys=[administrador_id], 
        backref=db.backref('solicitudes_revisadas', overlaps="adopciones_gestionadas")
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'mascota_id': self.mascota_id,
            'solicitante_id': self.solicitante_id,
            'administrador_id': self.administrador_id,
            'estado': self.estado,
            'comentarios': self.comentarios,
            'respuesta_admin': self.respuesta_admin,
            'fecha_solicitud': self.fecha_solicitud.isoformat() if self.fecha_solicitud else None,
            'fecha_respuesta': self.fecha_respuesta.isoformat() if self.fecha_respuesta else None,
            'mascota_transferida': self.mascota_transferida,
            'fecha_transferencia': self.fecha_transferencia.isoformat() if self.fecha_transferencia else None
        }
