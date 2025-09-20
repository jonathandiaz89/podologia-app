from datetime import datetime, timedelta
from models.firebase import db

class HorarioManager:
    HORARIO_INICIO = 10  # 10:00 AM
    HORARIO_FIN = 20     # 8:00 PM
    INTERVALO = 30       # 30 minutos

    @staticmethod
    def generar_horarios_disponibles(fecha):
        try:
            citas_ref = db.collection("citas")
            query = citas_ref.where("fecha", "==", fecha).stream()
            
            citas_ocupadas = []
            for cita in query:
                cita_data = cita.to_dict()
                citas_ocupadas.append(cita_data["hora"])
            
            horarios_disponibles = []
            hora_actual = HorarioManager.HORARIO_INICIO
            minuto_actual = 0
            
            while hora_actual < HorarioManager.HORARIO_FIN or (hora_actual == HorarioManager.HORARIO_FIN and minuto_actual == 0):
                hora_str = f"{hora_actual:02d}:{minuto_actual:02d}"
                
                if hora_str not in citas_ocupadas:
                    horarios_disponibles.append(hora_str)
                
                minuto_actual += HorarioManager.INTERVALO
                if minuto_actual >= 60:
                    minuto_actual = 0
                    hora_actual += 1
            
            return horarios_disponibles
        
        except Exception as e:
            print(f"Error generando horarios: {e}")
            return []
        
    @staticmethod
    def generar_todos_horarios_posibles():
        horarios = []
        hora_actual = HorarioManager.HORARIO_INICIO
        minuto_actual = 0
    
        while hora_actual < HorarioManager.HORARIO_FIN or (hora_actual == HorarioManager.HORARIO_FIN and minuto_actual == 0):
            horarios.append(f"{hora_actual:02d}:{minuto_actual:02d}")
        
            minuto_actual += HorarioManager.INTERVALO
            if minuto_actual >= 60:
                minuto_actual = 0
                hora_actual += 1
    
        return horarios