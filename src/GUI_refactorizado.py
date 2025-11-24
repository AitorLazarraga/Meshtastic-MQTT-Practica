import tkinter as tk
from tkinter import ttk

# Importar las pestañas modulares
from src.GUI.Pest_mensajes import PestanaMensajes
from src.GUI.Pest_directos import PestanaDirectos
from src.GUI.Pest_img import PestanaImagenes
from src.GUI.Pest_config import PestanaConfig
from src.GUI.Pest_map import VerMap
from src.GUI.Pest_dron import Pest_dron
from src.ConDron import ConDron


class GUI:
    """Interfaz gráfica principal - Coordinador de pestañas"""
    
    def __init__(self, root, connector=None, receiver=None, sender=None, contactos=None, onlydron=False, serial_receiver=None):
        self.root = root
        self.root.title("Meshtastic MQTT Client")
        self.root.geometry("900x700")
        
        # Referencias a los objetos del sistema
        self.connector = connector
        self.receiver = receiver
        self.sender = sender
        self.contactos = contactos
        self.serial_receiver = serial_receiver 
        self.controlador = ConDron() 
    
    # Variable para modo de envío
        self.modo_envio = tk.StringVar(value="mqtt")

        # Crear el notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        if onlydron == False:
            # Crear las pestañas (ahora son objetos independientes)
            self.pestana_mensajes = PestanaMensajes(
                self.notebook, 
                self.connector, 
                self.receiver, 
                self.sender,
                self.serial_receiver
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
            
            self.pestana_dron = Pest_dron(
                self.notebook,
                self.receiver
            )

            self.controlador.set_pestana(self.pestana_dron)

            self.pestana_dron.set_envio_imagen_callback(self.pestana_mensajes.enviar_imagen_broadcast)


            self.mapa = VerMap(self.notebook)
            self.mapa.cargar_csv()
            
        elif onlydron == True:
            # Crear las pestañas (ahora son objetos independientes)
            self.pestana_mensajes = PestanaMensajes(
                self.notebook, 
                self.connector, 
                self.receiver, 
                self.sender,
                self.serial_receiver
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
        self.actualizar_estado_conexion()
    
    def actualizar_estado_conexion(self):
        """Actualiza la barra de estado con el estado de conexión"""
        def verificar_estado():
            mqtt_conn = "MQTT: ✓" if self.connector.is_connected() else "MQTT: ✗"
            
            serial_conn = "Serial: ✓" if (self.serial_receiver and self.serial_receiver.is_connected()) else "Serial: ✗"
            
            texto_estado = f"{mqtt_conn} | {serial_conn} | Broker: {self.connector.mqtt_broker}"
            
            if self.connector.is_connected() or (self.serial_receiver and self.serial_receiver.is_connected()):
                self.status_bar.config(
                    text=texto_estado,
                    bg='#4CAF50',
                    fg='white'
                )
            else:
                self.status_bar.config(
                    text=texto_estado,
                    bg='#F44336',
                    fg='white'
                )
            
            self.root.after(2000, verificar_estado)
        
        verificar_estado()