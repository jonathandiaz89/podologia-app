from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable
from models.firebase import db
from kivy.clock import Clock
from datetime import datetime
from firebase_admin import firestore
from kivy.garden.graph import Graph, MeshLinePlot

class CentroCostosScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        filter_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        self.fecha_input = TextInput(
            hint_text="Fecha (DD-MM-YYYY)",
            text=datetime.now().strftime("%d-%m-%Y"),
            size_hint_x=0.6
        )
        
        btn_filtrar = Button(
            text="Día",
            size_hint_x=0.2,
            background_color=(0.3, 0.5, 0.8, 1)
        )
        btn_filtrar.bind(on_press=self.filtrar_dia)
        
        btn_mes = Button(
            text="Mes",
            size_hint_x=0.2,
            background_color=(0.4, 0.6, 0.8, 1)
        )
        btn_mes.bind(on_press=self.filtrar_mes)
        
        filter_layout.add_widget(self.fecha_input)
        filter_layout.add_widget(btn_filtrar)
        filter_layout.add_widget(btn_mes)
        self.layout.add_widget(filter_layout)
        
        # Gráfico simple con kivy.garden.graph
        self.graph = Graph(
            xlabel='Fecha',
            ylabel='Ingresos ($)',
            x_ticks_minor=1,
            x_ticks_major=1,
            y_ticks_major=10000,
            y_grid_label=True,
            x_grid_label=True,
            padding=5,
            x_grid=True,
            y_grid=True,
            xmin=0,
            xmax=10,
            ymin=0,
            ymax=100000,
            size_hint=(1, 0.3))
        
        self.plot = MeshLinePlot(color=[0.2, 0.6, 0.8, 1])
        self.graph.add_plot(self.plot)
        self.layout.add_widget(self.graph)
        
        total_layout = BoxLayout(size_hint_y=None, height=50)
        self.lbl_total = Label(text="Total: $0", font_size='18sp', bold=True)
        self.lbl_promedio = Label(text="Promedio: $0", font_size='18sp', bold=True)
        
        total_layout.add_widget(self.lbl_total)
        total_layout.add_widget(self.lbl_promedio)
        self.layout.add_widget(total_layout)
        
        self.tabla_detalles = MDDataTable(
            size_hint=(1, 0.4),
            use_pagination=True,
            column_data=[
                ("Fecha", dp(25)),
                ("Paciente", dp(40)),
                ("Procedimientos", dp(40)),
                ("Total", dp(25))
            ],
            row_data=[]
        )
        self.layout.add_widget(self.tabla_detalles)
        
        btn_volver = Button(
            text="Volver",
            size_hint_y=None,
            height=50,
            background_color=(0.8, 0.2, 0.2, 1))
        btn_volver.bind(on_press=self.volver)
        self.layout.add_widget(btn_volver)
        
        self.add_widget(self.layout)
        Clock.schedule_once(lambda dt: self.filtrar_dia(None))
    
    def filtrar_dia(self, instance):
        fecha = self.fecha_input.text.strip()
        
        try:
            fecha_dt = datetime.strptime(fecha, "%d-%m-%Y")
        except ValueError:
            from kivy.uix.popup import Popup
            Popup(title="Error", content=Label(text="Formato de fecha inválido (DD-MM-YYYY)"), size_hint=(0.7, 0.3)).open()
            return
        
        try:
            ingresos_ref = db.collection("ingresos")
            query = ingresos_ref.where("fecha", "==", fecha)
            resultados = query.stream()
            
            detalles = []
            total_dia = 0
            
            for doc in resultados:
                ingreso = doc.to_dict()
                proc_text = "\n".join([f"{p['descripcion']} (${p['valor']:,})" for p in ingreso.get("procedimientos", [])])
                
                detalles.append((
                    ingreso.get("fecha", ""),
                    ingreso.get("paciente_nombre", ""),
                    proc_text,
                    f"${ingreso.get('total', 0):,}"
                ))
                total_dia += ingreso.get("total", 0)
            
            detalles.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y"))
            
            self.tabla_detalles.row_data = detalles
            self.lbl_total.text = f"Total día: ${total_dia:,}"
            
            self.actualizar_grafico([fecha], [total_dia], "Ingresos del Día")
            
        except Exception as e:
            print(f"Error cargando ingresos: {e}")
            from kivy.uix.popup import Popup
            Popup(title="Error", content=Label(text=f"Error al cargar datos: {str(e)}"), size_hint=(0.7, 0.3)).open()
    
    def filtrar_mes(self, instance):
        fecha_text = self.fecha_input.text.strip()
        
        try:
            fecha_dt = datetime.strptime(fecha_text, "%d-%m-%Y")
        except ValueError:
            from kivy.uix.popup import Popup
            Popup(title="Error", content=Label(text="Formato de fecha inválido (DD-MM-YYYY)"), size_hint=(0.7, 0.3)).open()
            return
        
        mes = fecha_dt.month
        año = fecha_dt.year
        
        try:
            ingresos_ref = db.collection("ingresos")
            query = ingresos_ref
            resultados = query.stream()
            
            datos_mes = {}
            total_mes = 0
            contador_dias = 0
            
            for doc in resultados:
                ingreso = doc.to_dict()
                try:
                    fecha_ing = datetime.strptime(ingreso["fecha"], "%d-%m-%Y")
                
                    if fecha_ing.month == mes and fecha_ing.year == año:
                        fecha_str = ingreso["fecha"]
                        if fecha_str not in datos_mes:
                            datos_mes[fecha_str] = 0
                            contador_dias += 1
                        
                        datos_mes[fecha_str] += ingreso.get("total", 0)
                        total_mes += ingreso.get("total", 0)
                except:
                    continue
            
            fechas_ordenadas = sorted(datos_mes.keys(), key=lambda x: datetime.strptime(x, "%d-%m-%Y"))
            valores_ordenados = [datos_mes[f] for f in fechas_ordenadas]
            
            self.lbl_total.text = f"Total mes: ${total_mes:,}"
            promedio = total_mes / contador_dias if contador_dias > 0 else 0
            self.lbl_promedio.text = f"Promedio diario: ${promedio:,.0f}"
            
            self.actualizar_grafico(fechas_ordenadas, valores_ordenados, f"Ingresos Mensuales ({mes}/{año})")
            
            detalles = []
            for fecha, total in zip(fechas_ordenadas, valores_ordenados):
                detalles.append((fecha, f"{len([v for v in valores_ordenados if v > 0])} atenciones", "", f"${total:,}"))
            
            self.tabla_detalles.row_data = detalles
            
        except Exception as e:
            print(f"Error cargando ingresos mensuales: {e}")
            from kivy.uix.popup import Popup
            Popup(title="Error", content=Label(text=f"Error al cargar datos: {str(e)}"), size_hint=(0.7, 0.3)).open()
    
    def actualizar_grafico(self, fechas, valores, titulo):
        self.graph.xlabel = titulo
        if not valores:
            return
            
        max_val = max(valores) if valores else 1
        self.graph.ymax = max_val * 1.2  # 20% más que el valor máximo
        
        # Convertir fechas a índices numéricos para el eje X
        x_values = list(range(len(fechas)))
        points = list(zip(x_values, valores))
        
        self.plot.points = points
        self.graph.xmax = len(fechas) - 1 if len(fechas) > 1 else 1
        self.graph.x_ticks_major = 1
        
        # Actualizar etiquetas del eje X
        self.graph.x_labels = {i: fecha.split('-')[0] for i, fecha in enumerate(fechas)}
    
    def volver(self, instance):
        self.manager.current = 'main'