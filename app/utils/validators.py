import re

class Validators:
    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Valida que la contraseña tenga al menos 8 caracteres"""
        return len(password) >= 8
    
    @staticmethod
    def validate_phone(phone):
        """Valida formato de teléfono"""
        pattern = r'^\+?[\d\s\-()]+$'
        return re.match(pattern, phone) is not None if phone else True
