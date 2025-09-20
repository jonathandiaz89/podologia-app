import re
import hashlib
from datetime import datetime
from unidecode import unidecode

class Security:
    @staticmethod
    def sanitize_name(text, max_length=100):
        if not text or len(text) > max_length:
            return None
        
        sanitized = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ'\- ]", "", text)
        return sanitized.strip() if sanitized else None
    
    @staticmethod
    def sanitize_rut(rut):
        if not rut:
            return None
        
        rut = rut.replace(" ", "").replace(".", "").upper()
        
        if not re.match(r"^\d{7,8}-?[\dkK]$", rut):
            return None
        
        if "-" not in rut:
            rut = rut[:-1] + "-" + rut[-1]
        return rut
    
    @staticmethod
    def validar_rut(rut):
        rut = Security.sanitize_rut(rut)
        if not rut:
            return False, "Formato de RUT inválido. Ejemplo: 12345678-9"
            
        cuerpo, dv = rut.split("-")
        cuerpo = cuerpo.replace(".", "").replace(" ", "")
        
        if not cuerpo.isdigit():
            return False, "La parte antes del guión debe ser numérica"
            
        suma = 0
        multiplo = 2
        
        for c in reversed(cuerpo):
            suma += int(c) * multiplo
            multiplo += 1
            if multiplo > 7:
                multiplo = 2
        
        resto = suma % 11
        dv_esperado = "K" if resto == 1 else str(11 - resto) if resto != 0 else "0"
        
        if dv.upper() != dv_esperado:
            return False, f"Dígito verificador incorrecto. Debería ser {dv_esperado}"
        
        return True, "RUT válido"

    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone):
        return re.match(r'^\+?\d{8,15}$', phone) is not None

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def validate_date(date_str, format="%d-%m-%Y"):
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False