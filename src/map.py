import tkinter as tk
from tkinter import ttk
import tkintermapview
import pandas as pd
import os

class VerMap(tk.Toplevel):
    """Ventana con mapa para visualizar posiciones GPS"""
    
    def __init__(self, parent, csv_file="Datos/posiciones.csv"):
        super().__init__(parent)
        
        self.csv_file = csv_file
        self.markers = []
        self.paths = []
        self.notebook = parent
        #self.title("Mapa de Posiciones GPS")
        #self.geometry("800x600")
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Mapa GPS")
    
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(control_frame, text="Recargar Posiciones", 
                   command=self.reload_positions).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Centrar Mapa", 
                   command=self.center_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Limpiar Marcadores", 
                   command=self.clear_markers).pack(side=tk.LEFT, padx=5)
        
        self.show_path_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Mostrar Ruta", 
                        variable=self.show_path_var,
                        command=self.toggle_path).pack(side=tk.LEFT, padx=5)
        
        self.info_label = ttk.Label(control_frame, text="Posiciones: 0")
        self.info_label.pack(side=tk.RIGHT, padx=5)
        
        self.map_widget = tkintermapview.TkinterMapView(main_frame, 
                                                         width=800, 
                                                         height=500, 
                                                         corner_radius=0)
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configurar mapa inicial (centrado en Bilbao)
        self.map_widget.set_position(43.2630, -2.9350)
        self.map_widget.set_zoom(12)
    
        self.reload_positions()

        self.auto_update()

    def cargar_csv(self):
        if not os.path.exists(self.csv_file):
            return []
        df = pd.read_csv(self.csv_file)
        try:
            posiciones = []
            for _, row in df.iterrows():
                lat = row['lat']
                lon = row['lon']
                alt = row['alt']

                if abs(lat) > 180 or abs(lon) > 180:
                    lat = lat / 1e7
                    lon = lon / 1e7
                
                if not lat == 0 and not lon == 0:
                    posiciones.append((lat,lon,alt))
            
            return posiciones
        except Exception as e:
            print(f"Error al leer el CSV de posiciones: {e}")
            return []
    
    def reload_positions(self):
        self.clear_markers()
        posiciones = self.cargar_csv()
        for i, (lat, lon, alt)in enumerate(posiciones):
            marker = self.map_widget.set_marker(lat, lon, 
                                                text=f"Posición {alt}m")
            self.markers.append(marker)
        
        self.info_label.config(text=f"Posiciones: {len(self.markers)}")
        if posiciones:
            last_lat, last_lon, _ = posiciones[-1]
            self.map_widget.set_position(last_lat, last_lon)
        
        # Actualizar ruta si está activada
        if self.show_path_var.get():
            self.draw_path(posiciones)
        
    def draw_path(self, positions):
        """Dibuja una línea conectando todas las posiciones"""
        self.clear_paths()
        
        if len(positions) < 2:
            return
        
        # Crear lista de coordenadas para el path
        coords = [(lat, lon) for lat, lon, _ in positions]
        
        # Dibujar el path
        path = self.map_widget.set_path(coords)
        self.paths.append(path)
    
    def clear_paths(self):
        """Elimina todas las rutas del mapa"""
        for path in self.paths:
            path.delete()
        self.paths.clear()
    
    def toggle_path(self):
        """Activa/desactiva la visualización de la ruta"""
        if self.show_path_var.get():
            positions = self.cargar_csv()
            self.draw_path(positions)
        else:
            self.clear_paths()

    def clear_markers(self):
        """Elimina todos los marcadores del mapa"""
        for marker in self.markers:
            marker.delete()
        self.markers.clear()
        self.clear_paths()
    
    def center_map(self):
        """Centra el mapa en la última posición"""
        positions = self.cargar_csv()
        if positions:
            last_lat, last_lon, _ = positions[-1]
            self.map_widget.set_position(last_lat, last_lon)
            self.map_widget.set_zoom(15)
    
    def auto_update(self):
        """Actualiza el mapa automáticamente cada 10 segundos"""
        self.reload_positions()
        self.after(10000, self.auto_update)