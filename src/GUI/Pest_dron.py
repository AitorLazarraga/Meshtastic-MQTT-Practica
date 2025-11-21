# Pest_dron.py
import tkinter as tk
from tkinter import ttk, messagebox
from djitellopy import tello
import time
import cv2
import numpy as np
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

        self.gesture_thread = None
        self.last_processed_frame = None


        # Estado de movimiento
        self.lr = 0    # left/right
        self.fb = 0    # forward/back
        self.ud = 0    # up/down
        self.yv = 0    # yaw (rotación)
        self.speed = 20
        self.liftSpeed = 20
        self.moveSpeed = 35
        self.rotationSpeed = 40

        self.min_azul = np.array([100,100,20])
        self.max_azul = np.array([125,255,255])

        # Drone
        self.drone = None
        self.streaming = False
        self.frame_image = None  # PhotoImage para tkinter

        self.gesture_control = False  # Flag para activar gestos
        self.gesture_cooldown = 0     # Contador de cooldown
        self.finger_count = 0

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

        btn_gestures = ttk.Button(self.frame, text="Gestos OFF", command=self._toggle_gestures)
        btn_gestures.grid(row=1, column=4, padx=4, pady=4, sticky='ew')
        self.btn_gestures = btn_gestures

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

    def _gesture_loop(self):
        while self.gesture_control:
            if self.last_processed_frame is not None:
                processed = self._process_gestures(self.last_processed_frame.copy())
                self.last_processed_frame = processed
            time.sleep(0.02)  # 20 ms → 50 FPS máx


    def _toggle_gestures(self):
        self.gesture_control = not self.gesture_control
        
        if self.gesture_control:
            self.btn_gestures.config(text="Gestos ON")
            # iniciar hilo si no existe
            self.gesture_thread = threading.Thread(
                target=self._gesture_loop, daemon=True
            )
            self.gesture_thread.start()
        else:
            self.btn_gestures.config(text="Gestos OFF")


    def _count_fingers(self, contour):
        """Cuenta dedos usando convex hull y convexity defects"""
        hull = cv2.convexHull(contour, returnPoints=False)

        if len(hull) > 3:
            defects = cv2.convexityDefects(contour, hull)
            if defects is not None:
                fingers = 0

                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]

                    start = contour[s][0]
                    end   = contour[e][0]
                    far   = contour[f][0]

                    # Convertir a arrays
                    start = np.array(start)
                    end   = np.array(end)
                    far   = np.array(far)

                    # Lados del triángulo
                    a = np.linalg.norm(end - start)
                    b = np.linalg.norm(far - start)
                    c = np.linalg.norm(end - far)

                    # Evitar división por cero
                    if a == 0 or b == 0 or c == 0:
                        continue

                    # Ley de cosenos
                    angle = np.arccos((b*b + c*c - a*a) / (2 * b * c))

                    # Ángulo típico entre dedos <= 90º y profundidad grande
                    if angle <= np.pi / 2 and d > 5000:
                        fingers += 1

                return fingers + 1

        return 0

    
    def _process_gestures(self, frame):
        if not self.gesture_control:
            return frame
        
        h, w = frame.shape[:2]
        roi_size = 200
        
        # ROI real (esquina superior derecha)
        h, w = frame.shape[:2]
        roi_size = 200
        x1, y1 = w - roi_size - 10, 10
        x2, y2 = w - 10, 10 + roi_size

        roi = frame[y1:y2, x1:x2]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)


        # Convertir a HSV y máscara de piel
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Rango amplio de piel para iluminación variable
        lower_skin = np.array([0, 20, 50])
        upper_skin = np.array([25, 255, 255])

        mask = cv2.inRange(hsv, lower_skin, upper_skin)

        # Ruido
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # Contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            hand = max(contours, key=cv2.contourArea)

            if cv2.contourArea(hand) > 2000:
                # Dibujar contorno en ROI
                cv2.drawContours(roi, [hand], -1, (255, 0, 0), 2)

                # Convex hull y defectos
                hull = cv2.convexHull(hand, returnPoints=False)

                if hull is not None and len(hull) > 3:
                    defects = cv2.convexityDefects(hand, hull)
                    fingers = 0

                    if defects is not None:
                        for i in range(defects.shape[0]):
                            s, e, f, depth = defects[i, 0]
                            start = tuple(hand[s][0])
                            end   = tuple(hand[e][0])
                            far   = tuple(hand[f][0])

                            # Dibujar puntos
                            cv2.circle(roi, far, 5, (0, 0, 255), -1)
                            cv2.circle(roi, start, 5, (255, 0, 255), -1)

                    # Mostrar conteo
                    cv2.putText(frame, f"Dedos: {fingers+1}", 
                                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                                1, (0, 255, 0), 2)

                    self.finger_count = fingers + 1
        
        return frame
    
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
                print("Ha despegado")
                #self.drone.takeoff()
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
                    filename = f"Datos/Imagenes/dron_snapshot_{int(time.time())}.jpg"
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
            frame_corregido = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame_corregido
        except Exception:
            return None

    def _update_loop(self):
        """
        Llamada periódica para:
        - enviar comando rc al dron
        - obtener frame y actualizar imagen en la UI
        - procesar gestos si está activado
        """
        # Enviar controles
        try:
            if self.drone:
                self.drone.send_rc_control(self.lr, self.fb, self.ud, self.yv)
        except Exception:
            pass

        # Actualizar frame vídeo
        try:
            frame = self._get_frame_from_drone()
            if frame is not None:

                # Enviar frame al hilo de gestos
                if self.gesture_control:
                    self.last_processed_frame = frame.copy()
                    if self.last_processed_frame is not None:
                        frame = self.last_processed_frame

                # Convertir y mostrar en tkinter
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = img_rgb.shape[:2]
                max_w, max_h = 640, 480
                scale = min(max_w / w, max_h / h, 1.0)
                new_w, new_h = int(w * scale), int(h * scale)
                pil_img = PIL.Image.fromarray(img_rgb).resize((new_w, new_h))
                self.frame_image = PIL.ImageTk.PhotoImage(pil_img)
                self.video_label.config(image=self.frame_image, text='')
            else:
                if not self.frame_image:
                    self.video_label.config(text="Vídeo no disponible")
        except Exception:
            pass

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
