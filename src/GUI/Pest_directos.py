import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path


class PestanaDirectos:
    """Pestaña para mensajes directos"""
    
    def __init__(self, notebook, connector, receiver, sender, contactos):
        self.notebook = notebook
        self.connector = connector
        self.receiver = receiver
        self.sender = sender
        self.contactos = contactos
        
        # Crear frame principal
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Mensajes Directos")
        
        self._crear_interfaz()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la pestaña"""
        # Frame izquierdo para lista de contactos
        frame_izq = ttk.LabelFrame(self.frame, text="Contactos", padding=10)
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
        frame_der = ttk.Frame(self.frame)
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
        
        # Configurar tags para colores
        self.canvas_chat.tag_config('recibido', foreground='blue')
        self.canvas_chat.tag_config('enviado', foreground='green')
        self.canvas_chat.tag_config('sistema', foreground='red')
        
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
    
    def actualizar_lista_contactos(self):
        """Actualiza la lista de contactos"""
        self.listbox_contactos.delete(0, tk.END)
        
        if not self.contactos.lista_contactos.empty:
            for _, fila in self.contactos.lista_contactos.iterrows():
                self.listbox_contactos.insert(tk.END, f"{fila['Nombre']} ({fila['ID']})")
    
    def agregar_contacto_manual(self):
        """Permite agregar un contacto manualmente"""
        dialog = tk.Toplevel(self.frame)
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

        print(nombre)
        
        # Obtener ID del contacto
        id_envio = self.contactos.elegir_contacto(nombre)
        if id_envio is None:
            messagebox.showerror("Error", "No se pudo obtener el ID del contacto")
            return
        
        print(id_envio)

        try:
            if "!" in id_envio:
                id_envio = int(id_envio.replace("!", ""), 16)
                self.sender.send_message(id_envio, mensaje)
            else:
                id_envio = int(id_envio)
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