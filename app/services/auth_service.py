import secrets
from datetime import datetime, timedelta
from app.models.usuario import Usuario
from app.database import db


class AuthService:
    @staticmethod
    def generate_reset_token():
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_reset_token(email):
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            return None
        
        token = AuthService.generate_reset_token()
        usuario.reset_token = token
        usuario.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        return token
    
    @staticmethod
    def verify_reset_token(token):
        usuario = Usuario.query.filter_by(reset_token=token).first()
        if not usuario:
            return None
        
        if usuario.reset_token_expiry < datetime.utcnow():
            return None
        
        return usuario
    
    @staticmethod
    def reset_password(token, new_password):
        usuario = AuthService.verify_reset_token(token)
        if not usuario:
            return False
        
        usuario.set_password(new_password)
        usuario.reset_token = None
        usuario.reset_token_expiry = None
        db.session.commit()
        
        return True
