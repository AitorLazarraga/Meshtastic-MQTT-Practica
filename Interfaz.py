from MqttDispositivo import MqttDispositivo
from MqttEnvio import MqttEnvio
from meshtastic import BROADCAST_NUM
from MqttRecibo import MqttRecibo
import time

class Interfaz:
    def __init__(self, connector=None, receiver=None, sender=None):
        self.sel = 0
        self.mensaje = ""
        self.opciones = {1: "Enviar Mensaje",2: "Enviar Info Nodo", 3: "Enviar Position" ,4: "Ver Mensajes",5:"Cambiar Broker" ,6: "Salir"}
        
        # Usar instancias pasadas en lugar de crear nuevas
        if connector is None:
            self.connector = MqttDispositivo()
            self.connector.create_client_and_callbacks()
            self.connector.connect_mqtt()
            self.receiver = MqttRecibo(self.connector)
            self.sender = MqttEnvio(self.connector)
        else:
            self.connector = connector
            self.receiver = receiver
            self.sender = sender

        print("Interfaz creada")
        
    def mostrar_menu(self): 
        if self.connector.mqtt_broker == "mqtt.meshtastic.org" :
            print("Seleccione una opción:")
            for key, value in self.opciones.items():
                print(f"{key}. {value}")
        else:
            print("Pulse el 0 para cambiar a broker Meshtastic")
            try:
                num = int(input())
                if num == 0:
                    self.seleccionar_opcion(5)
            except ValueError:
                print("Opción no válida")
                return
                
    def seleccionar_opcion(self, opcion):
        if opcion in self.opciones:
            self.sel = opcion
            print(f"Opción seleccionada: {self.opciones[opcion]}")
        else:
            print("Opción no válida")
        match self.sel:
            case 1:
                print("Quieres enviar el mensaje predeterminado o crear uno nuevo?")
                print("1. Mensaje predeterminado")
                print("2. Crear nuevo mensaje")
                try:
                    opcion_mensaje = int(input("Seleccione una opción: "))
                except ValueError:
                    print("Opción no válida")
                    return
                match opcion_mensaje:
                    case 1:
                        self.mensaje = self.connector.message_text
                        if self.connector.is_connected():
                            self.sender.send_message(BROADCAST_NUM, self.mensaje)
                        else:
                            print("No estamos ready")
                            self.connector.connect_mqtt()
                    case 2:
                        self.mensaje = input("Escribe tu mensaje: ")
                        if self.connector.is_connected():
                            self.sender.send_message(BROADCAST_NUM, self.mensaje)
                        else:
                            print("No estamos ready")
                            self.connector.connect_mqtt()
                    case _:
                        print("Opción no válida")
            case 2:
                print("Enviando Info Nodo...")
                self.sender.send_node_info(BROADCAST_NUM, want_response=False)
            case 3:
                print("Enviando Position...")
                self.sender.send_position(BROADCAST_NUM)
            case 4:
                print("Mostrando mensajes recibidos...")
                self.receiver.mostrar_mensajes()
            case 5:
                if self.connector.mqtt_broker == self.connector.meshtastic_broker:
                    print("Cambiando a broker EMQX")
                    self.connector.mqtt_broker = self.connector.mqttS_broker
                    self.connector.disconnect_mqtt()
                    time.sleep(2)
                    # Limpiar topics de Meshtastic antes de reconectar
                    self.connector.subscribe_topic = ""
                    self.connector.publish_topic = ""
                    self.connector.connect_mqtt()
                else:
                    print("Cambiando a broker Meshtastic")
                    self.connector.mqtt_broker = self.connector.meshtastic_broker
                    self.connector.disconnect_mqtt()
                    time.sleep(2)
                    self.connector.subscribe_topic = ""
                    self.connector.publish_topic = ""
                    self.connector.connect_mqtt()
                print(f"Broker actual: {self.connector.mqtt_broker}")
            case 6:
                print("Saliendo...")
                self.connector.disconnect_mqtt()
                exit()
            case _:
                print("Opción no válida")
   
    def run(self):
        while True:
            self.mostrar_menu()
            if self.connector.mqtt_broker == self.connector.meshtastic_broker:
                try:
                    opcion = int(input("Seleccione una opción: "))
                    self.seleccionar_opcion(opcion)
                except ValueError:
                    print("Opción no válida")