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
        
        header_layout = BoxLayout(size_hint=(1, 0.15), spacing=10)
        
        title = Label(
            text="PodologíaApp", 
            font_size='28sp',
            bold=True,
            color=(0, 0, 0, 1)
        )
        
        # Botón de cerrar sesión
        btn_logout = Button(
            text="Cerrar Sesión",
            size_hint_x=None,
            width=120,
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        btn_logout.bind(on_press=self.cerrar_sesion)
        
        header_layout.add_widget(title)
        header_layout.add_widget(btn_logout)
        
        # Indicador de conexión - se inicializa vacío y se actualiza en on_enter
        self.connection_indicator = Label(
            text="",
            size_hint_x=None,
            width=100,
            color=(0, 0.6, 0, 1),
            font_size='12sp'
        )
        header_layout.add_widget(self.connection_indicator)
                
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
            background_color=(0.4, 0.2, 0.6, 1),
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
        
        self.layout.add_widget(header_layout)
        self.layout.add_widget(btn_grid)
        self.add_widget(self.layout)
        
    def _update_bg(self, instance, value):
        self.bg.size = value
        
    def on_enter(self):
        """Actualiza el indicador de conexión cuando se entra a la pantalla"""
        try:
            from kivy.app import App
            app = App.get_running_app()
            if hasattr(app, 'firebase_initialized') and app.firebase_initialized:
                self.connection_indicator.text = "✅ En línea"
                self.connection_indicator.color = (0, 0.6, 0, 1)
            else:
                self.connection_indicator.text = "❌ Offline"
                self.connection_indicator.color = (0.8, 0, 0, 1)
        except Exception as e:
            # En caso de error, mostrar estado offline
            self.connection_indicator.text = "❌ Offline"
            self.connection_indicator.color = (0.8, 0, 0, 1)
                
    def cerrar_sesion(self, instance):
        """Cerrar sesión y volver al login"""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        
        # Crear popup de confirmación
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text="¿Estás seguro de que quieres cerrar sesión?"))
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        btn_confirmar = Button(
            text='Si, cerrar sesión',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_confirmar.bind(on_press=self._confirmar_logout)
        
        btn_cancelar = Button(
            text="Cancelar",
            background_color=(0.4, 0.6, 0.8, 1)
        )
        
        popup = Popup(
            title="Cerrar Sesión",
            content=content,
            size_hint=(0.7, 0.4)
        )
        
        btn_cancelar.bind(on_press=popup.dismiss)
        btn_layout.add_widget(btn_confirmar)
        btn_layout.add_widget(btn_cancelar)
        content.add_widget(btn_layout)
        
        popup.open()
        
    def _confirmar_logout(self, instance):
        """Confirmar cierre de sesión"""
        try:
            # Cerrar popup
            instance.parent.parent.parent.dismiss()
            
            # Limpiar cualquier sesión existente
            try:
                from models.firebase import auth
                if hasattr(auth, 'auth') and auth.auth.current_user:
                    auth.auth.current_user = None
            except:
                pass
            
            # Volver a la pantalla login
            self.manager.current = 'login'
            
            # Limpiar campos de login si existen
            login_screen = self.manager.get_screen('login')
            if hasattr(login_screen, 'email_input'):
                login_screen.email_input.text = ''
            if hasattr(login_screen, 'password_input'):
                login_screen.password_input.text = ''
                
        except Exception as e:
            print(f"Error cerrando sesión: {e}")
            # Forzar volver al login incluso si hay error
            self.manager.current = 'login'
    
    def abrir_popup_nuevo_paciente(self, instance):
        popup = NuevoPacientePopup(self.mostrar_exito)
        popup.open()
    
    def ver_pacientes(self, instance):
        from screens.pacientes import PacientesScreen
        if not self.manager.has_screen('pacientes'):
            pacientes_screen = PacientesScreen(name='pacientes')
            self.manager.add_widget(pacientes_screen)
        self.manager.current = 'pacientes'
    
    def crear_cita(self, instance):
        from components.popups import CitaPopup
        popup = CitaPopup()
        popup.open()
    
    def buscar_paciente(self, instance):
        from components.popups import BuscarPacientePopup
        popup = BuscarPacientePopup()
        popup.open()
    
    def mostrar_exito(self, paciente_data):
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        
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
        if not self.manager.has_screen('citas'):
            citas_screen = CitasScreen(name='citas')
            self.manager.add_widget(citas_screen)
        self.manager.current = 'citas'
        
    def abrir_centro_costos(self, instance):
        from screens.costos import CentroCostosScreen
        if not self.manager.has_screen('centro_costos'):
            costos_screen = CentroCostosScreen(name='centro_costos')
            self.manager.add_widget(costos_screen)
        self.manager.current = 'centro_costos'
        