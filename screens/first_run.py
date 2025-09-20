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
from firebase_admin import firestore, auth

store = JsonStore('app_settings.json')

class FirstRunScreen(Screen):
    def __init__(self, setup_complete_callback, **kwargs):
        super().__init__(**kwargs)
        self.setup_complete_callback = setup_complete_callback
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        with layout.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(source='assets/podologia_bg.png', size=Window.size)
        
        Window.bind(size=self._update_bg)
        
        title = Label(
            text="Configuración Inicial", 
            font_size='24sp',
            bold=True,
            color=(0, 0, 0, 1)
        )
        
        self.email_input = TextInput(
            hint_text="Correo electrónico del administrador",
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
        
        self.confirm_password_input = TextInput(
            hint_text="Confirmar contraseña",
            password=True,
            multiline=False,
            size_hint=(1, None),
            height=50
        )
        
        btn_setup = Button(
            text="Guardar Credenciales",
            size_hint=(1, None),
            height=60,
            background_color=(0.2, 0.6, 0.2, 1),
            color=(1, 1, 1, 1)
        )
        btn_setup.bind(on_press=self.save_credentials)
        
        layout.add_widget(title)
        layout.add_widget(self.email_input)
        layout.add_widget(self.password_input)
        layout.add_widget(self.confirm_password_input)
        layout.add_widget(btn_setup)
        
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg.size = value
    
    def save_credentials(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        confirm_password = self.confirm_password_input.text.strip()
        
        if not Security.validate_email(email):
            self.show_error("Correo electrónico no válido")
            return
        
        if len(password) < 6:
            self.show_error("La contraseña debe tener al menos 6 caracteres")
            return
            
        if password != confirm_password:
            self.show_error("Las contraseñas no coinciden")
            return
        
        try:
            store.put('admin', email=email, password=Security.hash_password(password))
            auth.create_user(email=email, password=password)
            self.setup_complete_callback()
            
        except Exception as e:
            self.show_error(f"Error al guardar credenciales: {str(e)}")
    
    def show_error(self, message):
        popup = Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        
    def make_user_admin(email):
        try:
            # Obtener el usuario por email
            user = auth.get_user_by_email(email)
            
            # Establecer custom claim de administrador
            auth.set_custom_user_claims(user.uid, {'admin': True})
            
            print(f"Usuario {email} ahora es administrador")
        except Exception as e:
            print(f"Error haciendo admin: {e}")