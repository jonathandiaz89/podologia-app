from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from kivy.uix.popup import Popup
from components.security import Security
from models.firebase import auth
from kivy.storage.jsonstore import JsonStore
from firebase_admin import firestore

store = JsonStore('app_settings.json')

class LoginScreen(Screen):
    def __init__(self, login_success_callback, **kwargs):
        super().__init__(**kwargs)
        self.login_success_callback = login_success_callback
        
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        with layout.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(source='assets/podologia_bg.png', size=Window.size)
        
        Window.bind(size=self._update_bg)
        
        title = Label(
            text="PodologíaApp", 
            font_size='28sp',
            bold=True,
            color=(0, 0, 0, 1)
        )
        
        self.email_input = TextInput(
            hint_text="Correo",
            multiline=False,
            size_hint=(1, None),
            height=50
        )
        
        self.password_input = TextInput(
            hint_text="Contraseña",
            password=True,
            multiline=False,
            size_hint=(1, None),
            height=50
        )
        
        btn_layout = BoxLayout(spacing=10, size_hint=(1, None), height=60)
        
        login_btn = Button(
            text="Iniciar Sesión",
            background_color=(0.2, 0.4, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        login_btn.bind(on_press=self.login)
        
        register_btn = Button(
            text="Registrarse",
            background_color=(0.8, 0.4, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        register_btn.bind(on_press=self.register)
        
        btn_layout.add_widget(login_btn)
        btn_layout.add_widget(register_btn)
        
        layout.add_widget(title)
        layout.add_widget(self.email_input)
        layout.add_widget(self.password_input)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg.size = value
    
    def login(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        
        if not email or not password:
            self.show_error("Por favor ingrese correo y contraseña")
            return
        
        try:
            if store.exists('admin'):
                admin_data = store.get('admin')
                if (email == admin_data['email'] and 
                    Security.hash_password(password) == admin_data['password']):
                    self.login_success_callback()
                    return
            
            user = auth.get_user_by_email(email)
            self.login_success_callback()
            
        except Exception as e:
            self.show_error("Error al iniciar sesión. Verifica tus credenciales.")
    
    def register(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        
        if not Security.validate_email(email):
            self.show_error("Correo electrónico no válido")
            return
            
        if len(password) < 6:
            self.show_error("La contraseña debe tener al menos 6 caracteres")
            return
        
        try:
            auth.create_user(email=email, password=password)
            self.show_error("Usuario registrado correctamente. Ahora puedes iniciar sesión.")
        except Exception as e:
            error_msg = "Error al registrar usuario."
            if "EMAIL_EXISTS" in str(e):
                error_msg = "El correo ya está en uso."
            self.show_error(error_msg)
    
    def show_error(self, message):
        popup = Popup(
            title="Mensaje",
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()