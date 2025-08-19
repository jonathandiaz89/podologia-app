from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.core.window import Window
import os

# Importaciones de pantallas
from screens.login import LoginScreen
from screens.main_screen import MainScreen
from screens.first_run import FirstRunScreen
from screens.costos import CentroCostosScreen
from screens.pacientes import PacientesScreen
from screens.citas import CitasScreen

class PodologiaApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sm = ScreenManager()
        self.store = JsonStore('app_settings.json')
        self.firebase_initialized = False
        
    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        
        # Configuración de tamaño para móviles
        if platform in ['android', 'ios']:
            Window.size = (360, 640)
        
        # Configuración inicial
        if not self.store.exists('admin'):
            self.sm.add_widget(FirstRunScreen(
                setup_complete_callback=self.show_login_screen,
                name='firstrun'
            ))
        else:
            self.sm.add_widget(LoginScreen(
                login_success_callback=self.show_main_screen,
                name='login'
            ))
        
        # Registrar pantallas
        self.register_screens()
        
        # Verificar recordatorios cada 30 minutos
        Clock.schedule_interval(self.verificar_recordatorios, 1800)
        
        return self.sm
    
    def on_start(self):
        # Inicializar Firebase después de que la app esté lista
        if not self.firebase_initialized:
            self.initialize_firebase()
    
    def initialize_firebase(self):
        try:
            from models.firebase import initialize_firebase
            initialize_firebase()
            self.firebase_initialized = True
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
    
    def register_screens(self):
        """Registra todas las pantallas de la aplicación"""
        screens = {
            'main': MainScreen,
            'centro_costos': CentroCostosScreen,
            'pacientes': PacientesScreen,
            'citas': CitasScreen
        }
        
        for name, screen_class in screens.items():
            if name not in self.sm.screen_names:
                self.sm.add_widget(screen_class(name=name))
    
    def show_login_screen(self):
        self.sm.add_widget(LoginScreen(
            login_success_callback=self.show_main_screen,
            name='login'
        ))
        self.sm.current = 'login'
    
    def show_main_screen(self):
        if 'main' not in self.sm.screen_names:
            self.sm.add_widget(MainScreen(name='main'))
        self.sm.current = 'main'
        
    def verificar_recordatorios(self, dt):
        if not self.firebase_initialized:
            return
            
        from models.firebase import db
        from datetime import datetime, timedelta
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        
        try:
            hoy = datetime.now().strftime("%d-%m-%Y")
            manana = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
            
            citas_ref = db.collection("citas")
            query = citas_ref.where("fecha", "in", [hoy, manana]).where("estado", "==", "pendiente").stream()
            
            for cita in query:
                cita_data = cita.to_dict()
                fecha_cita = datetime.strptime(f"{cita_data['fecha']} {cita_data['hora']}", "%d-%m-%Y %H:%M")
                
                if datetime.now() <= fecha_cita <= (datetime.now() + timedelta(hours=24)):
                    self.mostrar_recordatorio(cita_data)
        
        except Exception as e:
            print(f"Error verificando recordatorios: {e}")
    
    def mostrar_recordatorio(self, cita_data):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(
            text=f"Recordatorio de cita:\n\n"
                 f"Paciente: {cita_data['paciente_nombre']}\n"
                 f"Fecha: {cita_data['fecha']} {cita_data['hora']}\n"
                 f"Motivo: {cita_data['motivo']}"
        ))
        
        btn_ok = Button(text="Aceptar", size_hint_y=None, height=50)
        
        popup = Popup(
            title="Recordatorio de Cita",
            content=content,
            size_hint=(0.8, 0.5)
        )
        btn_ok.bind(on_press=popup.dismiss)
        content.add_widget(btn_ok)
        popup.open()

if __name__ == '__main__':
    PodologiaApp().run()