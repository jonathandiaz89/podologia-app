# utils/offline_storage.py
from kivy.storage.jsonstore import JsonStore
import json
from datetime import datetime

store = JsonStore('offline_data.json')

def save_offline_data(collection, data):
    """Guardar datos para modo offline"""
    try:
        store.put(collection, data=data, timestamp=datetime.now().isoformat())
        return True
    except:
        return False

def load_offline_data(collection):
    """Cargar datos guardados offline"""
    try:
        if store.exists(collection):
            return store.get(collection)['data']
        return []
    except:
        return []