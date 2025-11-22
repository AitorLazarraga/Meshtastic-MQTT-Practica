import time

class ConDron:
    def __init__(self, pest_dron=None):
        self.pest_dron = pest_dron

    def set_pestana(self, pest_dron):
        """Permite conectar o reconectar la pestaña del dron."""
        self.pest_dron = pest_dron

    def despegar(self):
        print("PROBANDOS")
        self.pest_dron._cmd_takeoff()
        
    def aterrizar(self):
        self.pest_dron._cmd_land()

    def adelante(self, time_sec=1):
        self.pest_dron.fb = self.pest_dron.moveSpeed
        time.sleep(1)
        self.pest_dron.fb = 0

    def atras(self, time_sec=1):
        self.pest_dron.fb = -self.pest_dron.moveSpeed
        time.sleep(1)
        self.pest_dron.fb = 0

    def mov_izda(self, time_sec=1):
        self.pest_dron.lr = -self.pest_dron.speed
        time.sleep(1)
        self.pest_dron.lr = 0

    def mov_dcha(self, time_sec=1):
        self.pest_dron.lr = self.pest_dron.speed
        time.sleep(1)
        self.pest_dron.fb = 0

    def img(self):
        self.pest_dron._cmd_snapshot()

