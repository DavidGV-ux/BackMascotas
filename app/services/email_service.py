import os
import boto3
from botocore.exceptions import ClientError


class EmailService:
    def __init__(self):
        self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-2'))
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@veterinaria.com')
    
    def send_reset_password_email(self, to_email, reset_token):
        """Envía email de recuperación de contraseña"""
        reset_url = f"https://veterinaria.com/reset-password?token={reset_token}"
        
        html_body = f"""
        <html>
            <body>
                <h2>Recuperación de Contraseña</h2>
                <p>Has solicitado restablecer tu contraseña.</p>
                <p>Haz clic en el siguiente enlace:</p>
                <a href="{reset_url}">Restablecer Contraseña</a>
                <p>Este enlace expira en 1 hora.</p>
            </body>
        </html>
        """
        
        try:
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': 'Recuperación de Contraseña'},
                    'Body': {'Html': {'Data': html_body}}
                }
            )
            return True
        except ClientError as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_adoption_notification(self, to_email, mascota_nombre, estado):
        """Envía notificación de adopción"""
        subject = f"Solicitud de Adopción - {mascota_nombre}"
        
        html_body = f"""
        <html>
            <body>
                <h2>Actualización de Solicitud de Adopción</h2>
                <p>Tu solicitud de adopción para <strong>{mascota_nombre}</strong> ha sido <strong>{estado}</strong>.</p>
            </body>
        </html>
        """
        
        try:
            self.ses_client.send_email(
                Source=self.sender_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Html': {'Data': html_body}}
                }
            )
            return True
        except:
            return False
