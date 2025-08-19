import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore, auth

db = None

def initialize_firebase():
    global db
    try:
        if not firebase_admin._apps:
            # Para Android/iOS usamos las credenciales por defecto
            if os.environ.get('KIVY_BUILD') in ('android', 'ios'):
                cred = credentials.Certificate({
                    "type": os.environ.get("FIREBASE_TYPE"),
                    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
                    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
                    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
                    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
                    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
                    "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
                    "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
                    "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_CERT_URL"),
                    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_CERT_URL")
                })
            else:
                # Para desktop usamos el archivo JSON
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase-creds.json')
                if Path(cred_path).exists():
                    cred = credentials.Certificate(cred_path)
                else:
                    raise FileNotFoundError(f"No se encontró el archivo de credenciales en {cred_path}")
            
            firebase_admin.initialize_app(cred)
            db = firestore.client()
        return db
    except Exception as e:
        print(f"Error inicializando Firebase: {e}")
        raise

initialize_firebase()