import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import os
import platform
import subprocess


class PestanaImagenes:
    """Pestaña para visualizar imágenes recibidas"""
    
    def __init__(self, notebook, receiver):
        self.notebook = notebook
        self.receiver = receiver
        
        # Variables de control
        self.imagen_actual = None
        self.imagenes_recibidas = []
        
        # Crear frame principal
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Imágenes")
        
        self._crear_interfaz()
        self._iniciar_actualizacion()
    
    def _crear_interfaz(self):
        """Crea la interfaz de la pestaña"""
        # Frame superior con lista de imágenes
        frame_lista = ttk.LabelFrame(self.frame, text="Imágenes Recibidas", padding=10)
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
        frame_progreso = ttk.Frame(self.frame)
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

        self.label_idimg = tk.Label(frame_progreso, text=f"{self.receiver.id_actual}")
        self.label_idimg.pack(side="bottom", padx=3)
        
        # Frame para visualizar imagen
        frame_visor = ttk.LabelFrame(self.frame, text="Vista Previa", padding=10)
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
    
    def _iniciar_actualizacion(self):
        """Inicia la actualización automática de imágenes y progreso"""
        self._actualizar_imagenes_recibidas()
        self._actualizar_progreso_imagen()
    
    def _actualizar_imagenes_recibidas(self):
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
            
            self.frame.after(2000, verificar_imagenes)
        
        verificar_imagenes()
    
    def _actualizar_progreso_imagen(self):
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
            
            # Actualizar ID de imagen actual
            if hasattr(self.receiver, 'id_actual'):
                self.label_idimg.config(text=f"{self.receiver.id_actual}")
            
            self.frame.after(500, verificar_progreso)
        
        verificar_progreso()
    
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
            if platform.system() == 'Windows':
                os.startfile(ruta_imagen)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', ruta_imagen])
            else:  # Linux
                subprocess.call(['xdg-open', ruta_imagen])
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir imagen: {str(e)}")