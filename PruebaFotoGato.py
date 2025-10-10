from src.ImageEncoder import ImageEncoder

class pruebas():
    def __init__(self):
        self.lista_mensajes = []
        self.tipo_imagen = ""
        self.cantidad_partes = 0
        self.id_imagen = 1
        self.Encoder = ImageEncoder()
    
    def probar_imagen(self,ruta_imagen):
        base64_data, self.tipo_imagen = self.Encoder.imagen_a_cadena(ruta_imagen)
        if "Error" in base64_data:
            print(base64_data)
            return
        print(f"Tipo de imagen: {self.tipo_imagen}, Datos b64: {base64_data[:30]}...")
        partes, cantidad = self.Encoder.fragmentar_payload(base64_data, self.id_imagen)
        self.cantidad_partes = len(partes)
        print(f"Número de partes: {self.cantidad_partes, cantidad}, muestra de partes: {partes[:3]}...")
        print("Mensajes fragmentados y almacenados en lista_mensajes")
        self.reconstruir_imagen(partes)

    def reconstruir_imagen(self, trozos):
        if not trozos:
            print("No hay mensajes para reconstruir la imagen.")
            return
        cadena_completa = ''.join([mensaje['data'] for mensaje in trozos if 'data' in mensaje])
        print(f"Cadena completa reconstruida, longitud: {len(cadena_completa)}, muestra: {cadena_completa[:30]}...")
        ruta_salida = f"Datos\Imagenes{self.id_imagen}_reconstruida.{self.tipo_imagen}"
        self.Encoder.cadena_a_imagen(cadena_completa, ruta_salida)
        print(f"Imagen reconstruida y guardada en {ruta_salida}")

Probando = pruebas()
Probando.probar_imagen("Datos/Imagenes/Prueba.jpg")