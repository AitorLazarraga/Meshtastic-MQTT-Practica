import time

class ConDron:
    def __init__(self, pest_dron=None):
        self.pest_dron = pest_dron

    def set_pestana(self, pest_dron):
        """Permite conectar o reconectar la pestaña del dron."""
        self.pest_dron = pest_dron

    def despegar(self):
        self.pest_dron._cmd_takeoff()
        
    def aterrizar(self):
        self.pest_dron._cmd_land()

    def adelante(self, time_sec=3):
        self.pest_dron.fb = self.pest_dron.moveSpeed
        time.sleep(time_sec)
        self.pest_dron.fb = 0

    def atras(self, time_sec=3):
        self.pest_dron.fb = -self.pest_dron.moveSpeed
        time.sleep(time_sec)
        self.pest_dron.fb = 0

    def mov_izda(self, time_sec=1):
        self.pest_dron.lr = -self.pest_dron.speed
        time.sleep(time_sec)
        self.pest_dron.lr = 0

    def mov_dcha(self, time_sec=1):
        self.pest_dron.lr = self.pest_dron.speed
        time.sleep(time_sec)
        self.pest_dron.fb = 0
    
    def rotar(self, time_sec=1):
        self.pest_dron.yv = self.pest_dron.rotationSpeed
        time.sleep(time_sec)
        self.pest_dron.yv = 0

    def subir(self, time_sec=0.5):
        self.pest_dron.ud = self.pest_dron.liftSpeed
        time.sleep(time_sec)
        self.pest_dron.ud = 0
    
    def bajar(self, time_sec=0.5):
        self.pest_dron.ud = -self.pest_dron.liftSpeed
        time.sleep(time_sec)
        self.pest_dron.ud = 0
    
    def img(self):
        self.pest_dron._cmd_snapshot()

