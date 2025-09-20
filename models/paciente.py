from models.firebase import db, auth
from datetime import datetime
from components.security import Security

class Paciente:
    @staticmethod
    def crear(nombre, apellido, rut, fecha_nac, telefono, email):
        try:
            user = auth.create_user(
                email=email,
                password=rut.replace("-", ""),
                display_name=f"{nombre} {apellido}"
            )
            
            paciente_data = {
                "nombre": nombre,
                "apellido": apellido,
                "rut": rut,
                "fecha_nacimiento": fecha_nac,
                "telefono": telefono,
                "email": email,
                "fecha_registro": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "uid": user.uid
            }
            
            db.collection("pacientes").document(user.uid).set(paciente_data)
            return paciente_data
        
        except Exception as e:
            raise e
    
    @staticmethod
    def buscar_por_rut(rut):
        try:
            pacientes_ref = db.collection("pacientes")
            query = pacientes_ref.where("rut", "==", rut).limit(1).stream()
            
            for doc in query:
                return doc.to_dict()
            
            return None
        except Exception as e:
            raise e
    
    @staticmethod
    def obtener_todos():
        try:
            pacientes_ref = db.collection("pacientes")
            return [doc.to_dict() for doc in pacientes_ref.stream()]
        except Exception as e:
            raise e