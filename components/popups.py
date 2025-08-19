from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable
from components.inputs import RUTTextInput, PhoneTextInput
from components.security import Security
from models.firebase import db, auth
from models.horario import HorarioManager 
from datetime import datetime
import re
from kivy.clock import Clock
from firebase_admin import firestore

class NuevoPacientePopup(Popup):
    def __init__(self, guardar_callback, **kwargs):
        super().__init__(**kwargs)
        self.guardar_callback = guardar_callback
        self.title = "Nuevo Paciente"
        self.size_hint = (0.9, 0.9)
        
        layout = GridLayout(cols=1, spacing=10, padding=10)
        
        self.nombre_input = TextInput(
            hint_text="Nombre (solo letras y espacios)", 
            multiline=False
        )
        self.apellido_input = TextInput(
            hint_text="Apellido", 
            multiline=False
        )
        self.rut_input = RUTTextInput(
            hint_text="RUT (ej: 12345678-9)", 
            multiline=False
        )
        self.fecha_nac_input = TextInput(
            hint_text="Fecha de nacimiento (DD-MM-YYYY)", 
            multiline=False
        )
        self.telefono_input = PhoneTextInput(
            hint_text="Teléfono", 
            multiline=False
        )
        self.email_input = TextInput(
            hint_text="Email", 
            multiline=False
        )
        
        btn_guardar = Button(
            text="Guardar", 
            size_hint_y=None, 
            height=50,
            background_color=(0.1, 0.7, 0.3, 1)
        )
        btn_guardar.bind(on_press=self.guardar)
        
        layout.add_widget(Label(
            text="Datos del Paciente:", 
            font_size='18sp',
            bold=True
        ))
        layout.add_widget(self.nombre_input)
        layout.add_widget(self.apellido_input)
        layout.add_widget(self.rut_input)
        layout.add_widget(self.fecha_nac_input)
        layout.add_widget(self.telefono_input)
        layout.add_widget(self.email_input)
        layout.add_widget(btn_guardar)
        
        self.content = layout
    
    def guardar(self, instance):
        nombre = Security.sanitize_name(self.nombre_input.text)
        apellido = Security.sanitize_name(self.apellido_input.text)
        rut = Security.sanitize_rut(self.rut_input.text)
        fecha_nac = self.fecha_nac_input.text.strip()
        telefono = self.telefono_input.text.strip()
        email = self.email_input.text.strip().lower()
        
        errors = []
        if not nombre:
            errors.append("Nombre inválido (solo letras y espacios)")
        if not apellido:
            errors.append("Apellido inválido (solo letras y espacios)")
        
        is_rut_valid, rut_msg = Security.validar_rut(self.rut_input.text)
        if not is_rut_valid:
            errors.append(f"RUT: {rut_msg}")
        
        try:
            datetime.strptime(fecha_nac, "%d-%m-%Y")
        except ValueError:
            errors.append("Fecha debe tener formato DD-MM-YYYY")
        
        if not Security.validate_phone(telefono):
            errors.append("Teléfono debe tener 8-15 dígitos (puede incluir + al inicio)")
        
        if not Security.validate_email(email):
            errors.append("Email no válido")
        
        if errors:
            self.mostrar_error("\n".join(errors))
            return
        
        try:
            user = auth.create_user(
                email=email,
                password=rut.replace("-", ""),
                display_name=f"{nombre} {apellido}"
            )
            uid = user.uid
            
            paciente_data = {
                "nombre": nombre,
                "apellido": apellido,
                "rut": rut,
                "fecha_nacimiento": fecha_nac,
                "telefono": telefono,
                "email": email,
                "fecha_registro": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "uid": uid
            }
            
            db.collection("pacientes").document(uid).set(paciente_data)
            self.guardar_callback(paciente_data)
            self.dismiss()
            
        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                error_msg = "El email ya está registrado"
            self.mostrar_error(f"Error al crear usuario: {error_msg}")
    
    def mostrar_error(self, mensaje):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text=mensaje))
        close_btn = Button(text="Cerrar", size_hint_y=None, height=50)
        popup = Popup(
            title="Error", 
            content=content,
            size_hint=(0.8, 0.5)
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

class CitaPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Nueva Cita"
        self.size_hint = (0.9, 0.8)
        self.current_step = 1
        self.fecha_seleccionada = None
        self.hora_seleccionada = None
        
        self.layout_principal = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.content = self.layout_principal
        
        self.mostrar_paso_fecha()
    
    def mostrar_paso_fecha(self):
        self.current_step = 1
        self.layout_principal.clear_widgets()
        
        self.layout_principal.add_widget(Label(
            text="Seleccione la fecha para la cita:", 
            font_size='18sp',
            size_hint_y=None,
            height=40
        ))
        
        self.fecha_input = TextInput(
            hint_text="Fecha (DD-MM-YYYY)",
            text=datetime.now().strftime("%d-%m-%Y"),
            size_hint_y=None,
            height=50
        )
        self.fecha_input.bind(text=self.actualizar_horarios_disponibles)
        self.layout_principal.add_widget(self.fecha_input)
        
        btn_calendario = Button(
            text="Seleccionar del calendario",
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.5, 0.8, 1)
        )
        btn_calendario.bind(on_press=self.mostrar_calendario)
        self.layout_principal.add_widget(btn_calendario)
        
        self.horarios_container = BoxLayout(orientation='vertical', spacing=5)
        
        scroll_horarios = ScrollView(size_hint=(1, 0.6))
        self.grid_horarios = GridLayout(cols=3, spacing=5, size_hint_y=None)
        self.grid_horarios.bind(minimum_height=self.grid_horarios.setter('height'))
        scroll_horarios.add_widget(self.grid_horarios)
        self.horarios_container.add_widget(scroll_horarios)
        
        self.layout_principal.add_widget(self.horarios_container)
        
        btn_continuar = Button(
            text="Continuar",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            disabled=True
        )
        btn_continuar.bind(on_press=self.mostrar_paso_datos_paciente)
        self.btn_continuar = btn_continuar
        self.layout_principal.add_widget(btn_continuar)
        
        self.actualizar_horarios_disponibles(None, self.fecha_input.text)
    
    def mostrar_calendario(self, instance):
        from kivymd.uix.pickers import MDDatePicker
    
        def on_save(instance, value, date_range):
            self.fecha_input.text = value.strftime("%d-%m-%Y")
    
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=on_save)
        date_dialog.open()
    
    def actualizar_horarios_disponibles(self, instance, value):
        try:
            datetime.strptime(value, "%d-%m-%Y")
            self.fecha_seleccionada = value
        except ValueError:
            self.grid_horarios.clear_widgets()
            self.grid_horarios.add_widget(Label(
                text="Formato de fecha inválido (DD-MM-YYYY)",
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=40
            ))
            self.btn_continuar.disabled = True
            return
        
        horarios_disponibles = HorarioManager.generar_horarios_disponibles(value)
        horarios_ocupados = self.obtener_horarios_ocupados(value)
        
        self.grid_horarios.clear_widgets()
        self.hora_seleccionada = None
        self.btn_continuar.disabled = True
        
        if not horarios_disponibles:
            self.grid_horarios.add_widget(Label(
                text="No hay horarios disponibles para esta fecha",
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=40
            ))
            return
        
        for hora in HorarioManager.generar_todos_horarios_posibles():
            btn = Button(
                text=hora,
                size_hint_y=None,
                height=40,
                background_color=(0.8, 0.2, 0.2, 1) if hora in horarios_ocupados else (0.2, 0.8, 0.2, 1) if hora in horarios_disponibles else (0.8, 0.8, 0.8, 1),
                disabled=(hora not in horarios_disponibles))
            
            if hora in horarios_disponibles:
                btn.bind(on_press=lambda x, h=hora: self.seleccionar_hora(h))
            
            self.grid_horarios.add_widget(btn)
    
    def obtener_horarios_ocupados(self, fecha):
        try:
            citas_ref = db.collection("citas")
            query = citas_ref.where("fecha", "==", fecha).stream()
            
            horarios_ocupados = []
            for cita in query:
                cita_data = cita.to_dict()
                horarios_ocupados.append(cita_data["hora"])
            
            return horarios_ocupados
        except Exception as e:
            print(f"Error obteniendo horarios ocupados: {e}")
            return []
    
    def seleccionar_hora(self, hora):
        self.hora_seleccionada = hora
        self.btn_continuar.disabled = False
        
        for child in self.grid_horarios.children:
            if child.text == hora:
                child.background_color = (0.2, 0.6, 0.8, 1)
            elif not child.disabled:
                child.background_color = (0.2, 0.8, 0.2, 1)
    
    def mostrar_paso_datos_paciente(self, instance):
        self.current_step = 2
        self.layout_principal.clear_widgets()
        
        self.layout_principal.add_widget(Label(
            text=f"Cita para el {self.fecha_seleccionada} a las {self.hora_seleccionada}",
            font_size='18sp',
            size_hint_y=None,
            height=40
        ))
        
        self.rut_input = RUTTextInput(
            hint_text="RUT del Paciente (ej: 12345678-9)",
            size_hint_y=None,
            height=50
        )
        self.layout_principal.add_widget(self.rut_input)
        
        self.motivo_input = TextInput(
            hint_text="Motivo de la cita",
            multiline=True,
            size_hint=(1, 0.3)
        )
        self.layout_principal.add_widget(self.motivo_input)
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        btn_volver = Button(
            text="Volver",
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_volver.bind(on_press=self.mostrar_paso_fecha)
        
        btn_guardar = Button(
            text="Guardar Cita",
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_guardar.bind(on_press=self.guardar_cita)
        
        btn_layout.add_widget(btn_volver)
        btn_layout.add_widget(btn_guardar)
        self.layout_principal.add_widget(btn_layout)
    
    def guardar_cita(self, instance):
        rut = Security.sanitize_rut(self.rut_input.text)
        motivo = self.motivo_input.text.strip()
        
        errors = []
        
        is_rut_valid, rut_msg = Security.validar_rut(self.rut_input.text)
        if not is_rut_valid:
            errors.append(f"RUT: {rut_msg}")
        
        if not motivo:
            errors.append("Debe ingresar un motivo para la cita")
        
        if errors:
            Popup(title="Error", content=Label(text="\n".join(errors)), size_hint=(0.8, 0.4)).open()
            return
        
        try:
            pacientes_ref = db.collection("pacientes")
            query = pacientes_ref.where("rut", "==", rut).limit(1)
            results = query.stream()
            
            paciente_data = None
            for doc in results:
                paciente_data = doc.to_dict()
                break
            
            if not paciente_data:
                raise ValueError("No se encontró paciente con ese RUT")
            
            cita_data = {
                "paciente_rut": rut,
                "paciente_nombre": f"{paciente_data['nombre']} {paciente_data['apellido']}",
                "fecha": self.fecha_seleccionada,
                "hora": self.hora_seleccionada,
                "motivo": motivo,
                "creado_en": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "estado": "pendiente"
            }
            
            db.collection("citas").add(cita_data)
            Popup(title="Éxito", content=Label(text="Cita agendada correctamente"), size_hint=(0.8, 0.4)).open()
            self.dismiss()
            
        except Exception as e:
            Popup(title="Error", content=Label(text=f"Error al agendar cita: {str(e)}"), size_hint=(0.8, 0.4)).open()

class BuscarPacientePopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Buscar Paciente"
        self.size_hint = (0.9, 0.8)
        
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        search_layout = BoxLayout(size_hint_y=None, height=50)
        self.rut_input = RUTTextInput(hint_text="Ingrese RUT del paciente (ej: 12345678-9)", size_hint_x=0.8)
        
        btn_buscar = Button(
            text="Buscar",
            size_hint_x=0.2,
            background_color=(0.3, 0.5, 0.8, 1)
        )
        btn_buscar.bind(on_press=self.buscar_paciente)
        
        search_layout.add_widget(self.rut_input)
        search_layout.add_widget(btn_buscar)
        layout.add_widget(search_layout)
        
        self.result_container = ScrollView()
        self.result_layout = BoxLayout(
            orientation='vertical', 
            size_hint_y=None,
            spacing=10,
            padding=10
        )
        self.result_layout.bind(minimum_height=self.result_layout.setter('height'))
        
        self.result_container.add_widget(self.result_layout)
        layout.add_widget(self.result_container)
        
        self.content = layout
    
    def buscar_paciente(self, instance):
        rut = Security.sanitize_rut(self.rut_input.text)
        self.result_layout.clear_widgets()
        
        spinner = BoxLayout(orientation='vertical', size_hint_y=None, height=100)
        spinner.add_widget(Label(text="Buscando paciente..."))
        self.result_layout.add_widget(spinner)
        
        Clock.schedule_once(lambda dt: self._realizar_busqueda(rut), 0.1)
    
    def _realizar_busqueda(self, rut):
        self.result_layout.clear_widgets()
        
        is_rut_valid, rut_msg = Security.validar_rut(self.rut_input.text)
        if not is_rut_valid:
            self.result_layout.add_widget(Label(
                text=f"Error: {rut_msg}", 
                color=(1, 0, 0, 1), 
                size_hint_y=None, 
                height=40
            ))
            return
        
        try:
            pacientes_ref = db.collection("pacientes")
            query = pacientes_ref.where("rut", "==", rut).limit(1)
            results = query.stream()
            
            paciente_data = None
            paciente_id = None
            for doc in results:
                paciente_data = doc.to_dict()
                paciente_id = doc.id
                break
            
            if paciente_data:
                info_layout = GridLayout(cols=2, size_hint_y=None, height=150, spacing=10)
                info_layout.add_widget(Label(text="Nombre:", size_hint_x=0.3))
                info_layout.add_widget(Label(
                    text=f"{paciente_data['nombre']} {paciente_data['apellido']}", 
                    size_hint_x=0.7, 
                    halign='left'
                ))
                info_layout.add_widget(Label(text="RUT:", size_hint_x=0.3))
                info_layout.add_widget(Label(text=paciente_data['rut'], size_hint_x=0.7))
                info_layout.add_widget(Label(text="Teléfono:", size_hint_x=0.3))
                info_layout.add_widget(Label(text=paciente_data['telefono'], size_hint_x=0.7))
                info_layout.add_widget(Label(text="Email:", size_hint_x=0.3))
                info_layout.add_widget(Label(text=paciente_data['email'], size_hint_x=0.7))
                
                self.result_layout.add_widget(info_layout)
                
                btn_historial = Button(
                    text="Ver Historial Médico Completo",
                    size_hint_y=None,
                    height=50,
                    background_color=(0.3, 0.5, 0.7, 1)
                )
                btn_historial.bind(on_press=lambda x: self.mostrar_historial_completo(paciente_id, paciente_data))
                self.result_layout.add_widget(btn_historial)
                
                self.mostrar_ultimo_historial(paciente_id)
            else:
                self.result_layout.add_widget(Label(
                    text="No se encontró paciente con ese RUT",
                    size_hint_y=None,
                    height=40
                ))
        
        except Exception as e:
            self.result_layout.add_widget(Label(
                text=f"Error en la búsqueda: {str(e)}",
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=40
            ))
    
    def mostrar_ultimo_historial(self, paciente_id):
        try:
            from firebase_admin import firestore
            
            historial_ref = db.collection("pacientes").document(paciente_id).collection("historial")
            query = historial_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
            
            resultados = query.stream()
            
            for doc in resultados:
                historial_data = doc.to_dict()
                
                historial_box = BoxLayout(
                    orientation='vertical',
                    size_hint_y=None,
                    height=150,
                    spacing=5
                )
                
                historial_box.add_widget(Label(
                    text="[b]Última atención médica:[/b]",
                    markup=True,
                    size_hint_y=None,
                    height=30
                ))
                
                historial_box.add_widget(Label(
                    text=f"Fecha: {historial_data.get('fecha', 'No registrada')}",
                    size_hint_y=None,
                    height=25
                ))
                
                diagnostico = historial_data.get('diagnostico', 'Sin diagnóstico')
                if len(diagnostico) > 50:
                    diagnostico = diagnostico[:50] + "..."
                historial_box.add_widget(Label(
                    text=f"Diagnóstico: {diagnostico}",
                    size_hint_y=None,
                    height=25
                ))
                
                tratamiento = historial_data.get('tratamiento', 'Sin tratamiento')
                if len(tratamiento) > 50:
                    tratamiento = tratamiento[:50] + "..."
                historial_box.add_widget(Label(
                    text=f"Tratamiento: {tratamiento}",
                    size_hint_y=None,
                    height=25
                ))
                
                self.result_layout.add_widget(historial_box)
                break
                
        except Exception as e:
            print(f"Error cargando historial: {e}")
            self.result_layout.add_widget(Label(
                text="No se pudo cargar el historial médico",
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=40
            ))
    
    def mostrar_historial_completo(self, paciente_id, paciente_data):
        popup = HistorialMedicoPopup(paciente_data)
        popup.open()

class HistorialMedicoPopup(Popup):
    def __init__(self, paciente_data, **kwargs):
        super().__init__(**kwargs)
        self.title = f"Historial Médico: {paciente_data['nombre']}"
        self.size_hint = (0.9, 0.8)
        self.paciente_data = paciente_data
        
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        scroll = ScrollView()
        historial_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        historial_layout.bind(minimum_height=historial_layout.setter('height'))
        
        btn_nueva_atencion = Button(
            text="Agregar Atención",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        btn_nueva_atencion.bind(on_press=self.abrir_nueva_atencion)
        
        self.cargar_historial(historial_layout)
        
        scroll.add_widget(historial_layout)
        layout.add_widget(btn_nueva_atencion)
        layout.add_widget(scroll)
        self.content = layout
    
    def cargar_historial(self, layout):
        try:
            historial_ref = db.collection("pacientes").document(self.paciente_data['uid']).collection("historial")
            atenciones = historial_ref.order_by("fecha", direction=firestore.Query.DESCENDING).stream()
            
            for atencion in atenciones:
                atencion_data = atencion.to_dict()
                fecha = atencion_data.get("fecha", "Sin fecha")
                diagnostico = atencion_data.get("diagnostico", "Sin diagnóstico")
                tratamiento = atencion_data.get("tratamiento", "Sin tratamiento")
                procedimientos = atencion_data.get("procedimientos", [])
                
                item = BoxLayout(
                    orientation='vertical',
                    size_hint_y=None,
                    height=200,
                    spacing=5
                )
                
                header = BoxLayout(size_hint_y=None, height=30)
                header.add_widget(Label(text=f"Fecha: {fecha}", size_hint_x=0.7))
                header.add_widget(Label(text=f"Total: ${atencion_data.get('total', 0):,}", size_hint_x=0.3))
                item.add_widget(header)
                
                item.add_widget(Label(text=f"Diagnóstico: {diagnostico}", size_hint_y=None, height=30))
                item.add_widget(Label(text=f"Tratamiento: {tratamiento}", size_hint_y=None, height=30))
                
                scroll_proc = ScrollView(size_hint_y=None, height=100)
                proc_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
                proc_layout.bind(minimum_height=proc_layout.setter('height'))
                
                for proc in procedimientos:
                    proc_text = f"{proc['descripcion']} (${proc['valor']:,})"
                    if 'imagen' in proc:
                        btn_imagen = Button(
                            text=f"Ver imagen de {proc['descripcion'][:10]}...",
                            size_hint_y=None,
                            height=30,
                            background_color=(0.4, 0.6, 0.8, 0.3)
                        )
                        btn_imagen.bind(on_press=lambda x, url=proc['imagen']: self.mostrar_imagen_completa(url))
                        proc_layout.add_widget(btn_imagen)
                    else:
                        proc_layout.add_widget(Label(text=proc_text, size_hint_y=None, height=30))
                
                scroll_proc.add_widget(proc_layout)
                item.add_widget(scroll_proc)
                
                layout.add_widget(item)
        
        except Exception as e:
            print(f"Error cargando historial: {e}")

    def mostrar_imagen_completa(self, image_url):
        content = BoxLayout(orientation='vertical')
        img = Image(
            source=image_url,
            size_hint=(1, 0.9),
            allow_stretch=True
        )
        btn_close = Button(text="Cerrar", size_hint_y=None, height=50)
        
        popup = Popup(
            title="Imagen del Procedimiento",
            content=content,
            size_hint=(0.9, 0.9)
        )
        
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(img)
        content.add_widget(btn_close)
        popup.open()
    
    def abrir_nueva_atencion(self, instance):
        popup = NuevaAtencionPopup(self.paciente_data, self.actualizar_historial)
        popup.open()
    
    def actualizar_historial(self):
        self.content.clear_widgets()
        scroll = ScrollView()
        historial_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        historial_layout.bind(minimum_height=historial_layout.setter('height'))
        
        btn_nueva_atencion = Button(
            text="Agregar Atención",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        btn_nueva_atencion.bind(on_press=self.abrir_nueva_atencion)
        
        self.cargar_historial(historial_layout)
        
        scroll.add_widget(historial_layout)
        self.content.add_widget(btn_nueva_atencion)
        self.content.add_widget(scroll)

class NuevaAtencionPopup(Popup):
    def __init__(self, paciente_data, callback_actualizar, **kwargs):
        super(NuevaAtencionPopup, self).__init__(**kwargs)
        self.title = f"Nueva Atención para {paciente_data['nombre']}"
        self.size_hint = (0.9, 0.8)
        self.paciente_data = paciente_data
        self.callback_actualizar = callback_actualizar
        self.procedimientos = []
        
        layout = BoxLayout(orientation='vertical', spacing=5, padding=5)
        
        btn_guardar_proc=Button(
            text="Guardar Procedimientos",
            size_hint_y=None,
            height=10,
            background_color=(0.3, 0.6, 0.9, 1)
        )
        btn_guardar_proc.bind(on_press=self.guardar_procedimiento)
        layout.add_widget(btn_guardar_proc)
        
        self.fecha_input = TextInput(
            hint_text="Fecha de atención (DD-MM-YYYY)",
            text=datetime.now().strftime("%d-%m-%Y"),
            size_hint_y=None,
            height=40,  # Reducido de 50 a 40 (o incluso 35 si prefieres más pequeño)
            font_size='14sp'  # Fuente un poco más pequeña
        )
        layout.add_widget(self.fecha_input)
        
        procedimientos_layout = BoxLayout(orientation='vertical', spacing=5)
        procedimientos_layout.add_widget(Label(text="Procedimientos:", size_hint_y=None, height=20))
        
        self.procedimientos_container = GridLayout(cols=1, spacing=5, size_hint_y=None, height=200)
        self.procedimientos_container.bind(minimum_height=self.procedimientos_container.setter('height'))
        
        scroll_procedimientos = ScrollView(
            size_hint=(1.0, 0.3),
            bar_width=8
        )
            
        scroll_procedimientos.add_widget(self.procedimientos_container)
        procedimientos_layout.add_widget(scroll_procedimientos)
        
        btn_agregar_proc = Button(
            text="Agregar Procedimiento",
            size_hint_y=None,
            height=30,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn_agregar_proc.bind(on_press=self.agregar_procedimiento)
        procedimientos_layout.add_widget(btn_agregar_proc)
        
        self.diagnostico_input = TextInput(
            hint_text="Diagnóstico", 
            multiline=True, 
            size_hint_y=None, 
            height=30
        )
        self.tratamiento_input = TextInput(
            hint_text="Tratamiento", 
            multiline=True, 
            size_hint_y=None, 
            height=30
        )
        
        self.lbl_total = Label(
            text="Total: $0", 
            size_hint_y=None, 
            height=20, 
            font_size='18sp', 
            bold=True
        )
        
        btn_guardar = Button(
            text="Guardar Atención",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_guardar.bind(on_press=self.guardar_atencion)
        
        layout.add_widget(procedimientos_layout)
        layout.add_widget(Label(text="Diagnóstico:", size_hint_y=None, height=20))
        layout.add_widget(self.diagnostico_input)
        layout.add_widget(Label(text="Tratamiento:", size_hint_y=None, height=20))
        layout.add_widget(self.tratamiento_input)
        layout.add_widget(self.lbl_total)
        layout.add_widget(btn_guardar)
        
        self.content = layout
        self.agregar_procedimiento()
        self.content=layout
        
    def guardar_procedimiento(self, instance):
        if not self.procedimientos:
            return
        desc, valor, imagen=self.procedimientos[-1]
        
        if not desc.text.strip():
            Popup(title="Error",
                  content=Label(text="Debe ingresar una descripción"),
                  size_hint=(0.7, 0.3)).open()
            return
        
        try:
            int(valor.text)
        except ValueError:
            Popup(title="Error",
                  content=Label(text="El valor debe ser numérico"),
                  size_hint=(0.7, 0.3)).open()
            return
        
        self.agregar_procedimiento()
    
    def agregar_procedimiento(self, instance=None):
        proc_layout = BoxLayout(
            size_hint_y=None,
            height=40,
            spacing=5
        )
        
        proc_desc = TextInput(
            hint_text="Descripción",
            size_hint_x=0.5,
            font_size='12sp'
        )
        
        proc_valor = TextInput(
            hint_text="Valor",
            input_filter='int',
            size_hint_x=0.3,
            font_size='12sp',
            multiline=False
        )
        
        btn_eliminar = Button(
            text="X",
            size_hint_x=0.1,
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='10sp'
        )
        btn_eliminar.bind(on_press=lambda x: self.eliminar_procedimiento(proc_layout))
        
        btn_imagen = Button(
            text="📷", 
            size_hint_x=0.1,
            background_color=(0.4, 0.6, 0.8, 1),
            font_size='12sp'
        )
        btn_imagen.bind(on_press=lambda x: self.agregar_imagen_procedimiento(proc_layout))
        
        proc_layout.add_widget(proc_desc)
        proc_layout.add_widget(proc_valor)
        proc_layout.add_widget(btn_eliminar)
        proc_layout.add_widget(btn_imagen)
        
        self.procedimientos_container.add_widget(proc_layout)
        self.procedimientos.append((proc_desc, proc_valor, None))
        self.calcular_total()
        
    def eliminar_procedimiento(self, layout):
        for i, (desc, valor, imagen) in enumerate(self.procedimientos):
            if desc.parent==layout:
                del self.procedimientos[i]
                break
        self.procedimientos_container.remove_widget(layout)
        self.calcular_total()
    
    def calcular_total(self, *args):
        total = 0
        for desc, valor, _ in self.procedimientos:
            try:
                total += int(valor.text) if valor.text.strip() else 0
            except ValueError:
                pass
        self.lbl_total.text = f"Total: ${total:,}"
    
    def guardar_atencion(self, instance):
        fecha = self.fecha_input.text.strip()
        diagnostico = self.diagnostico_input.text.strip()
        tratamiento = self.tratamiento_input.text.strip()
        
        try:
            datetime.strptime(fecha, "%d-%m-%Y")
        except ValueError:
            Popup(title="Error", content=Label(text="Formato de fecha inválido (DD-MM-YYYY)"), size_hint=(0.8, 0.4)).open()
            return
        
        if not diagnostico:
            Popup(title="Error", content=Label(text="Debe ingresar un diagnóstico"), size_hint=(0.8, 0.4)).open()
            return
        
        procedimientos = []
        total = 0
        for desc, valor, imagen in self.procedimientos:
            desc_text = desc.text.strip()
            try:
                valor_num = int(valor.text) if valor.text.strip() else 0
            except ValueError:
                valor_num = 0
            
            if desc_text:
                procedimiento={
                    "descripcion": desc_text,
                    "valor": valor_num
                }
                
                if imagen:  
                    imagen_url = self.subir_imagen_firebase(imagen)
                    procedimiento["imagen"] = imagen_url
            
                procedimientos.append(procedimiento)
                total += valor_num
        
        try:
            atencion_data = {
                "fecha": fecha,
                "diagnostico": diagnostico,
                "tratamiento": tratamiento,
                "procedimientos": procedimientos,
                "total": total,
                "timestamp": datetime.now().timestamp()
            }
            
            db.collection("pacientes").document(self.paciente_data['uid']).collection("historial").add(atencion_data)
            
            ingreso_data = {
                "paciente_id": self.paciente_data['uid'],
                "paciente_nombre": f"{self.paciente_data['nombre']} {self.paciente_data['apellido']}",
                "fecha": fecha,
                "total": total,
                "procedimientos": procedimientos,
                "timestamp": datetime.now().timestamp()
            }
            db.collection("ingresos").add(ingreso_data)
            
            self.callback_actualizar()
            self.dismiss()
            Popup(title="Éxito", content=Label(text="Atención médica guardada"), size_hint=(0.8, 0.4)).open()
        
        except Exception as e:
            Popup(title="Error", content=Label(text=f"Error al guardar atención: {str(e)}"), size_hint=(0.8, 0.4)).open()
            
    def subir_imagen_firebase(self, image_path):
        try:
            from firebase_admin import storage
            import uuid
            
            bucket = storage.bucket()
            blob = bucket.blob(f"procedimientos/{uuid.uuid4()}.jpg")
            
            blob.upload_from_filename(image_path)
            blob.make_public()
            
            return blob.public_url
        except Exception as e:
            print(f"Error subiendo imagen: {e}")
            return None
        
    def agregar_imagen_procedimiento(self, instance):
        """Método para manejar la adición de imágenes a procedimientos"""
        from kivy.uix.filechooser import FileChooserIconView
        from kivy.uix.popup import Popup
        
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView()
        
        def seleccionar_imagen(selection):
            if selection:
                # Aquí guardamos la ruta de la imagen en el procedimiento
                for i, (desc, valor, _) in enumerate(self.procedimientos):
                    if desc.parent == instance.parent:
                        self.procedimientos[i] = (desc, valor, selection[0])
                        break
            popup.dismiss()
        
        btn_select = Button(text='Seleccionar', size_hint_y=None, height=50)
        btn_select.bind(on_press=lambda x: seleccionar_imagen(file_chooser.selection))
        
        content.add_widget(file_chooser)
        content.add_widget(btn_select)
        
        popup = Popup(title='Seleccionar imagen', content=content, size_hint=(0.9, 0.9))
        popup.open()    
        