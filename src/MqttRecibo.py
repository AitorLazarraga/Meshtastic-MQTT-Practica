from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import protocols
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import json
import re
import base64
import pandas as pd

class MqttRecibo:
    """Clase responsable de recibir y procesar mensajes"""
    
    def __init__(self, connector):
        self.connector = connector
        self.debug = connector.debug
        self.mensajes = {}
        self.posiciones = []
        self.gpsDF = pd.DataFrame(columns=['lat', 'lon', 'alt'])
        self.n_mensaje = 0
        # Opciones de impresi�n
        self.print_service_envelope = False
        self.print_message_packet = False
        self.print_node_info = True
        self.print_node_position = True
        self.print_node_telemetry = True
        self.csv_file = 'posiciones.csv'

    def ParseText(self,payload_str):
        matches = re.findall(r'(\w+):\s*([-\w.]+)', payload_str)
        data = {}
        for k, v in matches:
            if v.lstrip('-').isdigit():
                data[k] = int(v)
            else:
                data[k] = v
        return data

    def on_message(self, client, userdata, msg):
        """Procesa mensajes recibidos"""
        se = mqtt_pb2.ServiceEnvelope()
        if msg.topic == 'sensor/data/sen55' or msg.topic == 'sensor/data/gas_sensor':
            print(f"Mensaje obtenido en el topico: {msg.topic}")
            print(msg.payload.decode("utf-8"))
            
            if msg.topic == 'sensor/data/sen55':
                try:
                    # Decodificar y convertir el mensaje de JSON a diccionario
                    payload = json.loads(msg.payload.decode("utf-8"))
                    print(json.dumps(payload, indent=4))  # Mostrar el mensaje formateado
                    df = pd.DataFrame([payload])
                    df.to_csv('WaterSensor.csv', mode='a', header=not os.path.exists('sensor_data.csv'), index=False)
                except json.JSONDecodeError as e:
                    print(f"Error decodificando JSON: {e}")
            
            if msg.topic == 'sensor/data/gas_sensor':
                try:
                    # Decodificar y convertir el mensaje de JSON a diccionario
                    payload = json.loads(msg.payload.decode("utf-8"))
                    print(json.dumps(payload, indent=4))  # Mostrar el mensaje formateado
                    df = pd.DataFrame([payload])
                    df.to_csv('GasSensor_data.csv', mode='a', header=not os.path.exists('sensor_data.csv'), index=False)
                except json.JSONDecodeError as e:
                    print(f"Error decodificando JSON: {e}")

            
        else:
            try:
                se.ParseFromString(msg.payload)
                if self.print_service_envelope:
                    print("")
                    print("Service Envelope:")
                    print(se)
                mp = se.packet
                if self.print_message_packet:
                    print("")
                    print("Message Packet:")
                    print(mp)
            except Exception as e:
                print(f"*** ServiceEnvelope: {str(e)}")
                return

            if mp.HasField("encrypted") and not mp.HasField("decoded"):
                self._decode_encrypted(mp)

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
            
            
            print(mp)
            if mp.HasField("decoded"):
                if mp.decoded.portnum == portnums_pb2.PortNum.POSITION_APP:
                    pb = mp.decoded.payload
                    pb = pb.decode('utf-8')
                    print(f"Soy un debug del payload de posiciones {pb}")
                    pb_dict = self.ParseText(pb)

                    lat = pb_dict.get("latitude_i",0)
                    lon = pb_dict.get("longitude_i",0) 
                    alt = pb_dict.get("altitude_i",0)

                    self.posiciones.append([lat,lon,alt])

                    nueva_posicion = pd.DataFrame([[lat, lon, alt]], columns=['lat', 'lon', 'alt'])
                    print(f"Guardando nueva posicion en csv {lat,lon,alt}")
                    nueva_posicion.to_csv(
                        self.csv_file, 
                        mode='a',  # Modo append
                        header=not os.path.exists(self.csv_file),  # Header solo si es nuevo
                        index=False
                    )
                else:   
                    self.n_mensaje += 1
                    if self.n_mensaje % 10 == 0:
                        print("Guardando mensajes en csv")

                        mensajes_df = pd.DataFrame.from_dict(self.mensajes, orient='index', mode = 'a')
                        mensajes_df.to_csv('mensajes.csv', index=False)
                        self.mensajes.clear()

                        print("Se han guardado los mensajes y limpiado el diccionario")
                    if mp.decoded.portnum == portnums_pb2.PortNum.NODEINFO_APP or mp.decoded.portnum == portnums_pb2.PortNum.TELEMETRY_APP:
                        pb = mp.decoded.payload
                        pb = pb.decode('utf-8')
                        pb_dict = self.ParseText(pb)
                        pb_dict["Hora"] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        self.mensajes[self.n_mensaje] = pb_dict
                    if mp.decoded.portnum == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
                        pb = mp.decoded.payload
                        pb = pb.decode('utf-8')
                        pb = "Hora" + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + " " + pb
                        self.mensajes[self.n_mensaje] = pb
                    print(f"Mensaje {self.n_mensaje} guardado")

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

    
