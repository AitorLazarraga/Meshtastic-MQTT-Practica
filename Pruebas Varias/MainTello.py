import pygame as pg
from djitellopy import tello
import time
import PruebaKeyword as kp
import cv2

class MainTello:
    def __init__(self):
        self.image = ''
        self.lr, self.fb, self.ud, self.yv = 0,0,0,0
        self.speed = 20 
        self.liftSpeed = 20
        self.moveSpeed = 35
        self.rotationSpeed = 40
        kp.init()
        self.drone = tello.Tello()
        self.drone.connect()
        self.drone.streamon()

    
    def getKeyboardInput(self):
        
        self.lr, self.fb, self.ud, self.yv = 0,0,0,0
        if kp.getKey("LEFT"): self.lr = -self.speed #Controlling The Left And Right Movement
        elif kp.getKey("RIGHT"): self.lr = self.speed

        if kp.getKey("UP"): self.fb = self.moveSpeed #Controlling The Front And Back Movement
        elif kp.getKey("DOWN"): self.fb = -self.moveSpeed

        if kp.getKey("w"): self.ud = self.liftSpeed #Controlling The Up And Down Movemnt:
        elif kp.getKey("s"): self.ud = -self.liftSpeed 

        if kp.getKey("d"): self.yv = self.rotationSpeed #Controlling the Rotation:
        elif kp.getKey("a"): self.yv = -self.rotationSpeed 

        if kp.getKey("q"): self.drone.land(); time.sleep(3) #Landing The Drone
        elif kp.getKey("e"): self.drone.takeoff() #Take Off The Drone

        if kp.getKey("z"): #Screen Shot Image From The Camera Display
            cv2.imwrite(f"Datos/Imagenes/{time.time()}.jpg", self.img)
            time.sleep(0.3)

        if kp.getKey('b'):
            print(f"Bateria: {self.drone.get_battery()}%")
            time.sleep(0.3)

        return [self.lr, self.fb, self.ud, self.yv]

    def run(self):
        keyValues = self.getKeyboardInput()
        self.drone.send_rc_control(keyValues[0], keyValues[1], keyValues[2], keyValues[3])
        self.img = self.drone.get_frame_read().frame
        self.image = cv2.resize(self.img, (1080,720))
        cv2.imshow("Drone", self.image)
        cv2.waitKey(1)

if __name__ == "__main__":
    dron = MainTello()
    while True:
        dron.run()
        