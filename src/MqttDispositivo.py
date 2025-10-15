# MqttDispositivo.py
from meshtastic.protobuf import mesh_pb2, mqtt_pb2, portnums_pb2
import paho.mqtt.client as mqtt
import random
import time
import ssl
import base64

class MqttDispositivo:
    """Clase responsable de la conexión y configuración MQTT"""

    def __init__(self):
        # Topics base que SIEMPRE queremos suscribir
        self.BASE_TOPICS = ["sensor/data/sen55", "sensor/data/gas_sensor"]
        self.TOPICS = []
        
        # Debug Options
        self.debug = True
        self.auto_reconnect = True
        self.auto_reconnect_delay = 1  # seconds

        # MQTT Settings
        self.mqtt_broker = "mqtt.meshtastic.org"
        self.meshtastic_broker = "mqtt.meshtastic.org"
        self.mqttS_broker = "broker.emqx.io"
        self.mqtt_port = 1883
        self.mqtt_username = "meshdev"
        self.mqtt_password = "large4cats"
        self.message_text = "Soy un PC de Aitor"

        # Meshtastic Settings
        self.root_topic = "msh/EU_868/ES/2/e/"
        self.channel = "TestMQTT"
        self.key = "ymACgCy9Tdb8jHbLxUxZ/4ADX+BWLOGVihmKHcHTVyo="

        # Node Configuration
        self.random_hex_chars = ''.join(random.choices('0123456789abcdef', k=4))

        with open ("Datos/node_name.txt", "r+") as f:
            nombre = f.read()
            if not nombre:
                self.node_name = '!abcd' + self.random_hex_chars
                f.write(self.node_name)
            else:
                self.node_name = nombre
        
        self.node_number = int(self.node_name.replace("!", ""), 16)
        print("Nombre, Numero")
        print(self.node_name)
        print(self.node_number)
        self.client_short_name = "ALP"
        self.client_long_name = "Aitor_PC" + self.random_hex_chars
        self.lat = "0"
        self.lon = "0"
        self.alt = "0"
        self.client_hw_model = 255

        # Topics
        self.subscribe_topic = ""
        self.publish_topic = ""

        # MQTT Client
        self.client = None
        self.tls_configured = False

    def set_topic(self):
        if self.debug:
            print("set_topic")
        
        # Reiniciar TOPICS con los topics base
        self.TOPICS = self.BASE_TOPICS.copy()
        
        # Solo añadir topic de Meshtastic si estamos en ese broker
        if self.mqtt_broker == self.meshtastic_broker:
            node_name = '!' + hex(self.node_number)[2:]
            self.subscribe_topic = self.root_topic + self.channel + "/#"
            self.TOPICS.append(self.subscribe_topic)
            self.publish_topic = self.root_topic + self.channel + "/" + node_name
            if self.debug:
                print(f"Topics de Meshtastic añadidos: {self.subscribe_topic}")
        else:
            if self.debug:
                print("Broker externo detectado, solo topics de sensores")

    def xor_hash(self, data):
        result = 0
        for char in data:
            result ^= char
        return result

    def generate_hash(self, name, key):
        replaced_key = key.replace('-', '+').replace('_', '/')
        key_bytes = base64.b64decode(replaced_key.encode('utf-8'))
        h_name = self.xor_hash(bytes(name, 'utf-8'))
        h_key = self.xor_hash(key_bytes)
        result = h_name ^ h_key
        return result

    def create_client_and_callbacks(self, on_message_callback=None):
        """Crea el cliente MQTT y asigna callbacks (pero no hace connect)."""
        if self.client is None:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="", clean_session=True, userdata=None)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            if on_message_callback:
                self.client.on_message = on_message_callback

    def connect_mqtt(self):
        """Conecta al broker MQTT"""
        if self.debug:
            print(f"connect_mqtt a broker: {self.mqtt_broker}")

        self.create_client_and_callbacks()

        try:
            # Soporte para broker:port
            if ':' in self.mqtt_broker:
                broker, port = self.mqtt_broker.split(':', 1)
                self.mqtt_broker = broker
                try:
                    self.mqtt_port = int(port)
                except ValueError:
                    pass

            # Procesar clave por defecto
            if self.key == "AQ==":
                if self.debug:
                    print("key is default, expanding to AES128")
                self.key = "1PG7OiApB1nwvP+rz05pAQ=="

            # Normalizar clave
            padded_key = self.key.ljust(len(self.key) + ((4 - (len(self.key) % 4)) % 4), '=')
            replaced_key = padded_key.replace('-', '+').replace('_', '/')
            self.key = replaced_key

            # Configurar autenticación
            self.client.username_pw_set(self.mqtt_username, self.mqtt_password)

            # Configurar TLS si es necesario
            if self.mqtt_port == 8883 and not self.tls_configured:
                self.client.tls_set(ca_certs="cacert.pem", tls_version=ssl.PROTOCOL_TLSv1_2)
                self.client.tls_insecure_set(False)
                self.tls_configured = True

            # connect + start loop
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_start()

        except Exception as e:
            print("connect_mqtt exception:", e)

    def disconnect_mqtt(self):
        if self.debug:
            print("disconnect_mqtt")
        if self.client is not None and self.client.is_connected():
            self.client.disconnect()

    def is_connected(self):
        return self.client is not None and self.client.is_connected()

    def get_client(self):
        return self.client

    def _on_connect(self, client, userdata, properties, reason_code, flags):
        """Callback interno para conexión"""
        if self.debug:
            print(f"_on_connect called with rc={reason_code}")
        
        try:
            # Configurar topics según el broker actual
            self.set_topic()
            
            if reason_code == 0:
                if self.debug:
                    print(f"Connected to server: {self.mqtt_broker}")
                    print(f"Topics a suscribir: {self.TOPICS}")
                    if self.mqtt_broker == self.meshtastic_broker:
                        print(f"Publish Topic is: {self.publish_topic}")
                
                # Suscribirse a todos los topics configurados
                for topic in self.TOPICS:
                    result = self.client.subscribe(topic)
                    if self.debug:
                        print(f"Suscrito al tema '{topic}'")
            else:
                print(f"Conexión fallida con código: {reason_code}")
                
        except Exception as e:
            print("_on_connect exception:", e)

    def _on_disconnect(self, client, userdata, flags, rc, properties):
        """Callback interno para desconexión"""
        if self.debug:
            print("on_disconnect rc=", rc)
        if rc != 0:
            if self.auto_reconnect:
                print("attempting to reconnect in " + str(self.auto_reconnect_delay) + " second(s)")
                time.sleep(self.auto_reconnect_delay)
                try:
                    self.connect_mqtt()
                except Exception as e:
                    print("reconnect failed:", e)