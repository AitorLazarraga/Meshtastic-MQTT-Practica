from calendar import c
from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import random
import re
import time
from src.decoradores import req_conexion

class MqttEnvio:
    """Clase responsable de enviar mensajes y datos"""
    
    def __init__(self, connector):
        self.connector = connector
        self.cliente = connector.client
        self.global_message_id = random.getrandbits(32)
        self.debug = connector.debug

    @req_conexion
    def send_message(self, destination_id, message_text):
        """Envia un mensaje de texto"""
        if not self.cliente.is_connected():
            self.connector.connect_mqtt()

        if message_text:
            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.TEXT_MESSAGE_APP
            encoded_message.payload = message_text.encode("utf-8")
            self._generate_mesh_packet(destination_id, encoded_message)

    def direct_message(self, destination_id, message_text=None):
        """Env�a un mensaje directo a un nodo espec�fico"""
        if self.debug:
            print("direct_message")
        if destination_id:
            try:
                destination_id = int(destination_id[1:], 16)
                message = message_text or self.connector.message_text
                self.send_message(destination_id, message)
            except Exception as e:
                if self.debug:
                    print(f"Error converting destination_id: {e}")

    def send_traceroute(self, destination_id):
        """Env�a un paquete de traceroute"""
        if not self.connector.client.is_connected():
            self.connector.connect_mqtt()
        if self.debug:
            print(f"Sending Traceroute Packet to {str(destination_id)}")

        encoded_message = mesh_pb2.Data()
        encoded_message.portnum = portnums_pb2.TRACEROUTE_APP
        encoded_message.want_response = True

        destination_id = int(destination_id[1:], 16)
        self._generate_mesh_packet(destination_id, encoded_message)

    @req_conexion
    def send_node_info(self, destination_id, want_response):
        """Env�a informaci�n del nodo"""
        if self.cliente.is_connected():
            user_payload = mesh_pb2.User()
            setattr(user_payload, "id", self.connector.node_name)
            setattr(user_payload, "long_name", self.connector.client_long_name)
            setattr(user_payload, "short_name", self.connector.client_short_name)
            setattr(user_payload, "hw_model", self.connector.client_hw_model)

            user_payload = user_payload.SerializeToString()
            #print(f"Soy un debug de nodo {user_payload}")

            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.NODEINFO_APP
            encoded_message.payload = user_payload
            encoded_message.want_response = want_response
            self._generate_mesh_packet(destination_id, encoded_message)

    @req_conexion
    def send_position(self, destination_id):
        """Env�a informaci�n de posici�n"""
        if self.cliente.is_connected():
            pos_time = int(time.time())
            latitude = int(float(self.connector.lat) * 1e7)
            longitude = int(float(self.connector.lon) * 1e7)
            altitude_units = 1 / 3.28084 if 'ft' in str(self.connector.alt) else 1.0
            altitude = int(altitude_units * float(re.sub('[^0-9.]', '', str(self.connector.alt))))

            position_payload = mesh_pb2.Position()
            setattr(position_payload, "latitude_i", latitude)
            setattr(position_payload, "longitude_i", longitude)
            setattr(position_payload, "altitude", altitude)
            setattr(position_payload, "time", pos_time)

            position_payload = position_payload.SerializeToString()
            #print(f"Soy un debug de posicin {position_payload}")

            encoded_message = mesh_pb2.Data()
            encoded_message.portnum = portnums_pb2.POSITION_APP
            encoded_message.payload = position_payload
            encoded_message.want_response = True

            self._generate_mesh_packet(destination_id, encoded_message)

    def send_ack(self, destination_id, message_id):
        """Env�a un acknowledgment"""
        if self.debug:
            print("Sending ACK")
        encoded_message = mesh_pb2.Data()
        encoded_message.portnum = portnums_pb2.ROUTING_APP
        encoded_message.request_id = message_id
        encoded_message.payload = b"\030\000"
        self._generate_mesh_packet(destination_id, encoded_message)

    @req_conexion
    def send_img(self, destination_id, parts, total_parts, image_id, tipo_imagen):
        """Envia una imagen fragmentada"""
        if self.debug:
            print("Enviando imagen con datos")
            print(f"ID:{image_id}, Total Parts:{total_parts}, Tipo:{tipo_imagen}")

        #Mensaje Cabecera    
        message_text = f"Estado:INICIO_IMAGEN, ID:{image_id}, Total_parts:{total_parts}, Format:{tipo_imagen}"
        self.send_message(destination_id, message_text)
        time.sleep(5)

        #Envio Partes
        for part in parts:
            message_text = ','.join(f"{k}:{v}" for k, v in part.items())
            self.send_message(destination_id, message_text)
            time.sleep(5)  # Pequeña pausa entre envíos para evitar saturación

        #Mensaje Finalizador
        message_text = f"Estado:FIN_IMAGEN, ID:{image_id}, Total_parts:{total_parts}, Format:{tipo_imagen}"
        if self.debug:
            print("Enviando fin de imagen")
            
        self.send_message(destination_id, message_text)

    def _generate_mesh_packet(self, destination_id, encoded_message):
        """Genera y env�a un paquete mesh"""
        mesh_packet = mesh_pb2.MeshPacket()

        # Usar el ID global de mensaje e incrementarlo
        mesh_packet.id = self.global_message_id
        self.global_message_id += 1

        setattr(mesh_packet, "from", self.connector.node_number)
        mesh_packet.to = destination_id
        mesh_packet.want_ack = False
        mesh_packet.channel = self.connector.generate_hash(self.connector.channel, self.connector.key)
        mesh_packet.hop_limit = 3

        if self.connector.key == "":
            mesh_packet.decoded.CopyFrom(encoded_message)
        else:
            mesh_packet.encrypted = self._encrypt_message(self.connector.channel, self.connector.key, mesh_packet, encoded_message)

        service_envelope = mqtt_pb2.ServiceEnvelope()
        service_envelope.packet.CopyFrom(mesh_packet)
        service_envelope.channel_id = self.connector.channel
        service_envelope.gateway_id = self.connector.node_name

        payload = service_envelope.SerializeToString()
        self.cliente.publish(self.connector.publish_topic, payload)

    def _encrypt_message(self, channel, key, mesh_packet, encoded_message):
        """Encripta un mensaje"""
        mesh_packet.channel = self.connector.generate_hash(channel, key)
        key_bytes = base64.b64decode(key.encode('ascii'))
        nonce_packet_id = mesh_packet.id.to_bytes(8, "little")
        nonce_from_node = self.connector.node_number.to_bytes(8, "little")
        nonce = nonce_packet_id + nonce_from_node
        cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_bytes = encryptor.update(encoded_message.SerializeToString()) + encryptor.finalize()
        return encrypted_bytes