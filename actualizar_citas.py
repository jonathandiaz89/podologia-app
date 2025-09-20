#!/usr/bin/env python3
"""
Script para actualizar citas existentes con montos por defecto
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Configuración de Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def actualizar_citas_con_monto():
    """Agregar campo monto a las citas existentes"""
    try:
        citas_ref = db.collection('citas').stream()
        citas_actualizadas = 0
        
        for doc in citas_ref:
            cita = doc.to_dict()
            
            # Si la cita no tiene monto, agregarlo
            if 'monto' not in cita:
                # Monto por defecto basado en el servicio
                servicio = cita.get('servicio', '').lower()
                monto_por_defecto = 50.00  # Monto base
                
                if 'corte' in servicio or 'normal' in servicio:
                    monto_por_defecto = 15000
                elif 'uña' in servicio or 'onicocriptosis' in servicio:
                    monto_por_defecto = 20000
                elif 'callo' in servicio or 'hiperqueratosis' in servicio:
                    monto_por_defecto = 20000
                elif 'consulta' in servicio or 'evaluación' in servicio:
                    monto_por_defecto = 0
                
                # Actualizar la cita
                db.collection('citas').document(doc.id).update({
                    'monto': monto_por_defecto,
                    'actualizado_en': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                citas_actualizadas += 1
                print(f"Cita {doc.id} actualizada con monto: ${monto_por_defecto}")
        
        print(f"\n✅ Se actualizaron {citas_actualizadas} citas con montos por defecto")
        
    except Exception as e:
        print(f"❌ Error al actualizar citas: {e}")

if __name__ == "__main__":
    print("🔧 Actualizando citas existentes con montos...")
    actualizar_citas_con_monto()