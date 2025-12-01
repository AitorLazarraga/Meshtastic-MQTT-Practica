from abc import ABC, abstractmethod
import pandas as pd
import os

class ProcesarMensajes(ABC):
    def __init__(self, receiver_instance):
        """
        Args:
            receiver_instance: Instancia de MqttRecibo que contiene todos los recursos necesarios
        """
        self.receiver = receiver_instance
        self.mensajes = {}
        self.posiciones = []
        self.flag_imagen = False
        self.ultimo_mensaje = None
        self.nuevos_mensajes = []
        self.n_mensaje = 0

    @abstractmethod
    def procesar_mensaje(self, mensaje):
        pass

    @abstractmethod
    def guardar_csv(self, datos):
        pass


class LogMixin:
    def log(self, tipo, payload):
        print(f"Ha llegado un mensaje del tipo {tipo}")
        print(f"La payload es {payload}")

class ProcesarPosicion(ProcesarMensajes, LogMixin):
    
    def procesar_mensaje(self, mensaje):
        """Procesa mensajes de posición"""
        pb = mensaje.decoded.payload.decode('utf-8')
        pb_dict = self.receiver.ParseText(pb)
        print(f"POSICIONESPB {pb_dict}")

        lat = pb_dict.get("latitude_i", 0)
        lon = pb_dict.get("longitude_i", 0)
        
        if pb_dict.get("altitude", "NAN") != "NAN":
            alt = pb_dict.get("altitude", 0)
        else:
            alt = pb_dict.get("altitude_hae", 0)
        
        print(f"Latitude === {lat}")
        print(f"Longitude == {lon}")
        print(f"Altitude === {alt}")

        self.posiciones.append([lat, lon, alt])
        ultima_posicion = (lat, lon, alt)
        self.guardar_csv(ultima_posicion)

        try:
            nom = self.receiver.contactos.contactoNum(getattr(mensaje, 'from'))
        except:
            nom = str(getattr(mensaje, 'from'))
        
        self.n_mensaje += 1
        mensaje_pos = f"Hora {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - Posición recibida de {nom}: Lat: {lat}, Lon: {lon}, Alt: {alt}m"
        self.log('Posicional', mensaje_pos)
        self.mensajes[self.n_mensaje] = mensaje_pos
        self.ultimo_mensaje = mensaje_pos
        self.nuevos_mensajes.append(mensaje_pos)

        if hasattr(self.receiver, 'gui_callback'):
            self.receiver.gui_callback()

    def guardar_csv(self, datos):
        lat, lon, alt = datos[0], datos[1], datos[2]
        print(f"Guardando nueva posición en csv: {(lat, lon, alt)}")
        
        nueva_posicion = pd.DataFrame([[lat, lon, alt]], columns=['lat', 'lon', 'alt'])
        nueva_posicion.to_csv(
            self.receiver.csv_filePos,
            mode='a',
            header=not os.path.exists(self.receiver.csv_filePos),
            index=False
        )


class ProcesarTelemetria(ProcesarMensajes, LogMixin):
    
    def procesar_mensaje(self, mensaje):
        """Procesa mensajes de telemetría o nodeinfo"""
        self.n_mensaje += 1
        pb = mensaje.decoded.payload.decode('utf-8')
        pb_dict = self.receiver.ParseText(pb)
        
        self.receiver.contactos.anadir_contacto(
            pb_dict.get('id', "NAN"), 
            pb_dict.get('long_name', None)
        )
        pb_dict["Hora"] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Mensaje de telemetría recibido. Payload: {pb_dict}")

        self.mensajes[self.n_mensaje] = pb_dict
        self.ultimo_mensaje = f"Mensaje de Telemetría recibido de {pb_dict.get('long_name', '¿?')}"
        self.nuevos_mensajes.append(pb_dict)
        self.log('Telemetrico', pb_dict)
        
        if self.n_mensaje % 10 == 0:
            self.guardar_csv(self.mensajes)
            self.mensajes.clear()
    
    def guardar_csv(self, datos):
        print("Guardando mensajes en CSV")
        df = pd.DataFrame.from_dict(datos, orient='index')
        df.to_csv(
            self.receiver.csv_fileM,
            index=False,
            mode='a',
            header=not os.path.exists(self.receiver.csv_fileM)
        )
        print("Mensajes guardados y diccionario limpiado")


class ProcesarTexto(ProcesarMensajes, LogMixin):
    
    def __init__(self, receiver_instance):
        super().__init__(receiver_instance)
        self.partes_imagen = []
        self.id_actual = None
        self.partes_esperadas = 0
    
    def procesar_mensaje(self, mensaje):
        """Procesa mensajes de texto (incluye imágenes fragmentadas)"""
        pb = mensaje.decoded.payload.decode('utf-8')
        pb_dict = self.receiver.ParseText(pb)

        # Inicio de imagen
        if pb_dict.get("Estado", None) == "INICIO_IMAGEN" and not self.flag_imagen:
            print("Inicio de recepción de imagen")
            self.flag_imagen = True
            self.partes_imagen = []
            self.id_actual = pb_dict.get("ID")
            self.partes_esperadas = pb_dict.get("Total_parts")
            self.partes_imagen.append(pb_dict)
            self.log('Imagen', pb_dict)

            self.receiver.flag_imagen = True
            self.receiver.partes_imagen = self.partes_imagen
            self.receiver.partes_esperadas = self.partes_esperadas
            self.receiver.id_actual = self.id_actual
            return
        
        # Partes de imagen
        if self.flag_imagen and pb_dict.get("id") == self.id_actual:
            self.partes_imagen.append(pb_dict)
            print(f"Parte {pb_dict.get('part', '?')} de {self.partes_esperadas} recibida")
            
            # CORRECCIÓN: Sincronizar con receiver
            self.receiver.partes_imagen = self.partes_imagen
            return

        # Fin de imagen
        if pb_dict.get("Estado") == "FIN_IMAGEN" and self.flag_imagen:
            print(f"Mensaje de fin de imagen recibido. Total partes: {len(self.partes_imagen)}")
            self.receiver.Encoder.reconstruir_imagen(self)
            
            # CORRECCIÓN: Limpiar también en receiver
            self.receiver.flag_imagen = False
            self.receiver.partes_imagen = []
            self.receiver.partes_esperadas = 0
            self.receiver.id_actual = None
            return

        # Mensaje normal de texto
        self.n_mensaje += 1
        persona = getattr(mensaje, 'from')
        nombreper = self.receiver.contactos.contactoNum(persona)
        
        if not nombreper:
            nombreper = "¿?"
        nombreper = str(nombreper)
        
        if nombreper == " Yo_Mismo_Mismito":
            return

        pb_con_hora = f"Hora {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} {pb} recibido de {nombreper}"
        self.log('Texto', pb_con_hora)
        self.mensajes[self.n_mensaje] = pb_con_hora
        self.ultimo_mensaje = pb_con_hora
        self.nuevos_mensajes.append(pb_con_hora)

        print(f"{pb_con_hora}")
        
        if self.n_mensaje % 10 == 0:
            self.guardar_csv(self.mensajes)
            self.mensajes.clear()

    def guardar_csv(self, datos):
        print("Guardando mensajes en CSV")
        df = pd.DataFrame.from_dict(datos, orient='index')
        df.to_csv(
            self.receiver.csv_fileM,
            index=False,
            mode='a',
            header=not os.path.exists(self.receiver.csv_fileM)
        )
        print("Mensajes guardados y diccionario limpiado")