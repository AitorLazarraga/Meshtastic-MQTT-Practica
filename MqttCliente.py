# MqttCliente.py
from src.MqttDispositivo import MqttDispositivo
from src.MqttEnvio import MqttEnvio
from src.MqttRecibo import MqttRecibo
from meshtastic import BROADCAST_NUM
from src.Interfaz import Interfaz
import time

class MqttCliente:
    def __init__(self):
        # Crear el dispositivo primero (pero no conectar aún)
        self.connector = MqttDispositivo()

        # Crear receiver y pasarlo como callback de on_message antes de conectar
        self.receiver = MqttRecibo(self.connector)
        
        # Asegurar que el objeto client existe y tiene callbacks configurados
        self.connector.create_client_and_callbacks(on_message_callback=self.receiver.on_message)

        # Crear sender (usa connector.client que ya existe)
        self.sender = MqttEnvio(self.connector)

        # Finalmente conectar
        self.connector.connect_mqtt()

        # Pasar las instancias a Interfaz para que use las mismas
        self.interface = Interfaz(
            connector=self.connector,
            receiver=self.receiver,
            sender=self.sender
        )

    def run(self):
        while True:
            if self.connector.is_connected():
                print("Conectado al broker MQTT")
                self.interface.run()
            else:
                print("Conexion fallida, reintentando en 3 segundos")
                time.sleep(3)

if __name__ == "__main__":
    client = MqttCliente()
    client.run()