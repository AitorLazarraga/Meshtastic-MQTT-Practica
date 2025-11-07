import random
from abc import abstractmethod, ABC

class SensorError(Exception):
    def __init__(self, message):
        super().__init__(message)
    
class Sensor(ABC):
    @abstractmethod
    def read_value(self):
        pass

class TemSens(Sensor):
    def read_value(self, valor):
        try:
            if valor in range(15,76):
                print(f"La temperatura obtenida es {valor} Cº")
            else:
                raise SensorError("Fallo de lectura de sensor de temperatura")
        except SensorError:
            print(f"Valor {valor} no valido, omitiendo temp")

class PressSens(Sensor):
    def read_value(self, valor):
        try:
            if valor in range(1,11):
                print(f"La Presion obtenida es {valor} Atm")
            else:
                raise SensorError("Fallo de lectura de sensor de presión")
        except SensorError:
            print(f"Valor {valor} no valido, omitiendo pres")

temp_sens = TemSens()
press_sens = PressSens()

for i in range (0,10):
    valorT = random.randint(0,100)
    valorP = random.randint(0,20)
    temp_sens.read_value(valorT)
    press_sens.read_value(valorP)


        
