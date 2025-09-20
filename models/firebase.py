# models/firebase.py - VERSIÓN GITHUB
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logging.getLogger('firebase-admin').setLevel(logging.ERROR)

db_instance = None
is_initialized = False

def initialize_firebase():
    """Inicializar Firebase para GitHub Actions y producción"""
    global db_instance, is_initialized
    
    if is_initialized:
        return db_instance
        
    try:
        if firebase_admin._apps:
            db_instance = firestore.client()
            is_initialized = True
            return db_instance

        # 1. Primero intentar con variable de entorno (GitHub Secrets)
        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        if service_account_json:
            try:
                service_account_info = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_info)
                print("✅ Firebase configurado con GitHub Secrets")
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing service account JSON: {e}")
                return None

        # 2. Intentar con archivo local (solo desarrollo)
        elif os.path.exists('firebase-creds.json'):
            cred = credentials.Certificate('firebase-creds.json')
            print("✅ Firebase configurado con archivo local (solo desarrollo)")

        # 3. Fallback para testing
        else:
            print("⚠️  Modo offline: Firebase no configurado")
            return None

        firebase_admin.initialize_app(cred)
        db_instance = firestore.client()
        is_initialized = True
        print("✅ Firebase inicializado correctamente")
        return db_instance
        
    except Exception as e:
        print(f"❌ Error inicializando Firebase: {e}")
        return None

def get_db():
    """Obtener instancia de la base de datos"""
    if db_instance is None:
        return initialize_firebase()
    return db_instance

def get_auth():
    """Obtener instancia de autenticación"""
    initialize_firebase()
    return auth
