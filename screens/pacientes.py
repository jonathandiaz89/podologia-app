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
            from models.firebase import safe_query
            
            filters = []
            if filtro:
                # Buscar por nombre o RUT
                filters = [("rut", ">=", filtro), ("rut", "<=", filtro + '\uf8ff')]
            
            # Usar la nueva función safe_query
            resultados = safe_query("pacientes", filters=filters)
            
            for doc in resultados:
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
            self.pacientes_layout.add_widget(Label(
                text="Error cargando pacientes. Modo offline.",
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=40
            ))
            
    
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
        """Abrir popup del historial médico completo"""
        try:
            from components.popups import HistorialMedicoPopup
            
            popup = HistorialMedicoPopup(paciente_data)
            popup.open()
            
        except ImportError:
            print("Error no se pudo importar HistorialMedicoPop")
            self.mostrar_error_popup("Error: Componente de historial no disponible")
            
        except Exception as e:
            print(f"Error abriendo historial médico: {e}")
            self.mostrar_error_popup(f"No se pudo abrir el historial: {str(e)}")
            
    def mostrar_error_popup(self, mensaje):
        """Mostrar popup de error"""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        
        content=BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text=mensaje))
        
        btn_close=Button(text="Cerrar", size_hint_y=None, height=50)
        
        popup=Popup(
            title="Error",
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()
        
        
    def mostrar_ultimo_historial(self, paciente_id):
        try:
            # VERIFICACIÓN MÁS ROBUSTA del ID del paciente
            if not paciente_id or not isinstance(paciente_id, str) or paciente_id.strip() == "":
                print("ID de paciente inválido o vacío")
                return
                
            paciente_id = paciente_id.strip()
            
            print(f"Buscando historial para paciente ID: {paciente_id}")
            
            # Verificar que Firebase esté inicializado
            from models.firebase import db, is_initialized
            if not is_initialized or db is None:
                print("Firebase no está disponible")
                return
                
            try:
                # Referencia CORRECTA al historial
                historial_ref = db.collection("pacientes").document(paciente_id).collection("historial")
                
                from firebase_admin import firestore
                
                # Consulta ordenada por timestamp
                query = historial_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
                resultados = query.stream()
                
                historial_encontrado = False
                
                for doc in resultados:
                    historial_data = doc.to_dict()
                    historial_encontrado = True
                    
                    historial_box=BoxLayout(
                        orientation='vertical',
                        size_hint_y=None,
                        height=180,
                        spacing=5,
                        padding=10
                    )
                    
                    historial_box.add_widget(Label(
                        text="[b]Última atención médica:[/b]",
                        markup=True,
                        size_hint_y=None,
                        height=30,
                        color=(0.2, 0.4, 0.8, 1)
                    ))
                    
                    fecha_atencion=historial_data.get('fecha', 'Fecha no disponible')
                    
                    historial_box.add_widget(Label(
                        text=f"Fecha: {fecha_atencion}",
                        size_hint_y=None,
                        height=25,
                        haling='left'
                    ))
                    
                    # Diagnóstico (truncado si es muy largo)
                    diagnostico = historial_data.get('diagnostico', 'Sin diagnóstico registrado')
                    if len(diagnostico) > 60:
                        diagnostico = diagnostico[:57] + "..."
                    historial_box.add_widget(Label(
                        text=f"🏥 Diagnóstico: {diagnostico}",
                        size_hint_y=None,
                        height=25,
                        halign='left',
                        text_size=(None, None),
                        shorten=True
                    ))
                    
                    # Tratamiento (truncado si es muy largo)
                    tratamiento = historial_data.get('tratamiento', 'Sin tratamiento registrado')
                    if len(tratamiento) > 60:
                        tratamiento = tratamiento[:57] + "..."
                    historial_box.add_widget(Label(
                        text=f"💊 Tratamiento: {tratamiento}",
                        size_hint_y=None,
                        height=25,
                        halign='left',
                        text_size=(None, None),
                        shorten=True
                    ))
                    
                    # Total de la atención
                    total = historial_data.get('total', 0)
                    historial_box.add_widget(Label(
                        text=f"💰 Total: ${total:,}",
                        size_hint_y=None,
                        height=25,
                        halign='left',
                        color=(0.2, 0.6, 0.2, 1)
                    ))
                    
                    # Número de procedimientos
                    procedimientos = historial_data.get('procedimientos', [])
                    historial_box.add_widget(Label(
                        text=f"📋 Procedimientos: {len(procedimientos)}",
                        size_hint_y=None,
                        height=25,
                        halign='left'
                    ))
                    
                    # Agregar al layout principal
                    self.result_layout.add_widget(historial_box)
                    break
                    
                if not historial_encontrado:
                    # Mostrar mensaje si no hay historial
                    no_historial_label = Label(
                        text="No se encontró historial médico para este paciente",
                        size_hint_y=None,
                        height=40,
                        color=(0.8, 0.2, 0.2, 1),
                        italic=True
                    )
                    self.result_layout.add_widget(no_historial_label)
                    
            except Exception as e:
                print(f"❌ Error en consulta de historial: {e}")
                
        except Exception as e:
            print(f"❌ Error general en mostrar_ultimo_historial: {e}")
        
    
    def volver(self, instance):
        self.manager.current = 'main'