# MqttCliente.py
from src.MqttDispositivo import MqttDispositivo
from src.MqttEnvio import MqttEnvio
from src.MqttRecibo import MqttRecibo
from meshtastic import BROADCAST_NUM
from src.Interfaz import Interfaz
from src.GUI_refactorizado import GUI
from src.GUI.Pest_dron import Pest_dron
import tkinter as tk
import time

class main:
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
        self.interface = Interfaz(connector=self.connector, receiver=self.receiver, sender=self.sender)
        
        self.retrys = 0

    def run(self):
        """ Se conecta y se espera hasta estar preparado para iniciar la interfaz GUI """
        # Esperar a que esté conectado
        while not self.connector.is_connected():
            print("Esperando conexión al broker MQTT...")
            self.retrys += 1
            if self.retrys > 5:
                print("No se pudo conectar al broker MQTT")
                opt = input("Quieres abrir la interfaz del dron? (0/1) \n")
                if opt == "1":
                    root = tk.Tk()
                    gui = GUI(
                            root,
                            connector=self.connector,
                            receiver=self.receiver,
                            sender=self.sender,
                            contactos=self.interface.contacto,
                            onlydron=True
                        )
                    root.mainloop()
                elif opt != "1":
                    exit()
                return
            time.sleep(1)
        
        print("Conectado al broker MQTT")
        
        root = tk.Tk()
        gui = GUI(
            root,
            connector=self.connector,
            receiver=self.receiver,
            sender=self.sender,
            contactos=self.interface.contacto,
            onlydron=False
        )
        root.mainloop()

if __name__ == "__main__":
    client = main()
    client.run()