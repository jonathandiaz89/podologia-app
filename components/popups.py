from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from datetime import datetime, timedelta
from models.firebase import get_db, get_auth
from kivy.clock import Clock
from firebase_admin import firestore
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image

def some_method(self):
    db = get_db()
    auth = get_auth()
    if db and auth

# Diccionario de servicios y precios
SERVICIOS_PRECIOS = {
    "Consulta General": 17000,
    "Tratamiento de Uñas Encarnadas": 19000,
    "Tratamiento de Hongos": 10000,
    "Curaciones y Heridas": 7000,
    "Tratamiento uña encarnada con anestesia": 24000
}

class HorarioManager:
    @staticmethod
    def generar_todos_horarios_posibles():
        """Generar todos los horarios posibles del día"""
        horarios = []
        for hora in range(9, 20):  # De 9 AM a 8 PM
            for minuto in [0, 30]:  # Cada 30 minutos
                horarios.append(f"{hora:02d}:{minuto:02d}")
        return horarios

    @staticmethod
    def generar_horarios_disponibles(fecha):
        """Generar horarios disponibles para una fecha verificando contra Firebase"""
        try:
            #Obtener todos los horarios disponibles
            todos_horarios=HorarioManager.generar_todos_horarios_posibles()
            
            #Obtener horarios ya ocupados desde Firebase
            horarios_ocupados=[]
            
            try:
                citas_ref=db.collection("citas")
                #Usa la nueva sintaxis de Firebase con filter=
                query=citas_ref.where(
                    filter=firestore.FieldFilter("fecha", "==", fecha)
                ).where(
                    filter=firestore.FieldFilter("estado", "!=", "anulada")
                ).stream()
                
                for citas in query:
                    cita_data=citas.to_dict()
                    hora_cita=cita_data.get("hora")
                    if hora_cita and hora_cita in todos_horarios:
                        horarios_ocupados.append(hora_cita)
                        
            except Exception as e:
                print(f"Error consultando horarios ocupados: {e}")
                #Si hay error, asumir que todos están disponibles
                return todos_horarios
            #Filtrar horarios disponibles (los que NO están ocupados)
            horarios_disponibles=[hora for hora in todos_horarios if hora not in horarios_ocupados]
            
            return horarios_disponibles
        except Exception as e:
            print(f"Error generando horarios disponibles: {e}")
            #En caso de error, retornar horarios por defecto
            return HorarioManager.generar_todos_horarios_posibles()
    
    @staticmethod
    def esta_horario_disponible(fecha, hora):
        """Verificar si un horario específico está disponible"""
        try:
            citas_ref=db.collection("citas")
            query=citas_ref.where(
                filter=firestore.FieldFilter("fecha", "==", fecha)
            ).where(
                filter=firestore.FieldFilter("hora", "==", hora)
            ).where(
                filter=firestore.FieldFilter("estado", "!=", "anulada")
            ).limit(1).stream()
            
            #Si hay resultados, el horario está ocupado
            for _ in query:
                return False
            
            return True
        except Exception as e:
            print(f"Error verificando horarios: {e}")
            return False
        
    @staticmethod
    def obtener_horarios_ocupados(fecha):
        """Obtener lista de horarios ocupados para una fecha"""
        try:
            horarios_ocupados=[]
            citas_ref=db.collection("citas")
            query=citas_ref.where(
                filter=firestore.FieldFilter("fecha", "==", fecha)
            ).where(
                filter=firestore.FieldFilter("estado", "!=", "anulada")
            ).stream()
            
            for cita in query:
                cita_data=cita.to_dict()
                hora=cita_data.get("hora")
                if hora:
                    horarios_ocupados.append(hora)
                    
            return horarios_ocupados
        except Exception as e:
            print(f"Error obteniendo horarios ocupados: {e}")
            return []
        

class CitaPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Crear Nueva Cita"
        self.size_hint = (0.9, 0.9)
        self.fecha_seleccionada = None
        self.hora_seleccionada = None
        self.paciente_data = None
        
        self.layout_principal = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.content = self.layout_principal
        
        self.mostrar_selector_fecha_hora()
    
    def mostrar_selector_fecha_hora(self, instance=None):
        """Mostrar selector de fecha y hora"""
        self.layout_principal.clear_widgets()
        
        # Título
        titulo = Label(
            text="Seleccione Fecha y Hora para la Cita",
            font_size='18sp',
            bold=True,
            size_hint_y=None,
            height=40
        )
        self.layout_principal.add_widget(titulo)
        
        # Selector de fecha
        fecha_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        fecha_layout.add_widget(Label(text="Fecha (DD-MM-YYYY):", size_hint_x=0.4))
        
        self.fecha_input = TextInput(
            text=datetime.now().strftime("%d-%m-%Y"),
            size_hint_x=0.6
        )
        self.fecha_input.bind(text=self.actualizar_horarios_disponibles)
        fecha_layout.add_widget(self.fecha_input)
        
        self.layout_principal.add_widget(fecha_layout)
        
        # Horarios disponibles
        horarios_label = Label(
            text="Horarios Disponibles:",
            font_size='16sp',
            size_hint_y=None,
            height=30
        )
        self.layout_principal.add_widget(horarios_label)
        
        # Grid de horarios
        scroll_horarios = ScrollView(size_hint_y=0.6)
        self.grid_horarios = GridLayout(cols=4, spacing=5, size_hint_y=None)
        self.grid_horarios.bind(minimum_height=self.grid_horarios.setter('height'))
        scroll_horarios.add_widget(self.grid_horarios)
        self.layout_principal.add_widget(scroll_horarios)
        
        # Botón continuar
        self.btn_continuar = Button(
            text="Continuar con Formulario",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 0.2, 1),
            disabled=True
        )
        self.btn_continuar.bind(on_press=self.mostrar_formulario_cita)
        self.layout_principal.add_widget(self.btn_continuar)
        
        # Cargar horarios iniciales
        self.actualizar_horarios_disponibles(None, self.fecha_input.text)
    
    def actualizar_horarios_disponibles(self, instance, value):
        """Actualizar la lista de horarios disponibles"""
        try:
            # Validar fecha
            datetime.strptime(value, "%d-%m-%Y")
            self.fecha_seleccionada = value
        except ValueError:
            self.mostrar_error_fecha("Formato de fecha inválido (DD-MM-YYYY)")
            return
        
        # Obtener horarios disponibles REALES desde Firebase
        horarios_disponibles=HorarioManager.generar_horarios_disponibles(value)
                
        self.grid_horarios.clear_widgets()
        self.hora_seleccionada = None
        self.btn_continuar.disabled = True
        
        for hora in HorarioManager.generar_todos_horarios_posibles():
            disponible = hora in horarios_disponibles
                        
            btn = Button(
                text=hora,
                size_hint_y=None,
                height=40,
                background_color=self.get_color_horario(disponible, False),
                disabled=not disponible
            )
            
            if disponible:
                btn.bind(on_press=self.seleccionar_hora)
            
            self.grid_horarios.add_widget(btn)
    
    def get_color_horario(self, disponible, ocupado):
        """Obtener color según disponibilidad"""
        if ocupado:
            return (0.8, 0.2, 0.2, 1)  # Rojo - Ocupado
        elif disponible:
            return (0.2, 0.8, 0.2, 1)  # Verde - Disponible
        else:
            return (0.8, 0.8, 0.8, 1)  # Gris - No disponible
    
    def mostrar_error_fecha(self, mensaje):
        """Mostrar error de fecha"""
        self.grid_horarios.clear_widgets()
        error_label = Label(
            text=mensaje,
            color=(1, 0, 0, 1),
            size_hint_y=None,
            height=40
        )
        self.grid_horarios.add_widget(error_label)
    
    def obtener_horarios_ocupados(self, fecha):
        """Obtener horarios ya ocupados desde Firebase"""
        try:
            citas_ref = db.collection("citas")
            query = citas_ref.where("fecha", "==", fecha).stream()
            
            horarios_ocupados = []
            for cita in query:
                cita_data = cita.to_dict()
                if cita_data.get("estado") != "anulada":  # Ignorar citas anuladas
                    horarios_ocupados.append(cita_data.get("hora", ""))
            
            return horarios_ocupados
        except Exception as e:
            print(f"Error obteniendo horarios ocupados: {e}")
            return []
    
    def seleccionar_hora(self, instance):
        """Seleccionar una hora específica"""
        hora=instance.text
        self.hora_seleccionada = hora
        self.btn_continuar.disabled = False
        
        # Resaltar la hora seleccionada
        for child in self.grid_horarios.children:
            if child.text == hora:
                child.background_color = (0.2, 0.6, 0.8, 1)  # Azul - Seleccionado
            elif not child.disabled:
                child.background_color = (0.2, 0.8, 0.2, 1)  # Verde - Disponible
    
    def mostrar_formulario_cita(self, instance):
        """Mostrar formulario completo de cita"""
        if not self.fecha_seleccionada or not self.hora_seleccionada:
            return
        
        self.layout_principal.clear_widgets()
        
        # Información de fecha/hora seleccionada
        info_header = Label(
            text=f"Cita para: {self.fecha_seleccionada} a las {self.hora_seleccionada}",
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=40
        )
        self.layout_principal.add_widget(info_header)
        
        # ScrollView para el formulario
        scroll_form = ScrollView()
        form_container = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        form_container.bind(minimum_height=form_container.setter('height'))
        
        # SECCIÓN DE PACIENTE
        paciente_label = Label(
            text="Datos del Paciente:",
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30
        )
        form_container.add_widget(paciente_label)
        
        # Búsqueda por RUT
        rut_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        rut_layout.add_widget(Label(text="RUT:", size_hint_x=0.3))
        
        self.rut_input = TextInput(
            hint_text="12345678-9",
            size_hint_x=0.4
        )
        self.rut_input.bind(text=self.buscar_paciente_auto)
        
        btn_buscar_paciente = Button(
            text="Buscar Paciente",
            size_hint_x=0.3,
            background_color=(0.3, 0.5, 0.8, 1)
        )
        btn_buscar_paciente.bind(on_press=self.buscar_paciente)
        
        rut_layout.add_widget(self.rut_input)
        rut_layout.add_widget(btn_buscar_paciente)
        form_container.add_widget(rut_layout)
        
        # Info del paciente
        self.paciente_info_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=100,
            spacing=5
        )
        form_container.add_widget(self.paciente_info_layout)
        
        # SECCIÓN DE SERVICIO
        servicio_label = Label(
            text="Servicio:",
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30
        )
        form_container.add_widget(servicio_label)
        
        # Selector de servicio
        servicio_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        servicio_layout.add_widget(Label(text="Servicio:", size_hint_x=0.3))
        
        self.servicio_spinner = Spinner(
            text="Seleccione servicio",
            values=list(SERVICIOS_PRECIOS.keys()),
            size_hint_x=0.7
        )
        self.servicio_spinner.bind(text=self.actualizar_monto)
        servicio_layout.add_widget(self.servicio_spinner)
        form_container.add_widget(servicio_layout)
        
        # Monto automático
        monto_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        monto_layout.add_widget(Label(text="Monto:", size_hint_x=0.3))
        
        self.monto_label = Label(
            text="$0",
            font_size='16sp',
            bold=True,
            color=(0.2, 0.6, 0.2, 1),
            size_hint_x=0.7
        )
        monto_layout.add_widget(self.monto_label)
        form_container.add_widget(monto_layout)
        
        # Notas
        notas_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=100, spacing=5)
        notas_layout.add_widget(Label(text="Notas adicionales:"))
        
        self.notas_input = TextInput(
            hint_text="Observaciones o detalles adicionales...",
            multiline=True,
            size_hint_y=None,
            height=80
        )
        notas_layout.add_widget(self.notas_input)
        form_container.add_widget(notas_layout)
        
        scroll_form.add_widget(form_container)
        self.layout_principal.add_widget(scroll_form)
        
        # Botones
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        btn_volver = Button(
            text="← Volver a Horarios",
            background_color=(0.8, 0.5, 0.2, 1)
        )
        btn_volver.bind(on_press=self.mostrar_selector_fecha_hora)
        
        btn_guardar = Button(
            text="Guardar Cita",
            background_color=(0.2, 0.6, 0.2, 1)
        )
        btn_guardar.bind(on_press=self.guardar_cita)
        
        btn_layout.add_widget(btn_volver)
        btn_layout.add_widget(btn_guardar)
        self.layout_principal.add_widget(btn_layout)
    
    def buscar_paciente_auto(self, instance, value):
        """Búsqueda automática de paciente al escribir RUT"""
        if len(value) >= 9:  # Buscar cuando tenga formato completo de RUT
            Clock.schedule_once(lambda dt: self._buscar_paciente_por_rut(value), 0.5)
    
    def _buscar_paciente_por_rut(self, rut):
        """Buscar paciente por RUT"""
        try:
            rut_limpio = rut.replace(".", "").replace("-", "").upper()
            pacientes_ref = db.collection('pacientes')
            query = pacientes_ref.where('rut', '==', rut_limpio).stream()
            
            for doc in query:
                self.paciente_data = doc.to_dict()
                self.mostrar_info_paciente(self.paciente_data)
                return
            
            # Si no encuentra, limpiar info
            self.paciente_info_layout.clear_widgets()
            self.paciente_data = None
            
        except Exception as e:
            print(f"Error en búsqueda automática: {e}")
    
    def buscar_paciente(self, instance):
        """Búsqueda manual de paciente"""
        rut = self.rut_input.text.strip()
        if not rut:
            self.mostrar_error("Ingrese un RUT para buscar")
            return
        
        try:
            rut_limpio = rut.replace(".", "").replace("-", "").upper()
            pacientes_ref = db.collection('pacientes')
            query = pacientes_ref.where('rut', '==', rut_limpio).stream()
            
            encontrado = False
            for doc in query:
                self.paciente_data = doc.to_dict()
                self.mostrar_info_paciente(self.paciente_data)
                encontrado = True
                break
            
            if not encontrado:
                self.mostrar_error("No se encontró paciente con ese RUT")
                self.paciente_info_layout.clear_widgets()
                self.paciente_data = None
                
        except Exception as e:
            self.mostrar_error(f"Error al buscar paciente: {str(e)}")
    
    def mostrar_info_paciente(self, paciente_data):
        """Mostrar información del paciente encontrado"""
        self.paciente_info_layout.clear_widgets()
        
        info_text = f"""Nombre: {paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')}
Teléfono: {paciente_data.get('telefono', 'No registrado')}
Email: {paciente_data.get('email', 'No registrado')}"""
        
        info_label = Label(
            text=info_text,
            size_hint_y=None,
            height=80,
            halign='left',
            valign='top'
        )
        self.paciente_info_layout.add_widget(info_label)
    
    def actualizar_monto(self, instance, servicio):
        """Actualizar monto automáticamente al seleccionar servicio"""
        if servicio in SERVICIOS_PRECIOS:
            monto = SERVICIOS_PRECIOS[servicio]
            self.monto_label.text = f"${monto:,}"
        else:
            self.monto_label.text = "$0"
    
    def guardar_cita(self, instance):
        """Guardar la cita en Firebase"""
        # Validar paciente seleccionado
        if not self.paciente_data:
            self.mostrar_error("Debe seleccionar un paciente primero")
            return
        
        # Validar servicio seleccionado
        servicio = self.servicio_spinner.text
        if servicio == "Seleccione servicio":
            self.mostrar_error("Debe seleccionar un servicio")
            return
        
        # Validar monto
        monto_text = self.monto_label.text.replace("$", "").replace(",", "").strip()
        try:
            monto_valor = int(monto_text)
            if monto_valor <= 0:
                self.mostrar_error("El monto debe ser mayor a 0")
                return
        except ValueError:
            self.mostrar_error("Monto inválido")
            return
        
        notas = self.notas_input.text.strip()
        
        try:
            # Obtener usuario actual
            user = auth.auth.current_user
            if not user:
                self.mostrar_error("No hay usuario autenticado")
                return
            
            # Preparar datos de la cita
            cita_data = {
                'paciente_rut': self.paciente_data.get('rut', ''),
                'paciente_nombre': f"{self.paciente_data.get('nombre', '')} {self.paciente_data.get('apellido', '')}",
                'paciente_telefono': self.paciente_data.get('telefono', ''),
                'servicio': servicio,
                'fecha': self.fecha_seleccionada,
                'hora': self.hora_seleccionada,
                'monto': monto_valor,
                'notas': notas,
                'estado': 'programada',
                'creado_por': user.uid,
                'creado_en': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Guardar en Firebase
            db.collection('citas').add(cita_data)
            
            self.mostrar_exito("✅ Cita creada exitosamente")
            self.dismiss()
            
        except Exception as e:
            self.mostrar_error(f"Error al guardar: {str(e)}")
    
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        error_popup = Popup(
            title="Error",
            content=Label(text=mensaje),
            size_hint=(0.7, 0.3)
        )
        error_popup.open()
        Clock.schedule_once(lambda dt: error_popup.dismiss(), 3)
    
    def mostrar_exito(self, mensaje):
        """Mostrar mensaje de éxito"""
        exito_popup = Popup(
            title="Éxito",
            content=Label(text=mensaje),
            size_hint=(0.7, 0.3)
        )
        exito_popup.open()
        Clock.schedule_once(lambda dt: exito_popup.dismiss(), 2)

        
class NuevoPacientePopup(Popup):
    def __init__(self, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.title = "Nuevo Paciente"
        self.size_hint = (0.9, 0.8)
        self.callback = callback
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Campos del formulario
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.7)
        
        campos = [
            ("Nombre:", "nombre_input"),
            ("Apellido:", "apellido_input"),
            ("RUT:", "rut_input"),
            ("Email:", "email_input"),
            ("Teléfono:", "telefono_input"),
            ("Fecha Nacimiento (DD-MM-YYYY):", "fecha_nac_input")
        ]
        
        self.campos_dict = {}
        
        for label_text, field_name in campos:
            form_layout.add_widget(Label(text=label_text))
            campo = TextInput(hint_text=label_text)
            setattr(self, field_name, campo)
            self.campos_dict[field_name] = campo
            form_layout.add_widget(campo)
        
        layout.add_widget(form_layout)
        
        # Botones
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=10)
        
        btn_cancelar = Button(text="Cancelar")
        btn_cancelar.bind(on_press=self.dismiss)
        
        btn_guardar = Button(text="Guardar Paciente", background_color=(0.2, 0.6, 0.2, 1))
        btn_guardar.bind(on_press=self.guardar_paciente)
        
        btn_layout.add_widget(btn_cancelar)
        btn_layout.add_widget(btn_guardar)
        
        layout.add_widget(btn_layout)
        
        self.content = layout
    
    def guardar_paciente(self, instance):
        datos = {}
        for field_name, campo in self.campos_dict.items():
            key = field_name.replace('_input', '')
            datos[key] = campo.text.strip()
        
        # Validaciones básicas
        if not datos.get('nombre') or not datos.get('apellido'):
            self.mostrar_error("Nombre y apellido son obligatorios")
            return
        
        try:
            # Guardar en Firebase
            db.collection('pacientes').add(datos)
            
            if self.callback:
                self.callback(datos)
                
            self.mostrar_exito("Paciente guardado exitosamente")
            self.dismiss()
            
        except Exception as e:
            self.mostrar_error(f"Error al guardar: {str(e)}")
    
    def mostrar_error(self, mensaje):
        error_popup = Popup(
            title="Error",
            content=Label(text=mensaje),
            size_hint=(0.7, 0.3)
        )
        error_popup.open()
        Clock.schedule_once(lambda dt: error_popup.dismiss(), 2)
    
    def mostrar_exito(self, mensaje):
        exito_popup = Popup(
            title="Éxito",
            content=Label(text=mensaje),
            size_hint=(0.7, 0.3)
        )
        exito_popup.open()
        Clock.schedule_once(lambda dt: exito_popup.dismiss(), 2)

class BuscarPacientePopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Buscar Paciente y ver Historial"
        self.size_hint = (0.95, 0.95)
        self.paciente_data=None
        self.paciente_id=None
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Campo de búsqueda
        search_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        search_layout.add_widget(Label(text="RUT del Paciente: ", sise_hint_x=0.3))
        self.rut_input=TextInput(
            hint_text="12345678-9",
            size_hint_x=0.5
        )
        
        btn_buscar = Button(
            text="Buscar",
            size_hint_x=0.2,
            backgroud_color=(0.3, 0.5, 0.8, 1)
        )
        btn_buscar.bind(on_press=self.buscar_paciente)
        
        search_layout.add_widget(self.search_input)
        search_layout.add_widget(btn_buscar)
        layout.add_widget(search_layout)
        
        #Información del paciente
        self.info_paciente_layout=BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=120,
            spacing=5
        )
        layout.add_widget(self.info_paciente_layout)
        
        #Pestaña para Historial y Citas
        self.tabs_layout=BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=50,
            spacing=5
        )
        
        self.btn_historial=ToggleButton(
            text="Historial de Atenciones",
            group='paciente_tabs',
            state='down'
        )
        self.btn_historial.bind(on_press=self.mostrar_historial)
        
        self.btn_citas=ToggleButton(
            text="Citas Programadas",
            group='paciente_tabs'
        )
        self.btn_citas.bind(on_press=self.mostrar_citas)
        
        self.tabs_layout.add_widget(self.btn_historial)
        self.tabs_latout.add_widget(self.btn_citas)
        layout.add_widget(self.tabs_layout)
        
        # Contenedor de contenido
        self.scroll_content = ScrollView()
        self.content_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10,
            padding=10
        )
        self.content_layout.bind(minimun_height=self.content_layout.setter('height'))
        self.scroll_content.add_widget(self.content_layout)
        layout.add_widget(self.scroll_content)
        
        # Botones de accion
        btn_action_layout=BoxLayout(
            size_hint_y=None,
            height=50,
            spacing=10
        )
        
        btn_nueva_cita=Button(
            text="Nueva Cita",
            background_color=(0.2, 0.6, 0.2, 1)
        )
        btn_nueva_cita.bind(on_press=self.crear_nueva_cita)
        
        btn_cerrar=Button(
            text="Cerrar",
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_cerrar.bind(on_press=self.dismiss)
        
        btn_action_layout.add_widget(btn_nueva_cita)
        btn_action_layout.ad_widget(btn_cerrar)
        layout.add_widget(btn_action_layout)
        
        self.content=layout
        
    
    def buscar_paciente(self, instance):
        rut=self.rut_input.text.strip()
        if not rut:
            self.mostrar_error("Ingrese un RUT para buscar")
            return
        try:
            rut_limpio=rut.replace(".", "").upper()
            
            pacientes_ref=db.collection('pacientes')
            query=pacientes_ref.where('rut', '==', rut_limpio).stream()
            
            encontrado=False
            for doc in query:
                self.paciente_data=doc.to_dict()
                self.paciente_id=doc.id
                self.mostrar_info_paciente(self.paciente_data)
                self.mostrar_historial()
                
                encontrado=True
                break
            
            if not encontrado:
                self.mostrar_error("No se encontró paciente con ese RUT")
                self.limpiar_contenido()
        
        except Exception as e:
            self.mostrar_error(f"Error al buscar paciente: {str(e)}")
    
    def mostrar_info_paciente(self, paciente_data):
        """Mostrar información del paciente"""
        self.info_paciente_layout.clear_widgets()
        
        info_text = f"""📋 [b]PACIENTE ENCONTRADO[/b]
👤 Nombre: {paciente_data.get('nombre', '')} {paciente_data.get('apellido', '')}
📞 Teléfono: {paciente_data.get('telefono', 'No registrado')}
📧 Email: {paciente_data.get('email', 'No registrado')}
🆔 RUT: {paciente_data.get('rut', '')}"""
        
        info_label = Label(
            text=info_text,
            markup=True,
            size_hint_y=None,
            height=100,
            halign='left',
            valign='top'
        )
        self.info_paciente_layout.add_widget(info_label)
    
    def mostrar_historial(self, instance=None):
        """Mostrar historial de atenciones del paciente"""
        if not self.paciente_id:
            return
            
        self.content_layout.clear_widgets()
        
        # Título
        titulo = Label(
            text="📊 Historial de Atenciones Médicas",
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=40
        )
        self.content_layout.add_widget(titulo)
        
        try:
            # Obtener historial de atenciones
            historial_ref = db.collection("pacientes").document(self.paciente_id).collection("historial")
            atenciones = historial_ref.order_by("fecha", direction=firestore.Query.DESCENDING).stream()
            
            total_atenciones = 0
            total_ingresos = 0
            
            for atencion in atenciones:
                atencion_data = atencion.to_dict()
                total_atenciones += 1
                total_ingresos += atencion_data.get("total", 0)
                
                # Crear tarjeta de atención
                atencion_card = BoxLayout(
                    orientation='vertical',
                    size_hint_y=None,
                    height=180,
                    spacing=5,
                    padding=10,
                    background_color=(0.95, 0.95, 0.95, 1)
                )
                
                # Header de la atención
                header_layout = BoxLayout(size_hint_y=None, height=30)
                header_layout.add_widget(Label(
                    text=f"📅 {atencion_data.get('fecha', 'Sin fecha')}",
                    size_hint_x=0.7,
                    bold=True
                ))
                header_layout.add_widget(Label(
                    text=f"💰 ${atencion_data.get('total', 0):,}",
                    size_hint_x=0.3,
                    color=(0.2, 0.6, 0.2, 1),
                    bold=True
                ))
                atencion_card.add_widget(header_layout)
                
                # Diagnóstico
                diag_text = atencion_data.get('diagnostico', 'Sin diagnóstico')
                if len(diag_text) > 60:
                    diag_text = diag_text[:60] + "..."
                atencion_card.add_widget(Label(
                    text=f"🩺 Diagnóstico: {diag_text}",
                    size_hint_y=None,
                    height=30,
                    halign='left'
                ))
                
                # Tratamiento
                trat_text = atencion_data.get('tratamiento', 'Sin tratamiento')
                if len(trat_text) > 60:
                    trat_text = trat_text[:60] + "..."
                atencion_card.add_widget(Label(
                    text=f"💊 Tratamiento: {trat_text}",
                    size_hint_y=None,
                    height=30,
                    halign='left'
                ))
                
                # Procedimientos
                procedimientos = atencion_data.get('procedimientos', [])
                if procedimientos:
                    proc_text = ", ".join([p['descripcion'] for p in procedimientos[:2]])
                    if len(procedimientos) > 2:
                        proc_text += f" y {len(procedimientos) - 2} más..."
                    atencion_card.add_widget(Label(
                        text=f"⚡ Procedimientos: {proc_text}",
                        size_hint_y=None,
                        height=30,
                        halign='left'
                    ))
                
                self.content_layout.add_widget(atencion_card)
            
            # Estadísticas
            if total_atenciones > 0:
                stats_layout = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=50,
                    spacing=10
                )
                
                stats_layout.add_widget(Label(
                    text=f"📈 Total Atenciones: {total_atenciones}",
                    bold=True
                ))
                
                stats_layout.add_widget(Label(
                    text=f"💰 Total Ingresos: ${total_ingresos:,}",
                    bold=True,
                    color=(0.2, 0.6, 0.2, 1)
                ))
                
                self.content_layout.add_widget(stats_layout)
            else:
                self.content_layout.add_widget(Label(
                    text="No hay historial de atenciones para este paciente",
                    italic=True,
                    size_hint_y=None,
                    height=50
                ))
                
        except Exception as e:
            self.content_layout.add_widget(Label(
                text=f"Error al cargar historial: {str(e)}",
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=50
            ))
    
    def mostrar_citas(self, instance):
        """Mostrar citas programadas del paciente"""
        if not self.paciente_data:
            return
            
        self.content_layout.clear_widgets()
        
        try:
            rut_paciente = self.paciente_data.get('rut', '')
            
            # Buscar citas del paciente
            citas_ref = db.collection("citas")
            query = citas_ref.where("paciente_rut", "==", rut_paciente).where("estado", "==", "programada").stream()
            
            titulo = Label(
                text="📅 Citas Programadas",
                font_size='16sp',
                bold=True,
                size_hint_y=None,
                height=40
            )
            self.content_layout.add_widget(titulo)
            
            citas_encontradas = 0
            
            for cita in query:
                cita_data = cita.to_dict()
                citas_encontradas += 1
                
                cita_card = BoxLayout(
                    orientation='vertical',
                    size_hint_y=None,
                    height=100,
                    spacing=5,
                    padding=10,
                    background_color=(0.9, 0.95, 1, 1)
                )
                
                # Información de la cita
                cita_card.add_widget(Label(
                    text=f"📅 {cita_data.get('fecha', '')} ⏰ {cita_data.get('hora', '')}",
                    bold=True,
                    size_hint_y=None,
                    height=30
                ))
                
                cita_card.add_widget(Label(
                    text=f"🏥 {cita_data.get('servicio', '')} - 💰 ${cita_data.get('monto', 0):,}",
                    size_hint_y=None,
                    height=25
                ))
                
                if cita_data.get('notas'):
                    nota_text = cita_data['notas']
                    if len(nota_text) > 40:
                        nota_text = nota_text[:40] + "..."
                    cita_card.add_widget(Label(
                        text=f"📝 {nota_text}",
                        size_hint_y=None,
                        height=25,
                        font_size='12sp'
                    ))
                
                self.content_layout.add_widget(cita_card)
            
            if citas_encontradas == 0:
                self.content_layout.add_widget(Label(
                    text="No hay citas programadas para este paciente",
                    italic=True,
                    size_hint_y=None,
                    height=50
                ))
                
        except Exception as e:
            self.content_layout.add_widget(Label(
                text=f"Error al cargar citas: {str(e)}",
                color=(1, 0, 0, 1),
                size_hint_y=None,
                height=50
            ))
    
    def crear_nueva_cita(self, instance):
        """Abrir popup para crear nueva cita para este paciente"""
        if not self.paciente_data:
            self.mostrar_error("Primero debe buscar un paciente")
            return
            
        self.dismiss()
        from components.popups import CitaPopup
        cita_popup = CitaPopup()
        cita_popup.open()
    
    def limpiar_contenido(self):
        """Limpiar todo el contenido"""
        self.info_paciente_layout.clear_widgets()
        self.content_layout.clear_widgets()
        self.paciente_data = None
        self.paciente_id = None
    
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        error_popup = Popup(
            title="Error",
            content=Label(text=mensaje),
            size_hint=(0.7, 0.3)
        )
        error_popup.open()
        Clock.schedule_once(lambda dt: error_popup.dismiss(), 3)

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
        