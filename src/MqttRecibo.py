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
from src.ProcesarMensajes import ProcesarPosicion, ProcesarTexto, ProcesarTelemetria

class MqttRecibo:
    """Clase responsable de recibir y procesar mensajes"""
    
    def __init__(self, connector):

        self.connector = connector
        self.debug = connector.debug
        self.contactos = Contactos()

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
        self.rutapag = "Datos/PaginasAmarillas.csv"

        self.texto = ProcesarTexto(self)
        self.posicion = ProcesarPosicion(self)
        self.telemetria = ProcesarTelemetria(self)
        


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
                #self._procesar_posicion(mp)
                self.posicion.procesar_mensaje(mp)

            elif portnum in [portnums_pb2.PortNum.NODEINFO_APP, portnums_pb2.PortNum.TELEMETRY_APP]:
                #self._procesar_telemetria(mp)
                self.telemetria.procesar_mensaje(mp)

            elif portnum == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
                #.contactos.anadir_contacto(getattr(mp,"from"))
                #self._procesar_texto(mp)
                self.texto.procesar_mensaje(mp)


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

    
