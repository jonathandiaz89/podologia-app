from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from components.popups import HistorialMedicoPopup
from models.firebase import db
from kivy.clock import Clock
from firebase_admin import firestore

class PacientesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        search_layout = BoxLayout(size_hint_y=None, height=50)
        self.search_input = TextInput(hint_text="Buscar por nombre o RUT")
        search_btn = Button(text="Buscar", size_hint_x=None, width=100)
        search_btn.bind(on_press=self.buscar_pacientes)
        search_layout.add_widget(self.search_input)
        search_layout.add_widget(search_btn)
        
        self.scroll = ScrollView()
        self.pacientes_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.pacientes_layout.bind(minimum_height=self.pacientes_layout.setter('height'))
        self.scroll.add_widget(self.pacientes_layout)
        
        btn_volver = Button(
            text="Volver", 
            size_hint_y=None, 
            height=50,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_volver.bind(on_press=self.volver)
        
        self.layout.add_widget(search_layout)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(btn_volver)
        self.add_widget(self.layout)
        
        Clock.schedule_once(lambda dt: self.cargar_pacientes())
    
    def cargar_pacientes(self, filtro=None):
        self.pacientes_layout.clear_widgets()
        
        try:
            pacientes_ref = db.collection("pacientes")
            
            if filtro:
                query = pacientes_ref.where("rut", ">=", filtro).where("rut", "<=", filtro + '\uf8ff').stream()
            else:
                query = pacientes_ref.stream()
            
            for doc in query:
                paciente_data = doc.to_dict()
                btn = Button(
                    text=f"{paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')} - {paciente_data.get('rut', '')}",
                    size_hint_y=None,
                    height=60,
                    background_color=(0.2, 0.6, 0.8, 1)
                )
                btn.paciente_data = paciente_data
                btn.bind(on_press=self.mostrar_detalle_paciente)
                self.pacientes_layout.add_widget(btn)
                
        except Exception as e:
            print(f"Error cargando pacientes: {e}")
            self.pacientes_layout.add_widget(Label(text=f"Error al cargar pacientes: {str(e)}"))
    
    def buscar_pacientes(self, instance):
        filtro = self.search_input.text.strip()
        self.cargar_pacientes(filtro)
    
    def mostrar_detalle_paciente(self, instance):
        paciente_data = instance.paciente_data
        content = BoxLayout(orientation='vertical', spacing=10)
        
        details = f"""
        Nombre: {paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')}
        RUT: {paciente_data.get('rut', '')}
        Fecha Nac.: {paciente_data.get('fecha_nacimiento', '')}
        Teléfono: {paciente_data.get('telefono', '')}
        Email: {paciente_data.get('email', '')}
        """
        
        content.add_widget(Label(text=details))
        
        btn_historial = Button(
            text="Ver Historial Médico",
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.5, 0.7, 1)
        )
        btn_historial.bind(on_press=lambda x: self.abrir_historial(paciente_data))
        
        btn_close = Button(
            text="Cerrar",
            size_hint_y=None,
            height=50
        )
        
        content.add_widget(btn_historial)
        content.add_widget(btn_close)
        
        popup = Popup(
            title="Detalles del Paciente",
            content=content,
            size_hint=(0.8, 0.6))
        btn_close.bind(on_press=popup.dismiss)
        popup.open()
        
    def abrir_historial(self, paciente_data):
        popup = HistorialMedicoPopup(paciente_data)
        popup.open()
    
    def volver(self, instance):
        self.manager.current = 'main'