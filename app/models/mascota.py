from app.database import db
from datetime import datetime

class Mascota(db.Model):
    __tablename__ = 'mascotas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50))
    raza = db.Column(db.String(50))
    edad = db.Column(db.Integer)
    peso = db.Column(db.Float)
    color = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    foto_url = db.Column(db.String(500))
    propietario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    disponible_adopcion = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    propietario = db.relationship('Usuario', back_populates='mascotas')
    citas = db.relationship('Cita', back_populates='mascota', lazy=True)
    adopciones = db.relationship('Adopcion', back_populates='mascota', lazy=True)
    # Agregar en la clase Mascota:
    historial_medico = db.relationship('HistorialMedico', back_populates='mascota', lazy=True, order_by='HistorialMedico.fecha_consulta.desc()')

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'especie': self.especie,
            'raza': self.raza,
            'edad': self.edad,
            'peso': self.peso,
            'color': self.color,
            'descripcion': self.descripcion,
            'foto_url': self.foto_url,
            'propietario_id': self.propietario_id,
            'disponible_adopcion': self.disponible_adopcion,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
