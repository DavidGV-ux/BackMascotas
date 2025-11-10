import secrets
from datetime import datetime, timedelta
from app.models.usuario import Usuario
from app.database import db
from flask import current_app
from keycloak import KeycloakOpenID


class AuthService:
    _kc_client: KeycloakOpenID | None = None

    @staticmethod
    def get_keycloak_client() -> KeycloakOpenID:
        if AuthService._kc_client is None:
            cfg = current_app.config
            server_url = cfg.get('KEYCLOAK_SERVER_URL')
            realm = cfg.get('KEYCLOAK_REALM')
            client_id = cfg.get('KEYCLOAK_CLIENT_ID')
            client_secret = cfg.get('KEYCLOAK_CLIENT_SECRET')
            if not all([server_url, realm, client_id, client_secret]):
                raise RuntimeError('Keycloak settings are missing')
            AuthService._kc_client = KeycloakOpenID(
                server_url=server_url,
                client_id=client_id,
                realm_name=realm,
                client_secret_key=client_secret
            )
        return AuthService._kc_client
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
