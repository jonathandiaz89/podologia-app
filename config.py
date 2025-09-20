import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'podologia-app')
    FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY', '')
    
    @staticmethod
    def get_firebase_config():
        return {
            "apiKey": Config.FIREBASE_API_KEY,
            "authDomain": f"{Config.FIREBASE_PROJECT_ID}.firebaseapp.com",
            "projectId": Config.FIREBASE_PROJECT_ID,
            "storageBucket": f"{Config.FIREBASE_PROJECT_ID}.appspot.com"
        }