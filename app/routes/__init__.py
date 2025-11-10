from .auth import auth_bp
from .mascota import mascota_bp
from .adopcion import adopcion_bp  # ✅ ASEGURAR QUE ESTÉ
from .cita import cita_bp
from .historial import historial_bp
from .usuarios import usuarios_bp
from .reportes import reportes_bp

__all__ = [
    'auth_bp',
    'mascota_bp',
    'adopcion_bp',  # ✅ ASEGURAR QUE ESTÉ
    'cita_bp',
    'historial_bp',
    'usuarios_bp',
    'reportes_bp'
]
