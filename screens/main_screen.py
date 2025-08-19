from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from components.popups import NuevoPacientePopup, BuscarPacientePopup
from firebase_admin import firestore

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        with self.layout.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(source='assets/podologia_bg.png', size=Window.size)
        
        Window.bind(size=self._update_bg)
        
        title = Label(
            text="PodologíaApp", 
            font_size='28sp',
            bold=True,
            size_hint=(1, 0.2),
            color=(0, 0, 0, 1)
        )
        
        btn_grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.7))
        
        btn_nuevo_paciente = Button(
            text="Nuevo Paciente",
            background_color=(0.2, 0.6, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        btn_nuevo_paciente.bind(on_press=self.abrir_popup_nuevo_paciente)
        
        btn_ver_pacientes = Button(
            text="Ver Pacientes",
            background_color=(0.3, 0.5, 0.7, 1),
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        btn_ver_pacientes.bind(on_press=self.ver_pacientes)
        
        btn_crear_cita = Button(
            text="Crear Cita",
            background_color=(0.4, 0.4, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        btn_crear_cita.bind(on_press=self.crear_cita)
        
        btn_buscar_paciente = Button(
            text="Buscar Paciente",
            background_color=(0.5, 0.3, 0.5, 1),
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        btn_buscar_paciente.bind(on_press=self.buscar_paciente)
        
        btn_ver_citas = Button(
            text="Citas/Recordatorios",
            background_color=(0.6, 0.3, 0.5, 1),
            font_size='18sp'
        )
        btn_ver_citas.bind(on_press=self.ver_citas)
        
        btn_centro_costos = Button(
            text="Centro de Costos",
            background_color=(0.4, 0.2, 0.6, 1),  # Color distintivo
            color=(1, 1, 1, 1),
            font_size='18sp'
        )
        btn_centro_costos.bind(on_press=self.abrir_centro_costos)

        btn_grid.add_widget(btn_nuevo_paciente)
        btn_grid.add_widget(btn_ver_pacientes)
        btn_grid.add_widget(btn_crear_cita)
        btn_grid.add_widget(btn_buscar_paciente)
        btn_grid.add_widget(btn_ver_citas)
        btn_grid.add_widget(btn_centro_costos)
        
        self.layout.add_widget(title)
        self.layout.add_widget(btn_grid)
        
        self.add_widget(self.layout)
    
    def _update_bg(self, instance, value):
        self.bg.size = value
    
    def abrir_popup_nuevo_paciente(self, instance):
        popup = NuevoPacientePopup(self.mostrar_exito)
        popup.open()
    
    def ver_pacientes(self, instance):
        from screens.pacientes import PacientesScreen
        pacientes_screen = PacientesScreen(name='pacientes')
        self.manager.add_widget(pacientes_screen)
        self.manager.current = 'pacientes'
    
    def crear_cita(self, instance):
        from components.popups import CitaPopup
        popup = CitaPopup()
        popup.open()
    
    def buscar_paciente(self, instance):
        popup = BuscarPacientePopup()
        popup.open()
    
    def mostrar_exito(self, paciente_data):
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(
            text=f"Paciente {paciente_data['nombre']} registrado!",
            font_size='16sp'
        ))
        close_btn = Button(
            text="Aceptar", 
            size_hint_y=None, 
            height=50,
            background_color=(0.1, 0.7, 0.3, 1)
        )
        popup = Popup(
            title="Éxito",
            content=content,
            size_hint=(0.7, 0.4)
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()
        
    def ver_citas(self, instance):
        from screens.citas import CitasScreen
        citas_screen = CitasScreen(name='citas')
        self.manager.add_widget(citas_screen)
        self.manager.current = 'citas'
        
    def abrir_centro_costos(self, instance):
        from screens.costos import CentroCostosScreen  # Importa la pantalla
        costos_screen = CentroCostosScreen(name='centro_costos')
        self.manager.add_widget(costos_screen)
        self.manager.current = 'centro_costos'