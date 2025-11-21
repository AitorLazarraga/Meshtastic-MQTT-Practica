import time
import serial

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

def req_serial(func):
    """Decorador para funciones que requieren conexión serial"""
    def wrapper(self, *args, **kwargs):
        # Verificar si hay un receptor serial disponible
        if not hasattr(self, 'serial_receiver') or self.serial_receiver is None:
            print("No hay receptor serial configurado")
            return None
        
        if not self.serial_receiver.is_connected():
            print("Puerto serial no conectado. Intentando conectar...")
            if not self.serial_receiver.conectar():
                print("✗ No se pudo conectar al puerto serial")
                return None
            time.sleep(1)
        
        return func(self, *args, **kwargs)
    return wrapper