from src.MqttDispositivo import MqttDispositivo
from src.MqttEnvio import MqttEnvio
from meshtastic import BROADCAST_NUM
from src.MqttRecibo import MqttRecibo
from src.ImageEncoder import ImageEncoder
import time
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from src.Contactos import Contactos
from src.GUI import GUI

class Interfaz:
    def __init__(self, connector, receiver, sender):
        self.sel = 0
        self.mensaje = ""
        self.opciones = {1: "Enviar Mensaje",2: "Enviar Info Nodo", 3: "Enviar Position" ,4: "Ver Mensajes",5:"Cambiar Broker" ,6:"Enviar Posiciones", 7: "Salir"}

        self.lista_coordenadas = []

        self.Encoder = ImageEncoder()
        self.contacto = Contactos()      

        if not connector or not receiver or not sender:
            """En caso de haber iniciado la interfaz sin estar conectado o sin instanciar objetos se reconecta de forma forzada"""
            self.connector = MqttDispositivo()
            self.connector.create_client_and_callbacks()
            self.connector.connect_mqtt()
            self.receiver = MqttRecibo(self.connector)
            self.sender = MqttEnvio(self.connector)

        else:
            self.connector = connector
            self.receiver = receiver
            self.sender = sender

    def mostrar_menu(self): 
        """Muestra el menu e impide realizar acciónes en modo mqtt"""
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
        """ Recoge la opción del usuario y trabaja en respecto """
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
                print("3. Enviar Imagen")
                print("4. Enviar mensaje directo")
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
                    case 3:
                        """Se usa tkinter para seleccion de archivo de imagen"""
                        root = tk.Tk()
                        root.withdraw()

                        # Abrir el explorador de archivos
                        foto = filedialog.askopenfilename(
                            title="Selecciona una Imagen para Enviar",
                            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")]
                        )
                        
                        nombre = Path(foto)
                        FotoEnvio = foto
                        id_imagen = nombre.stem
                        
                        cadena64, tipo_imagen = self.Encoder.imagen_a_cadena(FotoEnvio) #Se obtiene la cadena de la imagen y su formato
                        partes_imagen, cantidad_paquetes = self.Encoder.fragmentar_payload(cadena64, id_imagen) #Se obtienen los paquetes a enviar

                        print("1.Envio General \n 2.Envio Privado")
                        opcion = int(input())
                        match opcion:
                            case 1:
                                if self.connector.is_connected():
                                    self.sender.send_img(BROADCAST_NUM, partes_imagen, cantidad_paquetes, id_imagen, tipo_imagen)
                            case 2:
                                self.contacto.mostrar_contactos()
                                nombre = input("A quien quieres enviarle la imagen\n")
                                id_envio = self.contacto.elegir_contacto(nombre)
                                try:
                                    id_envio = int(id_envio.replace("!", ""), 16)
                                except ValueError:
                                    print("Fallo de id")
                                if id_envio == None:
                                    print("Contacto no encontrado")
                                    return
                                if self.connector.is_connected():
                                    self.sender.send_img(id_envio, partes_imagen, cantidad_paquetes, id_imagen, tipo_imagen)
                            case _:
                                return
                    case 4:
                        """Se manda un mensaje directo a un contacto de la agenda"""
                        self.contacto.mostrar_contactos()
                        print("Elige a que contacto enviar un mensaje")
                        nombre = input("Nombre del contacto a enviar \n")
                        self.mensaje = input("Escribe mensaje a enviar")
                        id_envio = self.contacto.elegir_contacto(nombre)
                        try:
                            id_envio = int(id_envio.replace("!", ""), 16)
                        except ValueError:
                            print("Fallo de id")
                        if id_envio == None:
                            print("Contacto no encontrado")
                            return
                        print(f"Enviando mensaje {self.mensaje} a id {id_envio}")
                        self.sender.send_message(id_envio, self.mensaje)
                    
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
                """Opcion de cambio de broker
                Para mayor sencillez se usan 3 strings, dos constantes de los brokers y el que se usa para conexiones"""
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
                    #Limpiar topis antes de reconectar
                    self.connector.subscribe_topic = ""
                    self.connector.publish_topic = ""
                    self.connector.connect_mqtt()
                print(f"Broker actual: {self.connector.mqtt_broker}")
            case 6:
                print("Enviar coordenadas")
                print("Ingresa los datos de coordenadas, si Z = 0 se contará como que vas a enviar datos bidimensionales")
                flagZ = True
                while True:
                    x = input("Ingrese dato para X")
                    y = input("Ingrese dato para Y")
                    if flagZ == True:
                        z = input("Ingrese dato para Z")
                        try:
                            if float(z) == 0.0:
                                flagZ = False
                                z = None
                            else:
                                z = float(z)
                        except ValueError:
                            print("Dato no valido")
                    else:
                        z = None
                    try:
                        x = float(x)
                        y = float(y)
                    except ValueError:
                        print("Datos no validos")
                    
                    if z is not None:
                        dict_cords = {"X": x, "Y": y, "Z": z}
                    else:
                        dict_cords = {"X": x, "Y": y}

                    self.lista_coordenadas.append(dict_cords)
                    try:
                        opcion = int(input("Pulsa 0 para enviar coordenadas, cualquier otra cosa para añadir mas"))
                        if opcion == 0:
                            self.mensaje = str(self.lista_coordenadas)
                            self.sender.send_message(BROADCAST_NUM, self.mensaje)
                            return
                        else:
                            raise ValueError
                    except ValueError:
                        print("Añadiendo otra cordenada")
            case 7:
                print("Saliendo...")
                self.connector.disconnect_mqtt()
                exit()
            case _:
                print("Opción no válida")

    def run_gui(self):
        """Inicia la interfaz gráfica"""
        root = tk.Tk()
        gui = GUI(
            root,
            connector=self.connector,
            receiver=self.receiver,
            sender=self.sender,
            contactos=self.contacto
        )
        root.mainloop()
   
    def run(self):
        """Se muestra el menu y se espera a la entrada de usuario"""
        while True:
            self.mostrar_menu()
            if self.connector.mqtt_broker == self.connector.meshtastic_broker:
                try:
                    opcion = int(input("Seleccione una opción: "))
                    self.seleccionar_opcion(opcion)
                except ValueError:
                    print("Opción no válida")