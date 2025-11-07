# Pest_dron.py
import tkinter as tk
from tkinter import ttk, messagebox
from djitellopy import tello
import time
import cv2
import PIL.Image, PIL.ImageTk
import threading

class Pest_dron:
    """Pestaña para control del dron Tello dentro de un Notebook de Tkinter.
       Control por flechas + teclas auxiliares. Muestra vídeo en la pestaña.
    """

    def __init__(self, notebook, receiver=None):
        # notebook: el ttk.Notebook donde agregar la pestaña
        self.notebook = notebook
        self.receiver = receiver

        # Estado de movimiento
        self.lr = 0    # left/right
        self.fb = 0    # forward/back
        self.ud = 0    # up/down
        self.yv = 0    # yaw (rotación)
        self.speed = 20
        self.liftSpeed = 20
        self.moveSpeed = 35
        self.rotationSpeed = 40

        # Drone
        self.drone = None
        self.streaming = False
        self.frame_image = None  # PhotoImage para tkinter

        # Crear UI
        self._crear_pestana_ui()

        # Intentar conectar al dron (no bloqueante)
        threading.Thread(target=self._conectar_dron, daemon=True).start()

    def _crear_pestana_ui(self):
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="Control Dron")

        # Canvas / Label para vídeo
        self.video_label = tk.Label(self.frame, text="Vídeo no disponible", width=80, height=24, bd=2, relief=tk.SUNKEN)
        self.video_label.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky='nsew')

        # Panel de controles
        btn_takeoff = ttk.Button(self.frame, text="Takeoff (E)", command=self._cmd_takeoff)
        btn_land = ttk.Button(self.frame, text="Land (Q)", command=self._cmd_land)
        btn_snap = ttk.Button(self.frame, text="Snapshot (Z)", command=self._cmd_snapshot)
        btn_battery = ttk.Button(self.frame, text="Bateria", command=self._mostrar_bateria)

        btn_takeoff.grid(row=1, column=0, padx=4, pady=4, sticky='ew')
        btn_land.grid(row=1, column=1, padx=4, pady=4, sticky='ew')
        btn_snap.grid(row=1, column=2, padx=4, pady=4, sticky='ew')
        btn_battery.grid(row=1, column=3, padx=4, pady=4, sticky='ew')

        # Etiqueta de estado
        self.estado_label = tk.Label(self.frame, text="Estado: Desconectado")
        self.estado_label.grid(row=2, column=0, columnspan=4, sticky='w', padx=8)

        # Configurar grid para que el vídeo crezca
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure((0,1,2,3), weight=1)

        # Atajos de teclado: binds en la frame
        # Para recibir eventos de teclado, pedimos foco en el frame
        self.frame.bind_all('<KeyPress>', self._on_key_press)
        self.frame.bind_all('<KeyRelease>', self._on_key_release)

        # Llamada periódica para enviar controles y actualizar vídeo
        self._update_loop()

        # Cuando la pestaña sea eliminada / app cerrada -> limpiar
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _conectar_dron(self):
        try:
            self.drone = tello.Tello()
            self.drone.connect()
            # start video stream
            self.drone.streamon()
            self.streaming = True
            self.estado_label.config(text=f"Estado: Conectado (IP: {self.drone.get_current_state().get('ip','?') if hasattr(self.drone, 'get_current_state') else ''})")
        except Exception as e:
            self.streaming = False
            self.estado_label.config(text=f"Estado: Error conexión: {e}")

    # ---------- Comandos botones ----------
    def _cmd_takeoff(self):
        try:
            if self.drone:
                self.drone.takeoff()
        except Exception as e:
            messagebox.showerror("Takeoff", f"Error al despegar: {e}")

    def _cmd_land(self):
        try:
            if self.drone:
                self.drone.land()
        except Exception as e:
            messagebox.showerror("Land", f"Error al aterrizar: {e}")

    def _cmd_snapshot(self):
        try:
            if self.drone and self.streaming:
                frame = self._get_frame_from_drone()
                if frame is not None:
                    filename = f"snapshot_{int(time.time())}.jpg"
                    cv2.imwrite(filename, frame)
                    messagebox.showinfo("Snapshot", f"Guardado como {filename}")
                else:
                    messagebox.showwarning("Snapshot", "Frame no disponible")
        except Exception as e:
            messagebox.showerror("Snapshot", f"Error al hacer snapshot: {e}")

    def _mostrar_bateria(self):
        try:
            if self.drone:
                bat = self.drone.get_battery()
                messagebox.showinfo("Batería", f"{bat}%")
        except Exception as e:
            messagebox.showerror("Batería", f"Error al leer batería: {e}")

    # ---------- Teclado (press / release) ----------
    def _on_key_press(self, event):
        k = event.keysym
        # flechas
        if k == "Left":
            self.lr = -self.speed
        elif k == "Right":
            self.lr = self.speed
        elif k == "Up":
            self.fb = self.moveSpeed
        elif k == "Down":
            self.fb = -self.moveSpeed
        # subida/bajada
        elif k.lower() == "w":
            self.ud = self.liftSpeed
        elif k.lower() == "s":
            self.ud = -self.liftSpeed
        # rotación
        elif k.lower() == "d":
            self.yv = self.rotationSpeed
        elif k.lower() == "a":
            self.yv = -self.rotationSpeed
        # takeoff / land shortcuts
        elif k.lower() == "e":
            self._cmd_takeoff()
        elif k.lower() == "q":
            self._cmd_land()
        # snapshot
        elif k.lower() == "z":
            self._cmd_snapshot()

    def _on_key_release(self, event):
        k = event.keysym
        if k in ("Left", "Right"):
            self.lr = 0
        if k in ("Up", "Down"):
            self.fb = 0
        if k.lower() in ("w", "s"):
            self.ud = 0
        if k.lower() in ("a", "d"):
            self.yv = 0

    # ---------- Vídeo ----------
    def _get_frame_from_drone(self):
        try:
            if not self.drone or not self.streaming:
                return None
            frame = self.drone.get_frame_read().frame
            return frame
        except Exception:
            return None

    def _update_loop(self):
        """
        Llamada periódica para:
         - enviar comando rc al dron
         - obtener frame y actualizar imagen en la UI
        """
        # Enviar controles
        try:
            if self.drone:
                # send_rc_control espera (lr, fb, ud, yaw)
                self.drone.send_rc_control(self.lr, self.fb, self.ud, self.yv)
        except Exception:
            # no forzar excepción si falla momentáneamente
            pass

        # Actualizar frame vídeo
        try:
            frame = self._get_frame_from_drone()
            if frame is not None:
                # Convertir BGR (cv2) a RGB (PIL)
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # ajustar tamaño para la etiqueta (opcional). Aquí lo escalamos a 640x480 manteniendo ratio
                h, w = img_rgb.shape[:2]
                max_w, max_h = 640, 480
                scale = min(max_w / w, max_h / h, 1.0)
                new_w, new_h = int(w * scale), int(h * scale)
                pil_img = PIL.Image.fromarray(img_rgb).resize((new_w, new_h))
                self.frame_image = PIL.ImageTk.PhotoImage(pil_img)
                self.video_label.config(image=self.frame_image, text='')
            else:
                # si no hay frame, mantener texto
                if not self.frame_image:
                    self.video_label.config(text="Vídeo no disponible")
        except Exception:
            pass

        # Repetir cada 60 ms (~16 FPS)
        self.frame.after(60, self._update_loop)

    # ---------- Manejo cierre / cambio de pestaña ----------
    def _on_tab_changed(self, event):
        # Si la pestaña actual ya no es la nuestra, nada especial; 
        # si tu app necesita detectar cierre de pestaña, podría añadirse acá.
        pass

    def close(self):
        # Llamar cuando cierres la app para limpiar
        try:
            if self.drone:
                try:
                    self.drone.streamoff()
                except Exception:
                    pass
                try:
                    self.drone.end()
                except Exception:
                    pass
        except Exception:
            pass

# Si quieres usarlo como Toplevel directamente (opcional):
class Pest_dron_Toplevel(tk.Toplevel, Pest_dron):
    def __init__(self, parent, receiver=None):
        tk.Toplevel.__init__(self, parent)
        Pest_dron.__init__(self, self)  # esto es útil solo si quieres un toplevel como notebook
