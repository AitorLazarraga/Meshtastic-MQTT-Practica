import pygame

def init():
    """Inicializa pygame y crea una ventana para capturar las teclas"""
    pygame.init()
    global win
    win = pygame.display.set_mode((400, 400))
    pygame.display.set_caption("Control Tello - Teclado")

def getKey(keyName):
    """Devuelve True si la tecla indicada está presionada"""
    ans = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

    keyInput = pygame.key.get_pressed()
    myKey = getattr(pygame, f'K_{keyName}')
    if keyInput[myKey]:
        ans = True
    return ans

def main():
    """Solo para prueba manual"""
    print("Presiona teclas (ESC para salir)")
    while True:
        if getKey("LEFT"):
            print("Izquierda")
        if getKey("RIGHT"):
            print("Derecha")
        if getKey("UP"):
            print("Arriba")
        if getKey("DOWN"):
            print("Abajo")
        if getKey("escape"):
            print("Saliendo...")
            break

if __name__ == '__main__':
    init()
    main()
