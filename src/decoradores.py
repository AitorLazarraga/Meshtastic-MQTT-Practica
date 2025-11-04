import time

def req_conexion(func):
    def wrapper(self,*args, **kwargs):
        if not self.connector.is_connected():
            print("No hay conexión establecida. Reconectando...")
            self.connector.connect_mqtt()
            time.sleep(2)
        else:
            print("Funciona")
            return func(self, *args, **kwargs)
    return wrapper