from app.database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(255))
    rol = db.Column(db.String(10), default='CLIENTE')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    
    # Relaciones bidireccionales completas
    mascotas = db.relationship('Mascota', back_populates='propietario', lazy=True)
    citas = db.relationship('Cita', foreign_keys='Cita.cliente_id', back_populates='cliente', lazy=True)
    citas_veterinario = db.relationship('Cita', foreign_keys='Cita.veterinario_id', back_populates='veterinario', lazy=True)
    solicitudes_adopcion = db.relationship('Adopcion', foreign_keys='Adopcion.solicitante_id', back_populates='solicitante', lazy=True)
    adopciones_gestionadas = db.relationship('Adopcion', foreign_keys='Adopcion.administrador_id', back_populates='administrador', lazy=True)
    # Agregar en la clase Usuario, después de las relaciones existentes:
    historial_creado = db.relationship('HistorialMedico', foreign_keys='HistorialMedico.veterinario_id', back_populates='veterinario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
       return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'rol': self.rol,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
