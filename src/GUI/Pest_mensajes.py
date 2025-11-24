import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path


class PestanaMensajes:
    """Pestaña principal de mensajes broadcast"""
    
    def __init__(self, notebook, connector, receiver, sender, serial_receiver):
        self.notebook = notebook
        self.connector = connector
        self.receiver = receiver
        self.sender = sender
        self.modo_envio = tk.StringVar(value="mqtt")
        self.serial_receiver = serial_receiver  # NUEVO
        
        # Variables de control
        self.mensajes_mostrados = []
        self.max_mensajes = 50
        
        # Crear frame principal
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Mensajes")
        
        self._crear_interfaz()
        self._iniciar_actualizacion()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la pestaña"""
        # Frame superior para el canvas de mensajes
        frame_mensajes = ttk.LabelFrame(self.frame, text="Mensajes Recibidos", padding=10)
        frame_mensajes.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Canvas con scrollbar para mensajes
        self.canvas_mensajes = scrolledtext.ScrolledText(
            frame_mensajes,
            wrap=tk.WORD,
            width=80,
            height=25,
            state='disabled',
            font=('Courier', 9)
        )
        self.canvas_mensajes.pack(fill='both', expand=True)
        
        # Configurar tags para colores
        self.canvas_mensajes.tag_config('recibido', foreground='blue')
        self.canvas_mensajes.tag_config('enviado', foreground='green')
        self.canvas_mensajes.tag_config('sistema', foreground='red')
        self.canvas_mensajes.tag_config('serial', foreground='purple')
        
        # Frame inferior para enviar mensajes
        frame_envio = ttk.LabelFrame(self.frame, text="Enviar Mensaje", padding=10)
        frame_envio.pack(fill='x', padx=5, pady=5)

        frame_modo = ttk.Frame(frame_envio)
        frame_modo.pack(side='left', padx=5)
        tk.Label(frame_modo, text="Enviar por:").pack(side='top')
        radio_mqtt = ttk.Radiobutton(
            frame_modo, 
            text="MQTT", 
            variable=self.modo_envio, 
            value="mqtt"
        )
        radio_mqtt.pack(side='left')
        
        radio_serial = ttk.Radiobutton(
            frame_modo, 
            text="Serial", 
            variable=self.modo_envio, 
            value="serial"
        )
        radio_serial.pack(side='left')
        
        # Entry para escribir mensaje
        tk.Label(frame_envio, text="Mensaje:").pack(side='left', padx=5)
        self.entry_mensaje = tk.Entry(frame_envio, width=60)
        self.entry_mensaje.pack(side='left', padx=5, fill='x', expand=True)
        self.entry_mensaje.bind('<Return>', lambda e: self.enviar_mensaje_broadcast())
        
        # Botón enviar
        btn_enviar = tk.Button(
            frame_envio,
            text="Enviar",
            command=self.enviar_mensaje_broadcast,
            bg='#4CAF50',
            fg='white',
            padx=20
        )
        btn_enviar.pack(side='left', padx=5)
        
        # Botón enviar imagen
        btn_enviar_img = tk.Button(
            frame_envio,
            text="Enviar Imagen",
            command=self.enviar_imagen_broadcast,
            bg='#2196F3',
            fg='white',
            padx=10
        )
        btn_enviar_img.pack(side='left', padx=5)
    
    def agregar_mensaje(self, mensaje, tag='recibido'):
        """Agrega un mensaje al canvas"""
        self.canvas_mensajes.config(state='normal')
        try:
            self.canvas_mensajes.insert(tk.END, mensaje + '\n', tag)
            self.canvas_mensajes.see(tk.END)
        except:
            self.canvas_mensajes.insert(tk.END, "FALLO DE RECEPCIÓN\n", tag)
            self.canvas_mensajes.see(tk.END)
        finally:
            self.canvas_mensajes.config(state='disabled')
        
        # Limitar número de mensajes mostrados
        self.mensajes_mostrados.append(mensaje)
        if len(self.mensajes_mostrados) > self.max_mensajes:
            self.mensajes_mostrados.pop(0)
            self.canvas_mensajes.config(state='normal')
            self.canvas_mensajes.delete('1.0', '2.0')
            self.canvas_mensajes.config(state='disabled')
    
    def enviar_mensaje_broadcast(self):
        """Envía un mensaje a broadcast o por serial según el modo seleccionado"""
        mensaje = self.entry_mensaje.get().strip()
        if not mensaje:
            return
        
        modo = self.modo_envio.get()
        
        if modo == "serial":
            # Enviar por serial
            if self.serial_receiver is None:
                messagebox.showwarning("Advertencia", "Receptor serial no configurado")
                return
            
            if not self.serial_receiver.is_connected():
                messagebox.showwarning("Advertencia", "Puerto serial no conectado")
                return
            
            try:
                if self.sender.send_message_serial(mensaje):
                    self.agregar_mensaje(f"[SERIAL ENVIADO] {mensaje}", 'enviado')
                    self.entry_mensaje.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar por serial: {str(e)}")
        
        else:  # modo == "mqtt"
            if not self.connector.is_connected():
                messagebox.showwarning("Advertencia", "No estás conectado al broker MQTT")
                return
            
            try:
                from meshtastic import BROADCAST_NUM
                self.sender.send_message(BROADCAST_NUM, mensaje)
                self.agregar_mensaje(f"[MQTT ENVIADO] {mensaje}", 'enviado')
                self.entry_mensaje.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Error al enviar por MQTT: {str(e)}")
    
    def enviar_imagen_broadcast(self, imagen=None):
        """Envía una imagen a broadcast"""
        if not imagen:
            foto = filedialog.askopenfilename(
                title="Selecciona una Imagen para Enviar",
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")]
            )
        else:
            foto = imagen
            print(foto)
        
        if not foto:
            return
        
        try:
            from meshtastic import BROADCAST_NUM
            from src.ImageEncoder import ImageEncoder
            
            encoder = ImageEncoder()
            nombre = Path(foto)
            id_imagen = nombre.stem
            
            cadena64, tipo_imagen = encoder.imagen_a_cadena(foto)
            partes_imagen, cantidad_paquetes = encoder.fragmentar_payload(cadena64, id_imagen)
            
            def enviar_thread():
                if self.connector.is_connected():
                    self.sender.send_img(BROADCAST_NUM, partes_imagen, cantidad_paquetes, id_imagen, tipo_imagen)
                else:
                    self.sender.send_serial_img(partes_imagen, cantidad_paquetes, id_imagen, tipo_imagen)
                self.agregar_mensaje(f"[SISTEMA] Imagen '{id_imagen}' enviada correctamente", 'sistema')
            
            threading.Thread(target=enviar_thread, daemon=True).start()
            self.agregar_mensaje(f"[SISTEMA] Enviando imagen '{id_imagen}'...", 'sistema')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar imagen: {str(e)}")
    
    def _iniciar_actualizacion(self):
        """Inicia la actualización automática de mensajes"""
        def verificar_mensajes():
            try:
                # Procesar mensajes de texto
                if hasattr(self.receiver.texto, 'nuevos_mensajes'):
                    while len(self.receiver.texto.nuevos_mensajes) > 0:
                        mensaje = self.receiver.texto.nuevos_mensajes.pop(0)
                        self.agregar_mensaje(str(mensaje), 'recibido')
                
                # Procesar mensajes de telemetría
                if hasattr(self.receiver.telemetria, 'nuevos_mensajes'):
                    while len(self.receiver.telemetria.nuevos_mensajes) > 0:
                        mensaje = self.receiver.telemetria.nuevos_mensajes.pop(0)
                        if isinstance(mensaje, dict):
                            mensaje = f"Telemetría: {mensaje.get('long_name', '?')} - Hora: {mensaje.get('Hora', '?')}"
                        self.agregar_mensaje(str(mensaje), 'recibido')
                
                # Procesar mensajes de posición
                if hasattr(self.receiver.posicion, 'nuevos_mensajes'):
                    while len(self.receiver.posicion.nuevos_mensajes) > 0:
                        mensaje = self.receiver.posicion.nuevos_mensajes.pop(0)
                        self.agregar_mensaje(str(mensaje), 'recibido')

                if self.serial_receiver and hasattr(self.serial_receiver, 'nuevos_mensajes'):
                    while len(self.serial_receiver.nuevos_mensajes) > 0:
                        mensaje = self.serial_receiver.nuevos_mensajes.pop(0)
                        self.agregar_mensaje(str(mensaje), 'serial')
            
            except Exception as e:
                print(f"Error al actualizar mensajes: {e}")
            
            self.frame.after(500, verificar_mensajes)
        
        verificar_mensajes()
    
    def limpiar_mensajes(self):
        """Limpia el canvas de mensajes"""
        self.canvas_mensajes.config(state='normal')
        self.canvas_mensajes.delete('1.0', tk.END)
        self.canvas_mensajes.config(state='disabled')
        self.mensajes_mostrados.clear()
        self.agregar_mensaje("[SISTEMA] Mensajes limpiados", 'sistema')