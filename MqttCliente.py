# MqttCliente.py
from MqttDispositivo import MqttDispositivo
from MqttEnvio import MqttEnvio
from MqttRecibo import MqttRecibo
from meshtastic import BROADCAST_NUM
import time

class MeshtasticMQTTClient:
    def __init__(self):
        # crea el dispositivo primero (pero no hace connect a�n)
        self.connector = MqttDispositivo()

        # crea receiver y p�salo como callback de on_message antes de conectar
        self.receiver = MqttRecibo(self.connector)
        # ensure the client object exists and has callbacks set (and on_message assigned)
        self.connector.create_client_and_callbacks(on_message_callback=self.receiver.on_message)

        # ahora crea sender (usa connector.client que ya existe)
        self.sender = MqttEnvio(self.connector)

        # finalmente conecta
        self.connector.connect_mqtt()

    def run(self):
        try:
            while True:
                if self.connector.is_connected():
                    print("Tamos ready")
                    time.sleep(10)
                    '''# 1. Node Info
                    self.sender.send_node_info(BROADCAST_NUM, want_response=False)
                    time.sleep(4)

                    # 2. Position
                    self.sender.send_position(BROADCAST_NUM)
                    time.sleep(4)

                    # 3. Texto
                    self.sender.send_message(BROADCAST_NUM, self.connector.message_text)
                    time.sleep(10)  # espera antes de repetir ciclo'''
                else:
                    print("No estamos ready")
                    time.sleep(2)
        except KeyboardInterrupt:
            if self.connector.debug:
                print("Interrupted, disconnecting...")
            self.connector.disconnect_mqtt()


if __name__ == "__main__":
    client = MeshtasticMQTTClient()
    client.run()
