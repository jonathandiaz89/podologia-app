import requests
from config import FIREBASE_API_KEY
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
        
    def show_error(self, message):
        """Mostrar popup de error"""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text=message))
        
        btn_close = Button(text="Cerrar", size_hint_y=None, height=50)
        
        popup = Popup(
            title="Error",
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()    
    
    def login(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        
        if not email or not password:
            self.show_error("Por favor ingrese correo y contraseña")
            return
        
        # 1. Verificar admin local primero
        if store.exists('admin'):
            admin_data = store.get('admin')
            if (email == admin_data['email'] and 
                Security.hash_password(password) == admin_data['password']):
                self.login_success_callback()
                return
        
        # 2. Autenticación con Firebase
        self._firebase_login(email, password)
        
    def _firebase_login(self, email, password):
        try:
            API_KEY="AIzaSyCiHTz-UrtJkIOoxGqEv6_Td1gQ05iXL4U"
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
            
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            print(f"Respuesta login: {data}")
            
            if response.status_code == 200:
                print("Login exitoso, redirigiendo...")
                self.login_success_callback()
            else:
                error_msg = data.get('error', {}).get('message', 'Error de autenticación')
                self.show_error(f"Error de login: {error_msg}")
                
        except Exception as e:
            print(f"Error completo en login: {e}")
            self.show_error("Error de la aplicación. Revise la consola para detalles")
        
    def register(self, instance):
        """Método para registrar nuevos usuarios"""
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        
        if not email or not password:
            self.show_error("Por favor ingrese correo y contraseña")
            return
        
        if not Security.validate_email(email):
            self.show_error("Correo electrónico no válido")
            return
            
        if len(password) < 6:
            self.show_error("La contraseña debe tener al menos 6 caracteres")
            return
        
        try:
            API_KEY = "AIzaSyCiHTz-UrtJkIOoxGqEv6_Td1gQ05iXL4U"  # Esta parece ser tu key
        
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
        
            payload = {
                "email": email,
                "password": password, 
                "returnSecureToken": True
            }
            
            # Mostrar mensaje de espera
            self.show_error("Registrando usuario...")
            
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            
            print(f"Respuesta de registro: {data}")  # Para debug
            
            if response.status_code == 200:
                self.show_error("✅ Usuario registrado correctamente. Iniciando sesión...")
                self._firebase_login(email, password)
                
            else:
                error_msg = data.get('error', {}).get('message', 'Error desconocido')
                
                if error_msg=="EMAIL_EXISTS":
                    self.show_error("El usuario ya existe. Intentando iniciar sesión...")
                    
                    self._firebase_error(f"Error: {error_msg}")               
                
        except Exception as e:
            self.show_error(f"Error de conexión: {str(e)}")
            
    def _handle_register_error(self, error_code):
        """Manejar errores específicos de registro"""
        error_messages = {
            "EMAIL_EXISTS": "❌ El correo electrónico ya está registrado",
            "OPERATION_NOT_ALLOWED": "❌ El registro con email/contraseña no está habilitado",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "❌ Demasiados intentos. Intente más tarde",
            "INVALID_EMAIL": "❌ Correo electrónico inválido",
            "WEAK_PASSWORD": "❌ La contraseña es muy débil"
        }
    
        message = error_messages.get(error_code, f"❌ Error al registrar: {error_code}")
        self.show_error(message)
                
def _translate_error(self, error_code):
    errors = {
        "EMAIL_NOT_FOUND": "Usuario no encontrado",
        "INVALID_PASSWORD": "Contraseña incorrecta",
        "USER_DISABLED": "Usuario deshabilitado",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Demasiados intentos. Espere 5 minutos",
    }
    return errors.get(error_code, "Error de autenticación")
                            
    
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
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        popup = Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        
    def user_is_admin():
        try:
            user = auth.current_user
            if user:
                # Obtener los custom claims
                claims = user.get('custom_claims', {})
                return claims.get('admin', False)
            return False
        except:
            return False

    def on_enter(self):
        # Esta función se ejecuta cuando la pantalla se muestra
        try:
            # Verificar si el usuario es admin y habilitar/deshabilitar botones
            if hasattr(self, 'btn_centro_costos'):
                from models.firebase import auth
                user = auth.current_user
                if user:
                    # Verificar si es admin (aquí necesitarías implementar la lógica)
                    self.btn_centro_costos.disabled = not self.user_is_admin()
        except:
            pass
        
    def on_start(self):
        from kivy.clock import Clock
        from datetime import datetime
        
        def init_firebase_later(dt):
            try:
                from models.firebase import initialize_firebase, check_connection
                
                print("Intentando inicializar Firebase...")
                db_instance = initialize_firebase()
                
                if db_instance is not None:
                    self.firebase_initialized = True
                    print("✅ Firebase conectado correctamente")
                    
                    # Verificar conexión activa
                    if check_connection():
                        print("✅ Conexión a Firebase verificada")
                    else:
                        print("⚠️  Firebase inicializado pero sin conexión activa")
                        self.firebase_initialized = False
                else:
                    print("❌ Firebase no disponible - modo offline activado")
                    self.firebase_initialized = False
                    
            except Exception as e:
                print(f"❌ Error crítico iniciando Firebase: {e}")
                self.firebase_initialized = False
        
        # Programar la inicialización
        Clock.schedule_once(init_firebase_later, 1.0)
        
        # Verificar conexión periódicamente
        Clock.schedule_interval(self.verificar_conexion, 30)  # Cada 30 segundos

def verificar_conexion(self, dt):
    """Verificar conexión periódicamente"""
    if hasattr(self, 'firebase_initialized') and self.firebase_initialized:
        from models.firebase import check_connection
        if not check_connection():
            print("⚠️  Pérdida de conexión detectada")
            self.firebase_initialized = False
        