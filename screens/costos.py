from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.widget import Widget
from datetime import datetime, timedelta
from models.firebase import db
import calendar
import math

class CentroCostosScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gastos_totales = 0
        self.ingresos_totales = 0
        self.build_ui()
        
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Título
        title = Label(
            text="📊 Centro de Ingresos y Ganancias",
            font_size='26sp',
            bold=True,
            size_hint_y=None,
            height=60,
            color=(0.1, 0.4, 0.6, 1)
        )
        layout.add_widget(title)
        
        # Selector de período
        period_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        period_layout.add_widget(Label(text="Período:", size_hint_x=0.3))
        
        self.period_spinner = Spinner(
            text='Hoy',
            values=('Hoy', 'Esta semana', 'Este mes', 'Este año'),
            size_hint_x=0.7
        )
        self.period_spinner.bind(text=self.on_period_change)
        period_layout.add_widget(self.period_spinner)
        layout.add_widget(period_layout)
        
        # Estadísticas resumen
        self.stats_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=120)
        layout.add_widget(self.stats_layout)
        
        # Gráfico simple
        self.chart_widget = Widget(size_hint_y=None, height=200)
        layout.add_widget(self.chart_widget)
        
        # Detalle de ingresos
        detail_label = Label(
            text="📋 Detalle de Ingresos:",
            font_size='18sp',
            bold=True,
            size_hint_y=None,
            height=40
        )
        layout.add_widget(detail_label)
        
        # Headers del grid de ingresos
        headers_layout = GridLayout(cols=4, spacing=5, size_hint_y=None, height=40)
        headers = ["Fecha", "Paciente", "Servicio", "Monto"]
        for header in headers:
            header_label = Label(text=header, bold=True, color=(0.2, 0.2, 0.6, 1))
            headers_layout.add_widget(header_label)
        layout.add_widget(headers_layout)
        
        scroll = ScrollView(size_hint_y=0.3)
        self.income_grid = GridLayout(cols=4, spacing=5, size_hint_y=None)
        self.income_grid.bind(minimum_height=self.income_grid.setter('height'))
        scroll.add_widget(self.income_grid)
        layout.add_widget(scroll)
        
        # Sección de gastos
        costs_label = Label(
            text="💸 Gastos Registrados:",
            font_size='18sp',
            bold=True,
            size_hint_y=None,
            height=40
        )
        layout.add_widget(costs_label)
        
        scroll_gastos = ScrollView(size_hint_y=0.2)
        self.gastos_grid = GridLayout(cols=3, spacing=5, size_hint_y=None)
        self.gastos_grid.bind(minimum_height=self.gastos_grid.setter('height'))
        scroll_gastos.add_widget(self.gastos_grid)
        layout.add_widget(scroll_gastos)
        
        # Formulario para agregar gastos
        costs_form = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        self.cost_desc_input = TextInput(
            hint_text="Descripción del gasto",
            size_hint_x=0.4
        )
        
        self.cost_amount_input = TextInput(
            hint_text="Monto $",
            input_filter='float',
            size_hint_x=0.3
        )
        
        btn_add_cost = Button(
            text="+ Agregar Gasto",
            size_hint_x=0.3,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        btn_add_cost.bind(on_press=self.agregar_gasto)
        
        costs_form.add_widget(self.cost_desc_input)
        costs_form.add_widget(self.cost_amount_input)
        costs_form.add_widget(btn_add_cost)
        layout.add_widget(costs_form)
        
        # Botones de acción
        action_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        
        btn_actualizar = Button(
            text="🔄 Actualizar",
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn_actualizar.bind(on_press=self.actualizar_datos)
        
        btn_volver = Button(
            text="← Volver al Menú",
            background_color=(0.8, 0.5, 0.2, 1)
        )
        btn_volver.bind(on_press=self.volver)
        
        action_layout.add_widget(btn_actualizar)
        action_layout.add_widget(btn_volver)
        layout.add_widget(action_layout)
        
        self.add_widget(layout)
        
        # Inicializar datos
        self.fecha_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.fecha_fin = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        self.cargar_datos()

    def on_enter(self):
        """Se ejecuta cuando se entra a la pantalla"""
        self.cargar_datos()

    def volver(self, instance):
        """Volver a la pantalla principal"""
        self.manager.current = 'main'

    def on_period_change(self, instance, value):
        """Cambiar el período de reporte"""
        hoy = datetime.now()
        if value == 'Hoy':
            self.fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif value == 'Esta semana':
            self.fecha_inicio = hoy - timedelta(days=hoy.weekday())
            self.fecha_fin = self.fecha_inicio + timedelta(days=6)
        elif value == 'Este mes':
            self.fecha_inicio = hoy.replace(day=1)
            last_day = calendar.monthrange(hoy.year, hoy.month)[1]
            self.fecha_fin = hoy.replace(day=last_day)
        elif value == 'Este año':
            self.fecha_inicio = hoy.replace(month=1, day=1)
            self.fecha_fin = hoy.replace(month=12, day=31)
        
        self.fecha_fin = self.fecha_fin.replace(hour=23, minute=59, second=59, microsecond=999999)
        self.cargar_datos()

    def actualizar_datos(self, instance):
        """Actualizar todos los datos"""
        self.cargar_datos()

    def cargar_datos(self):
        """Cargar ingresos y gastos"""
        self.cargar_ingresos()
        self.cargar_gastos()

    def cargar_ingresos(self):
        """Cargar ingresos desde citas"""
        try:
            # Limpiar grids
            self.income_grid.clear_widgets()
            self.chart_widget.canvas.clear()
            
            # Obtener todas las citas en el período
            citas_ref = db.collection('citas').stream()
            
            self.ingresos_totales = 0
            citas_data = []
            
            for doc in citas_ref:
                cita = doc.to_dict()
                try:
                    fecha_cita = datetime.strptime(cita['fecha'], '%Y-%m-%d')
                    
                    if self.fecha_inicio.date() <= fecha_cita.date() <= self.fecha_fin.date():
                        # Asumir que todas las citas tienen un monto (valor por defecto 50 si no existe)
                        monto = float(cita.get('monto', 50))
                        self.ingresos_totales += monto
                        citas_data.append({
                            'fecha': cita['fecha'],
                            'paciente': cita.get('paciente_nombre', cita.get('nombre_paciente', 'Sin nombre')),
                            'servicio': cita.get('servicio', 'Consulta'),
                            'monto': monto
                        })
                except (KeyError, ValueError):
                    continue
            
            # Ordenar por fecha
            citas_data.sort(key=lambda x: x['fecha'], reverse=True)
            
            # Mostrar detalle
            for cita in citas_data:
                self.agregar_fila_ingreso(cita)
            
            # Crear gráfico
            self.crear_grafico(citas_data)
            
        except Exception as e:
            print(f"Error cargando ingresos: {e}")
            self.mostrar_popup("Error", f"No se pudieron cargar los ingresos: {str(e)}")

    def cargar_gastos(self):
        """Cargar gastos del período"""
        try:
            self.gastos_grid.clear_widgets()
            self.gastos_totales = 0
            
            # Obtener gastos del período
            gastos_ref = db.collection('gastos').stream()
            gastos_data = []
            
            for doc in gastos_ref:
                gasto = doc.to_dict()
                try:
                    fecha_gasto = datetime.strptime(gasto['fecha'], '%Y-%m-%d %H:%M:%S')
                    
                    if self.fecha_inicio <= fecha_gasto <= self.fecha_fin:
                        monto = float(gasto.get('monto', 0))
                        self.gastos_totales += monto
                        gastos_data.append({
                            'descripcion': gasto.get('descripcion', 'Sin descripción'),
                            'monto': monto,
                            'fecha': gasto['fecha'][:10]  # Solo la fecha
                        })
                except (KeyError, ValueError):
                    continue
            
            # Mostrar gastos
            for gasto in gastos_data:
                self.agregar_fila_gasto(gasto)
            
            # Actualizar estadísticas
            self.mostrar_estadisticas()
            
        except Exception as e:
            print(f"Error cargando gastos: {e}")

    def mostrar_estadisticas(self):
        """Mostrar estadísticas de ingresos y ganancias"""
        self.stats_layout.clear_widgets()
        
        ganancias = self.ingresos_totales - self.gastos_totales
        
        stats = [
            ("💰 Ingresos", f"${self.ingresos_totales:,.2f}", (0.2, 0.6, 0.2, 1)),
            ("💸 Gastos", f"${self.gastos_totales:,.2f}", (0.8, 0.2, 0.2, 1)),
            ("📊 Citas", str(len(self.income_grid.children) // 4), (0.3, 0.5, 0.8, 1)),
            ("🎯 Ganancias", f"${ganancias:,.2f}", (0.4, 0.7, 0.3, 1) if ganancias >= 0 else (0.8, 0.2, 0.2, 1))
        ]
        
        for texto, valor, color in stats:
            stat_box = BoxLayout(orientation='vertical', spacing=2)
            
            label_text = Label(
                text=texto,
                font_size='14sp',
                bold=True,
                size_hint_y=None,
                height=20
            )
            
            label_valor = Label(
                text=valor,
                font_size='16sp',
                bold=True,
                color=color,
                size_hint_y=None,
                height=30
            )
            
            stat_box.add_widget(label_text)
            stat_box.add_widget(label_valor)
            self.stats_layout.add_widget(stat_box)

    def agregar_fila_ingreso(self, cita):
        """Agregar fila al grid de ingresos"""
        fecha_label = Label(text=cita['fecha'], size_hint_x=None, width=100)
        paciente_label = Label(text=cita['paciente'][:15], size_hint_x=None, width=150)
        servicio_label = Label(text=cita['servicio'][:15], size_hint_x=None, width=120)
        monto_label = Label(text=f"${cita['monto']:,.2f}", size_hint_x=None, width=80, color=(0.2, 0.6, 0.2, 1))
        
        self.income_grid.add_widget(fecha_label)
        self.income_grid.add_widget(paciente_label)
        self.income_grid.add_widget(servicio_label)
        self.income_grid.add_widget(monto_label)

    def agregar_fila_gasto(self, gasto):
        """Agregar fila al grid de gastos"""
        fecha_label = Label(text=gasto['fecha'], size_hint_x=None, width=100)
        desc_label = Label(text=gasto['descripcion'][:20], size_hint_x=None, width=200)
        monto_label = Label(text=f"${gasto['monto']:,.2f}", size_hint_x=None, width=80, color=(0.8, 0.2, 0.2, 1))
        
        self.gastos_grid.add_widget(fecha_label)
        self.gastos_grid.add_widget(desc_label)
        self.gastos_grid.add_widget(monto_label)

    def crear_grafico(self, citas_data):
        """Crear gráfico básico de barras"""
        if not citas_data:
            # Mostrar mensaje si no hay datos
            with self.chart_widget.canvas:
                Color(0.7, 0.7, 0.7, 0.5)
                Rectangle(pos=self.chart_widget.pos, size=self.chart_widget.size)
            return
            
        # Agrupar por día
        ingresos_por_dia = {}
        for cita in citas_data:
            dia = cita['fecha']
            if dia not in ingresos_por_dia:
                ingresos_por_dia[dia] = 0
            ingresos_por_dia[dia] += cita['monto']
        
        dias = list(ingresos_por_dia.keys())
        valores = list(ingresos_por_dia.values())
        
        max_valor = max(valores) if valores else 1
        width, height = 400, 200  # Tamaño fijo para el gráfico
        
        with self.chart_widget.canvas:
            # Fondo
            Color(1, 1, 1, 1)
            Rectangle(pos=self.chart_widget.pos, size=self.chart_widget.size)
            
            # Eje X
            Color(0, 0, 0, 1)
            Line(points=[50, 40, width - 20, 40], width=1.5)
            
            # Barras
            bar_width = (width - 100) / len(dias) if len(dias) > 0 else 50
            bar_width = max(20, min(bar_width, 80))
            
            for i, (dia, valor) in enumerate(ingresos_por_dia.items()):
                x_pos = 60 + i * (bar_width + 10)
                bar_height = (valor / max_valor) * (height - 60)
                bar_height = max(5, bar_height)
                
                # Barra
                Color(0.2, 0.6, 0.8, 0.8)
                Rectangle(pos=(x_pos, 40), size=(bar_width, bar_height))
                
                # Etiqueta valor
                if bar_height > 15:
                    Color(0, 0, 0, 1)
                    Rectangle(pos=(x_pos, 40 + bar_height + 2), size=(bar_width, 1))

    def agregar_gasto(self, instance):
        """Agregar nuevo gasto"""
        descripcion = self.cost_desc_input.text.strip()
        monto_str = self.cost_amount_input.text.strip()
        
        if not descripcion or not monto_str:
            self.mostrar_popup("Error", "Por favor completa todos los campos")
            return
        
        try:
            monto = float(monto_str)
            if monto <= 0:
                self.mostrar_popup("Error", "El monto debe ser mayor a 0")
                return
                
            gasto_data = {
                'descripcion': descripcion,
                'monto': monto,
                'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'tipo': 'gasto'
            }
            
            # Guardar en Firebase
            db.collection('gastos').add(gasto_data)
            
            # Limpiar inputs
            self.cost_desc_input.text = ''
            self.cost_amount_input.text = ''
            
            self.mostrar_popup("Éxito", "Gasto agregado correctamente")
            self.cargar_gastos()  # Recargar solo gastos
            
        except ValueError:
            self.mostrar_popup("Error", "Ingresa un monto válido")
        except Exception as e:
            self.mostrar_popup("Error", f"Error al guardar: {str(e)}")

    def mostrar_popup(self, titulo, mensaje):
        """Mostrar popup de mensaje"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text=mensaje))
        
        btn_cerrar = Button(text="Cerrar", size_hint_y=None, height=40)
        popup = Popup(title=titulo, content=content, size_hint=(0.7, 0.3))
        
        btn_cerrar.bind(on_press=popup.dismiss)
        content.add_widget(btn_cerrar)
        popup.open()