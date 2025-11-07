import tkinter as tk
from tkinter import ttk, messagebox
import time


class PestanaConfig:
    """Pestaña de configuración"""
    
    def __init__(self, notebook, connector, sender, pestana_mensajes):
        self.notebook = notebook
        self.connector = connector
        self.sender = sender
        self.pestana_mensajes = pestana_mensajes  # Referencia para agregar mensajes
        
        # Crear frame principal
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Configuración")
        
        self._crear_interfaz()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la pestaña"""
        # Frame de información de conexión
        frame_info = ttk.LabelFrame(self.frame, text="Información de Conexión", padding=10)
        frame_info.pack(fill='x', padx=5, pady=5)
        
        # Mostrar información
        info_text = f"""
        Broker: {self.connector.mqtt_broker}
        Puerto: {self.connector.mqtt_port}
        Nodo: {self.connector.node_name}
        Canal: {self.connector.channel}
        """
        
        tk.Label(frame_info, text=info_text, justify='left', font=('Courier', 10)).pack()
        
        # Frame de opciones
        frame_opciones = ttk.LabelFrame(self.frame, text="Opciones", padding=10)
        frame_opciones.pack(fill='x', padx=5, pady=5)
        
        # Botón cambiar broker
        btn_cambiar_broker = tk.Button(
            frame_opciones,
            text="Cambiar Broker",
            command=self.cambiar_broker,
            bg='#9C27B0',
            fg='white',
            padx=20
        )
        btn_cambiar_broker.pack(pady=5)
        
        # Botón enviar posición
        btn_posicion = tk.Button(
            frame_opciones,
            text="Enviar Posición",
            command=self.enviar_posicion,
            bg='#00BCD4',
            fg='white',
            padx=20
        )
        btn_posicion.pack(pady=5)
        
        # Botón enviar info nodo
        btn_nodeinfo = tk.Button(
            frame_opciones,
            text="Enviar Info Nodo",
            command=self.enviar_nodeinfo,
            bg='#3F51B5',
            fg='white',
            padx=20
        )
        btn_nodeinfo.pack(pady=5)
        
        # Botón limpiar mensajes
        btn_limpiar = tk.Button(
            frame_opciones,
            text="Limpiar Mensajes",
            command=self.limpiar_mensajes,
            bg='#F44336',
            fg='white',
            padx=20
        )
        btn_limpiar.pack(pady=5)
    
    def cambiar_broker(self):
        """Cambia entre brokers"""
        if self.connector.mqtt_broker == self.connector.meshtastic_broker:
            respuesta = messagebox.askyesno(
                "Cambiar Broker",
                "¿Deseas cambiar al broker EMQX?"
            )
            if respuesta:
                self.connector.mqtt_broker = self.connector.mqttS_broker
        else:
            respuesta = messagebox.askyesno(
                "Cambiar Broker",
                "¿Deseas cambiar al broker Meshtastic?"
            )
            if respuesta:
                self.connector.mqtt_broker = self.connector.meshtastic_broker
        
        if respuesta:
            self.connector.disconnect_mqtt()
            time.sleep(2)
            self.connector.subscribe_topic = ""
            self.connector.publish_topic = ""
            self.connector.connect_mqtt()
            self.pestana_mensajes.agregar_mensaje(
                f"[SISTEMA] Cambiado a broker: {self.connector.mqtt_broker}", 
                'sistema'
            )
    
    def enviar_posicion(self):
        """Envía la posición del nodo"""
        try:
            from meshtastic import BROADCAST_NUM
            self.sender.send_position(BROADCAST_NUM)
            self.pestana_mensajes.agregar_mensaje("[SISTEMA] Posición enviada", 'sistema')
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar posición: {str(e)}")
    
    def enviar_nodeinfo(self):
        """Envía información del nodo"""
        try:
            from meshtastic import BROADCAST_NUM
            self.sender.send_node_info(BROADCAST_NUM, want_response=False)
            self.pestana_mensajes.agregar_mensaje("[SISTEMA] Info de nodo enviada", 'sistema')
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar info: {str(e)}")
    
    def limpiar_mensajes(self):
        """Limpia el canvas de mensajes"""
        self.pestana_mensajes.limpiar_mensajes()