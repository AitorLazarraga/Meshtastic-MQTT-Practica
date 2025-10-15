from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import protocols
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import json
import re
import base64
import pandas as pd
from pathlib import Path
from src.ImageEncoder import ImageEncoder
from src.Contactos import Contactos

class MqttRecibo:
    """Clase responsable de recibir y procesar mensajes"""
    
    def __init__(self, connector):

        self.connector = connector
        self.debug = connector.debug
        self.contactos = Contactos()

        self.mensajes = {}
        self.posiciones = []
        self.flag_imagen = False

        self.gpsDF = pd.DataFrame(columns=['lat', 'lon', 'alt'])
        self.n_mensaje = 0
        self.partes_imagen = []
        self.id_actual = None
        self.partes_esperadas = 0
        # Opciones de impresi�n
        self.print_service_envelope = False
        self.print_message_packet = False
        self.print_node_info = True
        self.print_node_position = True
        self.print_node_telemetry = True
        self.Encoder = ImageEncoder()

        self.csv_filePos = "Datos/posiciones.csv"
        self.csv_fileM = "Datos/mensajes.csv"
        self.csv_fileGas = "Datos/GasSensor_data.csv"
        self.csv_fileSen = "Datos/WaterSensor.csv"


    def ParseText(self,payload_str):
        """Funcion de parseo de string a diccionario python"""
        #Se ha cambiado la expresion regular para aceptar caracteres en base64 para las payloads de imagen
        matches = re.findall(r"(\w+):\s*([^,\s]+(?:\s(?!\w+:)[^,\s]+)*)", payload_str) #re.findall(r"(\w+):\s*([^,\s])")
    
        data = {}
        for k, v in matches:
            v = v.strip()
            try:
                data[k] = int(v)
            except ValueError:
                try:
                    data[k] = float(v)
                except ValueError:
                    data[k] = v
        return data

    def procesar_sensores(self, msg):
        """Al llegar un mensaje del topico sensor emqx se leen, se decodifican y se guardan en el csv que toque"""
        print(f"Mensaje obtenido en el topico: {msg.topic}")
        print(msg.payload.decode("utf-8"))
            
        if msg.topic == 'sensor/data/sen55':
            try:
                # Decodificar y convertir el mensaje de JSON a diccionario
                payload = json.loads(msg.payload.decode("utf-8"))
                print(json.dumps(payload, indent=4))  # Mostrar el mensaje formateado
                df = pd.DataFrame([payload])
                df.to_csv(self.csv_fileSen, mode='a', header=not os.path.exists(self.csv_fileSen), index=False)
            except json.JSONDecodeError as e:
                print(f"Error decodificando JSON: {e}")
            
        if msg.topic == 'sensor/data/gas_sensor':
            try:
                # Decodificar y convertir el mensaje de JSON a diccionario
                payload = json.loads(msg.payload.decode("utf-8"))
                print(json.dumps(payload, indent=4))  # Mostrar el mensaje formateado
                df = pd.DataFrame([payload])
                df.to_csv(self.csv_fileGas, mode='a', header=not os.path.exists(self.csv_fileGas), index=False)
            except json.JSONDecodeError as e:
                print(f"Error decodificando JSON: {e}")
   
    def procesar_mensaje(self, msg):
        """Si llega un mensaje que no sea de sensores se decodifica el paquete mesh y luego se trabaja dependiendo su port"""
        se = mqtt_pb2.ServiceEnvelope()
        try:
            se.ParseFromString(msg.payload)
        except Exception as e:
            print(f"*** Error parseando ServiceEnvelope: {str(e)}")
            return
        
        if self.print_service_envelope:
            print("\nService Envelope:\n", se)
        
        mp = se.packet
        if self.print_message_packet:
            print("\nMessage Packet:\n", mp)
        
        if mp.HasField("encrypted") and not mp.HasField("decoded"):
            self._decode_encrypted(mp)
            print(f"Mensaje mp {mp}")
            
            # Intentar procesar el payload desencriptado
            portNumInt = mp.decoded.portnum if mp.HasField("decoded") else None
            handler = protocols.get(portNumInt) if portNumInt else None

            pb = None
            if handler is not None and handler.protobufFactory is not None:
                pb = handler.protobufFactory()
                try:
                    pb.ParseFromString(mp.decoded.payload)
                except Exception:
                    # payload puede no ser protobuf para este handler
                    pb = None

            if pb:
                # Limpiar y actualizar el payload
                pb_str = str(pb).replace('\n', ' ').replace('\r', ' ').strip()
                mp.decoded.payload = pb_str.encode("utf-8")

        if mp.HasField('decoded'):
            portnum = mp.decoded.portnum
            
            if portnum == portnums_pb2.PortNum.POSITION_APP:
                #self.contactos.anadir_contacto(getattr(mp,"from"))
                self._procesar_posicion(mp)

            elif portnum in [portnums_pb2.PortNum.NODEINFO_APP, portnums_pb2.PortNum.TELEMETRY_APP]:
                self._procesar_telemetria(mp)

            elif portnum == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
                #.contactos.anadir_contacto(getattr(mp,"from"))
                self._procesar_texto(mp)

    def _procesar_posicion(self, mp):
        """Procesa mensajes de posición GPS"""
        pb = mp.decoded.payload.decode('utf-8')
        pb_dict = self.ParseText(pb)
        print(f"POSICIONESPB {pb_dict}")

        lat = pb_dict.get("latitude_i", 0)
        lon = pb_dict.get("longitude_i", 0)
        if pb_dict.get("altitude", "NAN") != "NAN":
            alt = pb_dict.get("altitude",0)
        else:
            alt = pb_dict.get("altitude_hae", 0) 
        
        print(f"Latitude === {lat}")
        print(f"Longitude == {lon}")
        print(f"Altitude === {alt}")


        self.posiciones.append([lat, lon, alt])
        print(f"Guardando nueva posición en csv: {(lat, lon, alt)}")
        
        nueva_posicion = pd.DataFrame([[lat, lon, alt]], columns=['lat', 'lon', 'alt'])
        nueva_posicion.to_csv(
            self.csv_filePos,
            mode='a',
            header=not os.path.exists(self.csv_filePos),
            index=False
        )

    def _procesar_telemetria(self, mp):
        """Procesa mensajes de telemetría o nodeinfo"""
        self.n_mensaje += 1
        pb = mp.decoded.payload
        pb = pb.decode('utf-8')
        pb_dict = self.ParseText(pb)
        self.contactos.anadir_contacto(pb_dict.get('id',"NAN"), pb_dict.get('long_name', None))
        pb_dict["Hora"] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Mensaje de telemtria recibido. Payload: {pb_dict}")

        self.mensajes[self.n_mensaje] = pb_dict
        
        if self.n_mensaje % 10 == 0:
            print("Guardando mensajes en CSV")
            df = pd.DataFrame.from_dict(self.mensajes, orient='index')
            df.to_csv(
                self.csv_fileM,
                index=False,
                mode='a',
                header=not os.path.exists(self.csv_fileM)
            )
            self.mensajes.clear()
            print("Mensajes guardados y diccionario limpiado")

    def _procesar_texto(self, mp):
        """Procesa mensajes de texto (incluye imágenes fragmentadas)"""
        pb = mp.decoded.payload
        pb = pb.decode('utf-8')
        pb_dict = self.ParseText(pb)

        # Inicio de imagen
        if pb_dict.get("Estado", None) == "INICIO_IMAGEN" and not self.flag_imagen:
            print("Inicio de recepción de imagen")
            self.flag_imagen = True
            self.partes_imagen = []
            self.id_actual = pb_dict.get("ID")
            self.partes_esperadas = pb_dict.get("Total_parts")
            self.partes_imagen.append(pb_dict)
            return
        
        # Partes de imagen
        if self.flag_imagen and pb_dict.get("id") == self.id_actual:
            self.partes_imagen.append(pb_dict)
            print(f"Parte guardada: {pb_dict}")
            return

        # Fin de imagen
        if pb_dict.get("Estado") == "FIN_IMAGEN" and self.flag_imagen:
            self._reconstruir_imagen()
            return

        # Mensaje normal de texto
        self.n_mensaje += 1
        pb_con_hora = "Hora" + " " + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + " " + pb
        self.mensajes[self.n_mensaje] = pb_con_hora
        print(f"Mensaje: {pb_con_hora}")
        print(f"Mensaje {self.n_mensaje} guardado")
        
        #Al tener 10 o más mensajes se guardan y se borra el diccionario
        if self.n_mensaje % 10 == 0:
            print("Guardando mensajes en CSV")
            df = pd.DataFrame.from_dict(self.mensajes, orient='index')
            df.to_csv(
                self.csv_fileM,
                index=False,
                mode='a',
                header=not os.path.exists(self.csv_fileM)
            )
            self.mensajes.clear()
            print("Mensajes guardados y diccionario limpiado")

    def _reconstruir_imagen(self):
        """Reconstruye una imagen recibida por partes"""
        
        print("Fin de recepción de imagen")
        id_imagen = self.partes_imagen[0]['ID']
        tipo_imagen = self.partes_imagen[0]['Format']
        del self.partes_imagen[0]
        
        if len(self.partes_imagen) == self.partes_esperadas:
            print("Todas las partes recibidas correctamente")
            self.flag_imagen = False
            self.partes_imagen.sort(key=lambda x: x['part'])
            cadena_completa = ''.join([p['data'] for p in self.partes_imagen if 'data' in p])
            ruta_salida = f"Datos/Imagenes/imagen_recibida_{id_imagen}.{tipo_imagen}"
            print(f"Guardando imagen recibida como {ruta_salida}")
            self.Encoder.cadena_a_imagen(cadena_completa, ruta_salida)

        else:
            print(f"Faltan partes de la imagen. Esperadas: {self.partes_esperadas}, Recibidas: {len(self.partes_imagen)}")
            print(f"Partes recibidas: {self.partes_imagen}")
        
        self.flag_imagen = False
        self.partes_imagen = []


    def on_message(self, client, userdata, msg):
        """Procesa mensajes recibidos"""
        if msg.topic in ['sensor/data/sen55', 'sensor/data/gas_sensor']:
            self.procesar_sensores(msg)
        else:
            self.procesar_mensaje(msg)

    def _decode_encrypted(self, mp):
        """Desencripta un mensaje"""
        try:
            key_bytes = base64.b64decode(self.connector.key.encode('ascii'))
            nonce_packet_id = getattr(mp, "id").to_bytes(8, "little")
            nonce_from_node = getattr(mp, "from").to_bytes(8, "little")
            nonce = nonce_packet_id + nonce_from_node
            cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_bytes = decryptor.update(getattr(mp, "encrypted")) + decryptor.finalize()
            data = mesh_pb2.Data()
            data.ParseFromString(decrypted_bytes)
            mp.decoded.CopyFrom(data)
        except Exception as e:
            if self.print_message_packet:
                print(f"failed to decrypt: \n{mp}")
            if self.debug:
                print(f"*** Decryption failed: {str(e)}")
            return
    
    def mostrar_mensajes(self):
        """Muestra todos los mensajes guardados"""
        print("Mostrando mensajes recibidos...")
        print("Se mostrarán los últimos 10 mensajes recibidos")
        
        if not self.mensajes:
            print("No hay mensajes guardados aún.")
            return
        
        for key in sorted(self.mensajes.keys()):
            print(f"{key}: {self.mensajes[key]}")
            print("--------------------------------------")

    
