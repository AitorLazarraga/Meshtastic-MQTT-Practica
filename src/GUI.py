import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
import time
from pathlib import Path
import os

class GUI:
    def __init__(self, root, connector, receiver, sender, contactos):
        self.root = root
        self.root.title("Meshtastic MQTT Client")
        self.root.geometry("900x700")
        
        # Referencias a los objetos del sistema
        self.connector = connector
        self.receiver = receiver
        self.sender = sender
        self.contactos = contactos
        
        # Variables de control
        self.mensajes_mostrados = []
        self.max_mensajes = 50
        self.imagen_actual = None
        self.imagenes_recibidas = []
        
        # Crear el notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Crear las pestañas
        self.crear_pestana_mensajes()
        self.crear_pestana_directos()
        self.crear_pestana_imagenes()
        self.crear_pestana_config()
        
        # Barra de estado
        self.status_bar = tk.Label(self.root, text="Desconectado", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Iniciar actualización de mensajes
        self.actualizar_mensajes_thread()
        self.actualizar_estado_conexion()
        self.actualizar_imagenes_recibidas()
        
    def crear_pestana_mensajes(self):
        """Pestaña principal de mensajes broadcast"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Mensajes")
        
        # Frame superior para el canvas de mensajes
        frame_mensajes = ttk.LabelFrame(frame, text="Mensajes Recibidos", padding=10)
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
        
        # Frame inferior para enviar mensajes
        frame_envio = ttk.LabelFrame(frame, text="Enviar Mensaje", padding=10)
        frame_envio.pack(fill='x', padx=5, pady=5)
        
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
    
    def crear_pestana_directos(self):
        """Pestaña para mensajes directos"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Mensajes Directos")
        
        # Frame izquierdo para lista de contactos
        frame_izq = ttk.LabelFrame(frame, text="Contactos", padding=10)
        frame_izq.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        
        # Listbox para contactos
        scrollbar_contactos = tk.Scrollbar(frame_izq)
        scrollbar_contactos.pack(side='right', fill='y')
        
        self.listbox_contactos = tk.Listbox(
            frame_izq,
            width=30,
            yscrollcommand=scrollbar_contactos.set,
            font=('Arial', 10)
        )
        self.listbox_contactos.pack(side='left', fill='both', expand=True)
        scrollbar_contactos.config(command=self.listbox_contactos.yview)
        
        # Botones de gestión de contactos
        frame_btn_contactos = tk.Frame(frame_izq)
        frame_btn_contactos.pack(fill='x', pady=5)
        
        btn_actualizar = tk.Button(
            frame_btn_contactos,
            text="Actualizar",
            command=self.actualizar_lista_contactos
        )
        btn_actualizar.pack(side='left', padx=2)
        
        btn_nuevo = tk.Button(
            frame_btn_contactos,
            text="Nuevo",
            command=self.agregar_contacto_manual
        )
        btn_nuevo.pack(side='left', padx=2)
        
        # Frame derecho para chat
        frame_der = ttk.Frame(frame)
        frame_der.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        # Área de mensajes del chat
        frame_chat = ttk.LabelFrame(frame_der, text="Conversación", padding=10)
        frame_chat.pack(fill='both', expand=True)
        
        self.canvas_chat = scrolledtext.ScrolledText(
            frame_chat,
            wrap=tk.WORD,
            width=50,
            height=20,
            state='disabled',
            font=('Courier', 9)
        )
        self.canvas_chat.pack(fill='both', expand=True)
        
        # Frame para enviar mensaje directo
        frame_envio_directo = ttk.Frame(frame_der)
        frame_envio_directo.pack(fill='x', pady=5)
        
        tk.Label(frame_envio_directo, text="Mensaje:").pack(side='left', padx=5)
        self.entry_mensaje_directo = tk.Entry(frame_envio_directo, width=40)
        self.entry_mensaje_directo.pack(side='left', padx=5, fill='x', expand=True)
        self.entry_mensaje_directo.bind('<Return>', lambda e: self.enviar_mensaje_directo())
        
        btn_enviar_directo = tk.Button(
            frame_envio_directo,
            text="Enviar",
            command=self.enviar_mensaje_directo,
            bg='#4CAF50',
            fg='white'
        )
        btn_enviar_directo.pack(side='left', padx=5)
        
        btn_enviar_img_directo = tk.Button(
            frame_envio_directo,
            text="Enviar Imagen",
            command=self.enviar_imagen_directa,
            bg='#2196F3',
            fg='white'
        )
        btn_enviar_img_directo.pack(side='left', padx=5)
        
        # Cargar contactos inicialmente
        self.actualizar_lista_contactos()
    
    def crear_pestana_imagenes(self):
        """Pestaña para visualizar imágenes recibidas"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Imágenes")
        
        # Frame superior con lista de imágenes
        frame_lista = ttk.LabelFrame(frame, text="Imágenes Recibidas", padding=10)
        frame_lista.pack(fill='x', padx=5, pady=5)
        
        # Listbox para imágenes
        scrollbar_imgs = tk.Scrollbar(frame_lista)
        scrollbar_imgs.pack(side='right', fill='y')
        
        self.listbox_imagenes = tk.Listbox(
            frame_lista,
            height=5,
            yscrollcommand=scrollbar_imgs.set,
            font=('Arial', 10)
        )
        self.listbox_imagenes.pack(side='left', fill='both', expand=True)
        scrollbar_imgs.config(command=self.listbox_imagenes.yview)
        self.listbox_imagenes.bind('<<ListboxSelect>>', self.mostrar_imagen_seleccionada)
        
        # Barra de progreso para recepción de imágenes
        frame_progreso = ttk.Frame(frame)
        frame_progreso.pack(fill='x', padx=5, pady=5)
        
        tk.Label(frame_progreso, text="Recepción de imagen:").pack(side='left', padx=5)
        self.progress_imagen = ttk.Progressbar(
            frame_progreso,
            mode='determinate',
            length=300
        )
        self.progress_imagen.pack(side='left', fill='x', expand=True, padx=5)
        self.label_progreso = tk.Label(frame_progreso, text="0%")
        self.label_progreso.pack(side='left', padx=5)

        self.label_idimg = tk.Label(frame_progreso, text= f"{self.receiver.id_actual}")
        self.label_idimg.pack(side="bottom", padx=3)
        
        # Frame para visualizar imagen
        frame_visor = ttk.LabelFrame(frame, text="Vista Previa", padding=10)
        frame_visor.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Canvas para mostrar imagen
        self.canvas_imagen = tk.Canvas(frame_visor, bg='gray90')
        self.canvas_imagen.pack(fill='both', expand=True)
        
        # Botón para abrir imagen
        btn_abrir = tk.Button(
            frame_visor,
            text="Abrir en Visor Externo",
            command=self.abrir_imagen_externa,
            bg='#FF9800',
            fg='white'
        )
        btn_abrir.pack(pady=5)
    
    def crear_pestana_config(self):
        """Pestaña de configuración"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Configuración")
        
        # Frame de información de conexión
        frame_info = ttk.LabelFrame(frame, text="Información de Conexión", padding=10)
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
        frame_opciones = ttk.LabelFrame(frame, text="Opciones", padding=10)
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
    
    # === FUNCIONES DE MENSAJES ===
    
    def agregar_mensaje_canvas(self, mensaje, tag='recibido'):
        """Agrega un mensaje al canvas principal"""
        self.canvas_mensajes.config(state='normal')
        self.canvas_mensajes.insert(tk.END, mensaje + '\n', tag)
        self.canvas_mensajes.see(tk.END)
        self.canvas_mensajes.config(state='disabled')
        
        # Limitar número de mensajes mostrados
        self.mensajes_mostrados.append(mensaje)
        if len(self.mensajes_mostrados) > self.max_mensajes:
            self.mensajes_mostrados.pop(0)
            # Borrar primera línea
            self.canvas_mensajes.config(state='normal')
            self.canvas_mensajes.delete('1.0', '2.0')
            self.canvas_mensajes.config(state='disabled')
    
    def enviar_mensaje_broadcast(self):
        """Envía un mensaje a broadcast"""
        mensaje = self.entry_mensaje.get().strip()
        if not mensaje:
            return
        
        if not self.connector.is_connected():
            messagebox.showwarning("Advertencia", "No estás conectado al broker")
            return
        
        try:
            from meshtastic import BROADCAST_NUM
            self.sender.send_message(BROADCAST_NUM, mensaje)
            self.agregar_mensaje_canvas(f"[ENVIADO] {mensaje}", 'enviado')
            self.entry_mensaje.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar mensaje: {str(e)}")
    
    def enviar_imagen_broadcast(self):
        """Envía una imagen a broadcast"""
        foto = filedialog.askopenfilename(
            title="Selecciona una Imagen para Enviar",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")]
        )
        
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
            
            # Enviar en thread separado
            def enviar_thread():
                self.sender.send_img(BROADCAST_NUM, partes_imagen, cantidad_paquetes, id_imagen, tipo_imagen)
                self.agregar_mensaje_canvas(f"[SISTEMA] Imagen '{id_imagen}' enviada correctamente", 'sistema')
            
            threading.Thread(target=enviar_thread, daemon=True).start()
            self.agregar_mensaje_canvas(f"[SISTEMA] Enviando imagen '{id_imagen}'...", 'sistema')
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar imagen: {str(e)}")
    
    def actualizar_mensajes_thread(self):
        """Actualiza el canvas con nuevos mensajes del receiver"""
        def verificar_mensajes():
            # Verificar diccionario de mensajes del receiver
            if hasattr(self.receiver, 'mensajes') and self.receiver.mensajes:
                for key in sorted(self.receiver.mensajes.keys()):
                    mensaje = str(self.receiver.mensajes[key])
                    if mensaje not in self.mensajes_mostrados:
                        self.agregar_mensaje_canvas(mensaje, 'recibido')
            
            # Programar próxima verificación
            self.root.after(1000, verificar_mensajes)
        
        verificar_mensajes()
    
    def actualizar_progreso_imagen(self):
        """Actualiza la barra de progreso de recepción de imagen"""
        def verificar_progreso():
            if hasattr(self.receiver, 'flag_imagen') and self.receiver.flag_imagen:
                if hasattr(self.receiver, 'partes_esperadas') and self.receiver.partes_esperadas > 0:
                    partes_recibidas = len(self.receiver.partes_imagen)
                    progreso = (partes_recibidas / self.receiver.partes_esperadas) * 100
                    self.progress_imagen['value'] = progreso
                    self.label_progreso.config(text=f"{int(progreso)}%")
            else:
                self.progress_imagen['value'] = 0
                self.label_progreso.config(text="0%")
            
            self.root.after(500, verificar_progreso)
        
        verificar_progreso()
    
    # === FUNCIONES DE MENSAJES DIRECTOS ===
    
    def actualizar_lista_contactos(self):
        """Actualiza la lista de contactos"""
        self.listbox_contactos.delete(0, tk.END)
        self.contactos.lista_contactos = self.contactos.lista_contactos
        
        if not self.contactos.lista_contactos.empty:
            for _, fila in self.contactos.lista_contactos.iterrows():
                self.listbox_contactos.insert(tk.END, f"{fila['Nombre']} ({fila['ID']})")
    
    def agregar_contacto_manual(self):
        """Permite agregar un contacto manualmente"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Contacto")
        dialog.geometry("300x150")
        
        tk.Label(dialog, text="ID del contacto:").pack(pady=5)
        entry_id = tk.Entry(dialog, width=30)
        entry_id.pack(pady=5)
        
        tk.Label(dialog, text="Nombre:").pack(pady=5)
        entry_nombre = tk.Entry(dialog, width=30)
        entry_nombre.pack(pady=5)
        
        def guardar():
            id_contacto = entry_id.get().strip()
            nombre = entry_nombre.get().strip()
            if id_contacto and nombre:
                self.contactos.anadir_contacto(id_contacto, nombre)
                self.actualizar_lista_contactos()
                dialog.destroy()
        
        tk.Button(dialog, text="Guardar", command=guardar, bg='#4CAF50', fg='white').pack(pady=10)
    
    def enviar_mensaje_directo(self):
        """Envía un mensaje directo al contacto seleccionado"""
        seleccion = self.listbox_contactos.curselection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un contacto primero")
            return
        
        mensaje = self.entry_mensaje_directo.get().strip()
        if not mensaje:
            return
        
        # Obtener nombre del contacto seleccionado
        contacto_texto = self.listbox_contactos.get(seleccion[0])
        nombre = contacto_texto.split(' (')[0]
        
        # Obtener ID del contacto
        id_envio = self.contactos.elegir_contacto(nombre)
        if id_envio is None:
            messagebox.showerror("Error", "No se pudo obtener el ID del contacto")
            return
        
        try:
            id_envio = int(id_envio.replace("!", ""), 16)
            self.sender.send_message(id_envio, mensaje)
            
            # Mostrar en el chat
            self.canvas_chat.config(state='normal')
            self.canvas_chat.insert(tk.END, f"Tú: {mensaje}\n", 'enviado')
            self.canvas_chat.see(tk.END)
            self.canvas_chat.config(state='disabled')
            
            self.entry_mensaje_directo.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar mensaje: {str(e)}")
    
    def enviar_imagen_directa(self):
        """Envía una imagen al contacto seleccionado"""
        seleccion = self.listbox_contactos.curselection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un contacto primero")
            return
        
        foto = filedialog.askopenfilename(
            title="Selecciona una Imagen para Enviar",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")]
        )
        
        if not foto:
            return
        
        # Obtener nombre del contacto
        contacto_texto = self.listbox_contactos.get(seleccion[0])
        nombre = contacto_texto.split(' (')[0]
        
        id_envio = self.contactos.elegir_contacto(nombre)
        if id_envio is None:
            messagebox.showerror("Error", "No se pudo obtener el ID del contacto")
            return
        
        try:
            from src.ImageEncoder import ImageEncoder
            
            id_envio = int(id_envio.replace("!", ""), 16)
            encoder = ImageEncoder()
            nombre_img = Path(foto)
            id_imagen = nombre_img.stem
            
            cadena64, tipo_imagen = encoder.imagen_a_cadena(foto)
            partes_imagen, cantidad_paquetes = encoder.fragmentar_payload(cadena64, id_imagen)
            
            def enviar_thread():
                self.sender.send_img(id_envio, partes_imagen, cantidad_paquetes, id_imagen, tipo_imagen)
                self.canvas_chat.config(state='normal')
                self.canvas_chat.insert(tk.END, f"[Imagen '{id_imagen}' enviada]\n", 'sistema')
                self.canvas_chat.see(tk.END)
                self.canvas_chat.config(state='disabled')
            
            threading.Thread(target=enviar_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar imagen: {str(e)}")
    
    # === FUNCIONES DE IMÁGENES ===
    
    def actualizar_imagenes_recibidas(self):
        """Actualiza la lista de imágenes recibidas"""
        def verificar_imagenes():
            ruta_imagenes = Path("Datos/Imagenes")
            if ruta_imagenes.exists():
                imagenes = list(ruta_imagenes.glob("imagen_recibida_*"))
                
                # Agregar nuevas imágenes a la lista
                for img in imagenes:
                    if str(img) not in self.imagenes_recibidas:
                        self.imagenes_recibidas.append(str(img))
                        self.listbox_imagenes.insert(tk.END, img.name)
            
            self.root.after(2000, verificar_imagenes)
        
        verificar_imagenes()
    
    def mostrar_imagen_seleccionada(self, event):
        """Muestra la imagen seleccionada en el canvas"""
        seleccion = self.listbox_imagenes.curselection()
        if not seleccion:
            return
        
        ruta_imagen = self.imagenes_recibidas[seleccion[0]]
        
        try:
            # Cargar imagen
            img = Image.open(ruta_imagen)
            
            # Redimensionar para ajustar al canvas
            canvas_width = self.canvas_imagen.winfo_width()
            canvas_height = self.canvas_imagen.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                img.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)
            
            # Convertir a PhotoImage
            self.imagen_actual = ImageTk.PhotoImage(img)
            
            # Limpiar canvas y mostrar imagen
            self.canvas_imagen.delete("all")
            self.canvas_imagen.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self.imagen_actual,
                anchor='center'
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar imagen: {str(e)}")
    
    def abrir_imagen_externa(self):
        """Abre la imagen seleccionada en el visor externo"""
        seleccion = self.listbox_imagenes.curselection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una imagen primero")
            return
        
        ruta_imagen = self.imagenes_recibidas[seleccion[0]]
        
        try:
            import platform
            import subprocess
            
            if platform.system() == 'Windows':
                os.startfile(ruta_imagen)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', ruta_imagen])
            else:  # Linux
                subprocess.call(['xdg-open', ruta_imagen])
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir imagen: {str(e)}")
    
    # === FUNCIONES DE CONFIGURACIÓN ===
    
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
            self.agregar_mensaje_canvas(f"[SISTEMA] Cambiado a broker: {self.connector.mqtt_broker}", 'sistema')
    
    def enviar_posicion(self):
        """Envía la posición del nodo"""
        try:
            from meshtastic import BROADCAST_NUM
            self.sender.send_position(BROADCAST_NUM)
            self.agregar_mensaje_canvas("[SISTEMA] Posición enviada", 'sistema')
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar posición: {str(e)}")
    
    def enviar_nodeinfo(self):
        """Envía información del nodo"""
        try:
            from meshtastic import BROADCAST_NUM
            self.sender.send_node_info(BROADCAST_NUM, want_response=False)
            self.agregar_mensaje_canvas("[SISTEMA] Info de nodo enviada", 'sistema')
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar info: {str(e)}")
    
    def limpiar_mensajes(self):
        """Limpia el canvas de mensajes"""
        self.canvas_mensajes.config(state='normal')
        self.canvas_mensajes.delete('1.0', tk.END)
        self.canvas_mensajes.config(state='disabled')
        self.mensajes_mostrados.clear()
        self.agregar_mensaje_canvas("[SISTEMA] Mensajes limpiados", 'sistema')
    
    def actualizar_estado_conexion(self):
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
        # Iniciar también actualización de progreso
        self.actualizar_progreso_imagen()