from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
from meshtastic import protocols
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

class MqttRecibo:
    """Clase responsable de recibir y procesar mensajes"""
    
    def __init__(self, connector):
        self.connector = connector
        self.debug = connector.debug
        
        # Opciones de impresi�n
        self.print_service_envelope = False
        self.print_message_packet = False
        self.print_node_info = True
        self.print_node_position = True
        self.print_node_telemetry = True


    def on_message(self, client, userdata, msg):
        """Procesa mensajes recibidos"""
        se = mqtt_pb2.ServiceEnvelope()
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
        print("Soy la payload que hay que guardar")

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