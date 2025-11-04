from typing import Protocol
import random

class Sensor(Protocol):
    def get_data() -> float:
        ...
    
    def get_type() -> str:
        ...

class TempSens():
    def __init__(self):
        self.nom = "Sensor Temperatura"

    def get_data(self) -> float:
        return float(random.randint(0,1000))
    
    def get_type(self) -> str:
        return "C"
    
class AguaSens():
    def get_data(self) -> float:
        return float(random.randint(0,1000))
    
    def get_type(self) -> str:
        return "g/m³"
    
class VelSens():
    def get_data(self) -> float:
        return float(random.randint(0,1000))
    
    def get_type(self) -> str:
        return "m/s"
    
def datos_sens(sensor : Sensor) -> None:
    valor = sensor.get_data()
    tipo = sensor.get_type()
    self.
    print(f"Se ha obtenido {valor} {tipo} del sensor {nomsens}")

temperatura = TempSens
velocidad = VelSens
agua = AguaSens

datos_sens(temperatura)
print(" ")
datos_sens(velocidad)
print(" ")
datos_sens(agua)