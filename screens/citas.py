from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from datetime import datetime, timedelta
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from models.firebase import db
import re

class CitasScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Layout principal con pestañas
        self.tabs = TabbedPanel()
        self.tabs.do_default_tab = False
        
        # ----------------------------
        # Pestaña de Citas
        # ----------------------------
        self.tab_citas = TabbedPanelItem(text='Citas')
        self.citas_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Filtro de fechas
        filter_layout = BoxLayout(size_hint_y=None, height=50)
        self.fecha_filter = TextInput(
            hint_text="Filtrar por fecha (DD-MM-YYYY)",
            text=datetime.now().strftime("%d-%m-%Y")
        )
        filter_btn = Button(text="Filtrar", size_hint_x=None, width=100)
        filter_btn.bind(on_press=self.filtrar_citas)
        filter_layout.add_widget(self.fecha_filter)
        filter_layout.add_widget(filter_btn)
        self.citas_content.add_widget(filter_layout)
        
        # Lista de citas
        self.scroll_citas = ScrollView()
        self.citas_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.citas_grid.bind(minimum_height=self.citas_grid.setter('height'))
        self.scroll_citas.add_widget(self.citas_grid)
        self.citas_content.add_widget(self.scroll_citas)
        
        # Botón Volver
        btn_volver = Button(
            text="Volver", 
            size_hint_y=None, 
            height=50,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_volver.bind(on_press=self.volver)
        self.citas_content.add_widget(btn_volver)
        
        self.tab_citas.add_widget(self.citas_content)
        self.tabs.add_widget(self.tab_citas)
        
        # ----------------------------
        # Pestaña de Recordatorios
        # ----------------------------
        self.tab_recordatorios = TabbedPanelItem(text='Recordatorios')
        self.recordatorios_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Lista de recordatorios
        self.scroll_recordatorios = ScrollView()
        self.recordatorios_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.recordatorios_grid.bind(minimum_height=self.recordatorios_grid.setter('height'))
        self.scroll_recordatorios.add_widget(self.recordatorios_grid)
        self.recordatorios_content.add_widget(self.scroll_recordatorios)
        
        self.tab_recordatorios.add_widget(self.recordatorios_content)
        self.tabs.add_widget(self.tab_recordatorios)
        
        # Agregar pestañas al screen
        self.add_widget(self.tabs)
        
        # Cargar datos
        Clock.schedule_once(lambda dt: self.cargar_citas())
        Clock.schedule_once(lambda dt: self.cargar_recordatorios())

    def cargar_citas(self, fecha=None):
        self.citas_grid.clear_widgets()
        
        try:
            citas_ref = db.collection("citas")
            
            if fecha:
                query = citas_ref.where("fecha", "==", fecha).order_by("hora").stream()
            else:
                query = citas_ref.order_by("fecha").order_by("hora").stream()
            
            for doc in query:
                cita_data = doc.to_dict()
                btn = Button(
                    text=f"{cita_data.get('fecha', '')} {cita_data.get('hora', '')} - {cita_data.get('paciente_nombre', '')}\nMotivo: {cita_data.get('motivo', '')}",
                    size_hint_y=None,
                    height=100,
                    background_color=(0.8, 0.8, 0.2, 1) if cita_data.get('estado', 'pendiente') == 'anulada' else (0.2, 0.8, 0.2, 1),
                    halign='left'
                )
                btn.cita_data = cita_data
                btn.cita_id = doc.id
                btn.bind(on_press=self.mostrar_detalle_cita)
                self.citas_grid.add_widget(btn)
                
        except Exception as e:
            print(f"Error cargando citas: {e}")
            self.citas_grid.add_widget(Label(text=f"Error al cargar citas: {str(e)}"))

    def cargar_recordatorios(self):
        self.recordatorios_grid.clear_widgets()  # Cambiado de recordatorios_layout a recordatorios_grid
        
        try:
            # Obtener citas próximas (hoy + 2 días)
            hoy = datetime.now()
            fechas = [hoy + timedelta(days=i) for i in range(3)]  # Hoy, mañana y pasado
            
            citas_ref = db.collection("citas")
            query = citas_ref.where("fecha", "in", [fecha.strftime("%d-%m-%Y") for fecha in fechas]).where("estado", "==", "pendiente")
            
            for doc in query.stream():
                cita = doc.to_dict()
                btn = Button(
                    text=f"{cita['fecha']} {cita['hora']}\n{cita['paciente_nombre']}\nMotivo: {cita['motivo']}",
                    size_hint_y=None,
                    height=120,
                    background_color=(0.9, 0.7, 0.1, 1),
                    halign='left',
                    valign='top'
                )
                self.recordatorios_grid.add_widget(btn)
            
            # Separador
            self.recordatorios_grid.add_widget(Label(
                text="[b]Cumpleaños esta semana:[/b]", 
                markup=True,
                size_hint_y=None,
                height=40
            ))
            
            # Obtener cumpleaños de la semana
            self.cargar_cumpleanos()
            
        except Exception as e:
            print(f"Error cargando recordatorios: {e}")
            self.recordatorios_grid.add_widget(Label(
                text="Error cargando recordatorios",
                color=(1, 0, 0, 1)
            ))

    # ... (mantener el resto de los métodos igual)
    
    def cargar_cumpleanos(self):
        try:
            # Obtener pacientes
            pacientes_ref = db.collection("pacientes")
            hoy = datetime.now()
            semana = [hoy + timedelta(days=i) for i in range(7)]  # Próximos 7 días
            
            for paciente in pacientes_ref.stream():
                paciente_data = paciente.to_dict()
                try:
                    fecha_nac = datetime.strptime(paciente_data['fecha_nacimiento'], "%d-%m-%Y")
                    
                    # Verificar si cumple años esta semana
                    for dia in semana:
                        if fecha_nac.day == dia.day and fecha_nac.month == dia.month:
                            edad = dia.year - fecha_nac.year
                            lbl = Label(
                                text=f"{paciente_data['nombre']} {paciente_data['apellido']}\n" +
                                     f"Cumple: {fecha_nac.strftime('%d/%m')} - {edad} años",
                                size_hint_y=None,
                                height=60,
                                halign='left'
                            )
                            self.recordatorios_grid.add_widget(lbl)
                            break
                            
                except Exception as e:
                    print(f"Error procesando paciente {paciente.id}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error cargando cumpleaños: {e}")
            self.recordatorios_grid.add_widget(Label(
                text="Error cargando cumpleaños",
                color=(1, 0, 0, 1)
            ))
    
    def volver(self, instance):
        self.manager.current = 'main'
    
    def filtrar_citas(self, instance):
        fecha = self.fecha_filter.text.strip()
        try:
            datetime.strptime(fecha, "%d-%m-%Y")
            self.cargar_citas(fecha)
        except ValueError:
            self.citas_layout.clear_widgets()
            self.citas_layout.add_widget(Label(text="Formato de fecha inválido (DD-MM-YYYY)"))
    
    def mostrar_detalle_cita(self, instance):
        cita_data = instance.cita_data
        cita_id = instance.cita_id
        
        content = BoxLayout(orientation='vertical', spacing=10)
        
        details = f"""
        Paciente: {cita_data.get('paciente_nombre', '')}
        RUT: {cita_data.get('paciente_rut', '')}
        Fecha: {cita_data.get('fecha', '')}
        Hora: {cita_data.get('hora', '')}
        Motivo: {cita_data.get('motivo', '')}
        Estado: {cita_data.get('estado', 'pendiente')}
        """
        
        content.add_widget(Label(text=details))
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
    
        btn_anular = Button(
            text="Anular Cita",
            size_hint_x=0.5,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_anular.bind(on_press=lambda x: self.anular_cita(cita_id))
    
        btn_modificar = Button(
            text="Modificar Cita",
            size_hint_x=0.5,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn_modificar.bind(on_press=lambda x: self.modificar_cita(cita_id, cita_data))
    
        btn_close = Button(
            text="Cerrar",
            size_hint_y=None,
            height=50
        )
        
        btn_layout.add_widget(btn_anular)
        btn_layout.add_widget(btn_modificar)
        content.add_widget(btn_layout)
        content.add_widget(btn_close)
        
        self.popup_detalle = Popup(
            title="Detalles de la Cita",
            content=content,
            size_hint=(0.8, 0.6))
        btn_close.bind(on_press=self.popup_detalle.dismiss)
        self.popup_detalle.open()
        
    def anular_cita(self, cita_id):
        try:
            db.collection("citas").document(cita_id).update({
                "estado": "anulada",
                "fecha_anulacion": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            })
            self.popup_detalle.dismiss()
            self.cargar_citas()
            Popup(title="Éxito", content=Label(text="Cita anulada correctamente"), size_hint=(0.7, 0.3)).open()
        except Exception as e:
            Popup(title="Error", content=Label(text=f"Error al anular cita: {str(e)}"), size_hint=(0.7, 0.3)).open()
    
    def modificar_cita(self, cita_id, cita_data):
        self.popup_detalle.dismiss()
    
        popup = Popup(title="Modificar Cita", size_hint=(0.9, 0.8))
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
    
        layout.add_widget(Label(text=f"Modificando cita para: {cita_data['paciente_nombre']}"))
    
        fecha_layout = BoxLayout(size_hint_y=None, height=50)
        fecha_layout.add_widget(Label(text="Fecha actual:"))
        fecha_actual = Label(text=cita_data['fecha'])
        fecha_layout.add_widget(fecha_actual)
        layout.add_widget(fecha_layout)
    
        self.nueva_fecha = TextInput(
            hint_text="Nueva fecha (DD-MM-YYYY)",
            text=cita_data['fecha']
        )
        layout.add_widget(self.nueva_fecha)
    
        hora_layout = BoxLayout(size_hint_y=None, height=50)
        hora_layout.add_widget(Label(text="Hora actual:"))
        hora_actual = Label(text=cita_data['hora'])
        hora_layout.add_widget(hora_actual)
        layout.add_widget(hora_layout)
    
        self.nueva_hora = TextInput(
            hint_text="Nueva hora (HH:MM)",
            text=cita_data['hora']
        )
        layout.add_widget(self.nueva_hora)
    
        layout.add_widget(Label(text="Motivo actual:"))
        layout.add_widget(Label(text=cita_data['motivo']))
    
        self.nuevo_motivo = TextInput(
            hint_text="Nuevo motivo",
            text=cita_data['motivo'],
            multiline=True
        )
        layout.add_widget(self.nuevo_motivo)
    
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
    
        btn_guardar = Button(
            text="Guardar Cambios",
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_guardar.bind(on_press=lambda x: self.guardar_cambios_cita(cita_id))
    
        btn_cancelar = Button(
            text="Cancelar",
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_cancelar.bind(on_press=popup.dismiss)
    
        btn_layout.add_widget(btn_guardar)
        btn_layout.add_widget(btn_cancelar)
        layout.add_widget(btn_layout)
    
        popup.content = layout
        self.popup_modificar = popup
        popup.open()
        
    def guardar_cambios_cita(self, cita_id):
        nueva_fecha = self.nueva_fecha.text.strip()
        nueva_hora = self.nueva_hora.text.strip()
        nuevo_motivo = self.nuevo_motivo.text.strip()
        
        errors = []
        
        try:
            datetime.strptime(nueva_fecha, "%d-%m-%Y")
        except ValueError:
            errors.append("Formato de fecha inválido (DD-MM-YYYY)")
            
        if not re.match(r'^\d{2}:\d{2}$', nueva_hora):
            errors.append("Hora debe tener formato HH:MM")
            
        if not nuevo_motivo:
            errors.append("Debe ingresar un motivo para la cita")
            
        if errors:
            Popup(title="Error", content=Label(text="\n".join(errors)), size_hint=(0.7, 0.3)).open()
            return
    
        try:
            db.collection("citas").document(cita_id).update({
                "fecha": nueva_fecha,
                "hora": nueva_hora,
                "motivo": nuevo_motivo,
                "modificado_en": datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            })
            self.popup_modificar.dismiss()
            self.cargar_citas()
            Popup(title="Éxito", content=Label(text="Cita modificada correctamente"), size_hint=(0.7, 0.3)).open()
        except Exception as e:
            Popup(title="Error", content=Label(text=f"Error al modificar cita: {str(e)}"), size_hint=(0.7, 0.3)).open()
            
    def volver(self, instance):
        self.manager.current = 'main'