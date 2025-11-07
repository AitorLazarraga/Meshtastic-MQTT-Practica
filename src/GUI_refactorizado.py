import tkinter as tk
from tkinter import ttk

# Importar las pestañas modulares
from src.GUI.Pest_mensajes import PestanaMensajes
from src.GUI.Pest_directos import PestanaDirectos
from src.GUI.Pest_img import PestanaImagenes
from src.GUI.Pest_config import PestanaConfig
from src.GUI.Pest_map import VerMap
from src.GUI.Pest_dron import Pest_dron


class GUI:
    """Interfaz gráfica principal - Coordinador de pestañas"""
    
    def __init__(self, root, connector=None, receiver=None, sender=None, contactos=None, onlydron=False):
        self.root = root
        self.root.title("Meshtastic MQTT Client")
        self.root.geometry("900x700")
        
        # Referencias a los objetos del sistema
        self.connector = connector
        self.receiver = receiver
        self.sender = sender
        self.contactos = contactos
        
        # Crear el notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        if onlydron == False:
            # Crear las pestañas (ahora son objetos independientes)
            self.pestana_mensajes = PestanaMensajes(
                self.notebook, 
                self.connector, 
                self.receiver, 
                self.sender
            )
            
            self.pestana_directos = PestanaDirectos(
                self.notebook,
                self.connector,
                self.receiver,
                self.sender,
                self.contactos
            )
            
            self.pestana_imagenes = PestanaImagenes(
                self.notebook,
                self.receiver
            )
            
            self.pestana_config = PestanaConfig(
                self.notebook,
                self.connector,
                self.sender,
                self.pestana_mensajes  # Para poder agregar mensajes del sistema
            )
            
            self.mapa = VerMap(self.notebook)
            self.mapa.cargar_csv()
            
        elif onlydron == True:
            self.pestana_dron = Pest_dron(
                self.notebook,
                self.receiver
            )
        

        # Barra de estado
        self.status_bar = tk.Label(
            self.root, 
            text="Desconectado", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Iniciar actualización de estado de conexión
        self._actualizar_estado_conexion()
    
    def _actualizar_estado_conexion(self):
        """Actualiza la barra de estado con el estado de conexión"""
        def verificar_estado():
            if self.connector.is_connected():
                self.status_bar.config(
                    text=f"Conectado a: {self.connector.mqtt_broker}",
                    bg='#4CAF50',
                    fg='white'
                )
            else:
                self.status_bar.config(
                    text="Desconectado",
                    bg='#F44336',
                    fg='white'
                )
            
            self.root.after(2000, verificar_estado)
        
        verificar_estado()