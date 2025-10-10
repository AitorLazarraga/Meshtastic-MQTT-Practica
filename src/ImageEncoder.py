import base64
from PIL import Image 
"""
Añadir una funcion para fragmentar la imagen en cadenas de 200bytes y enviarlas de una en una

n_paquetes = len(cadena_base64) // 200
n_paquetes = round(n_paquetes) + 1


Cada una tiene que tener un identificador unico para luego reconstruir la imagen (Igual esto se puede hacer mandando diccionarios ID:Mensaje)
Crear una funcion para reconstruir la imagen a partir de las cadenas recibidas (Si esta por diccionario primero guardarlos todos en lista, ordenar por Keys y luego sacar payloads)

for key in sorted(mensajes.keys()):
    lista_mensajes.append(mensajes[key])
    
Mandar mensaje de inicio y mensaje de fin de transmision indicando nº de paquetes

Indicar al principio tamaño imagen, nº de paquetes, tipo imagen.

{ID:ParteFoto}

"""

class ImageEncoder:
    def __init__(self):
        self.cadena_imagen = ""
        self.cadena_base64 = ""

    def imagen_a_cadena(self,ruta_imagen):
        """
        Convierte una imagen a una cadena Base64.
        """
        try:
            with open(ruta_imagen, "rb") as imagen_file:
                # Lee los datos binarios de la imagen
                imagen_bytes = imagen_file.read()
                # Codifica los bytes a Base64
                self.cadena_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
                print(self.cadena_base64)
                return self.cadena_base64
        except FileNotFoundError:
            return "Error: El archivo de imagen no se encontró."
        except Exception as e:
            return f"Ocurrió un error al procesar la imagen: {e}"
    
    def cadena_a_imagen(self,cadena_base64, ruta_salida):
        """
        Convierte una cadena Base64 de vuelta a una imagen y la guarda.
        """
        try:
            # Decodifica la cadena Base64 a bytes
            imagen_bytes = base64.b64decode(cadena_base64)
            # Escribe los bytes en un archivo de imagen
            with open(ruta_salida, "wb") as imagen_file:
                imagen_file.write(imagen_bytes)
            print(f"Imagen guardada en {ruta_salida}")
        except Exception as e:
            print(f"Ocurrió un error al guardar la imagen: {e}")
