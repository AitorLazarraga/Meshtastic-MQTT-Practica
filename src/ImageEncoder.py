import base64
from PIL import Image 
from typing import TypeVar, Generic, List, Tuple, Dict

T = TypeVar('T')

class ImageEncoder(Generic[T]):
    def __init__(self):
        self.cadena_imagen = ""
        self.cadena_base64 = ""
        self.cadena_cortada = []
        self.cantidad_partes = 0
        self.tipo_imagen = ""
        self.max_bytes = 200  # Máximo tamaño en bytes por fragmento

    def imagen_a_cadena(self, ruta_imagen):
        """
        Convierte una imagen a una cadena Base64.
        """
        try:
            with open(ruta_imagen, "rb") as imagen_file:
                self.tipo_imagen = ruta_imagen.split('.')[-1]  # Obtener la extensión del archivo
                # Lee los datos binarios de la imagen
                imagen_bytes = imagen_file.read()
                # Codifica los bytes a Base64
                self.cadena_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
                return self.cadena_base64, self.tipo_imagen
        except FileNotFoundError:
            return "Error: El archivo de imagen no se encontró."
        except Exception as e:
            return f"Ocurrió un error al procesar la imagen: {e}"
    
    def cadena_a_imagen(self, cadena_base64, ruta_salida):
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

    def fragmentar_payload(self, base64_data : str, id_imagen: T):
        partes = []
        index = 0

        while base64_data:
            # Buscamos cuántos caracteres caben en la cadena 'data'
            for i in range(1, len(base64_data) + 1):
                dic = {'id': id_imagen, 'part': index, 'data': base64_data[:i]}
                literal = str(dic)
                size = len(literal.encode('utf-8'))

                if size > self.max_bytes:
                    i -= 1
                    break

            parte_dic = {'id': id_imagen, 'part': index, 'data': base64_data[:i]}
            partes.append(parte_dic)
            base64_data = base64_data[i:]
            index += 1

        print(f"Debug: La imagen tiene {index} partes.")
        return partes, index
    
    def reconstruir_imagen(self, procesador_texto):
        """
        Reconstruye una imagen recibida por partes.
        
        Args:
            procesador_texto: Instancia de Objeto procesador que contiene las partes de la imagen
        """
        print("Fin de recepción de imagen")
        
        if not procesador_texto.partes_imagen:
            print("Error: No hay partes de imagen para reconstruir")
            procesador_texto.flag_imagen = False
            return
        
        id_imagen = procesador_texto.partes_imagen[0].get('ID')
        tipo_imagen = procesador_texto.partes_imagen[0].get('Format')
        
        # Eliminar el mensaje de inicio
        del procesador_texto.partes_imagen[0]
        
        if len(procesador_texto.partes_imagen) == procesador_texto.partes_esperadas:
            print("Todas las partes recibidas correctamente")
            
            # Ordenar por número de parte
            procesador_texto.partes_imagen.sort(key=lambda x: x.get('part', 0))
            
            # Reconstruir la cadena completa
            cadena_completa = ''.join([p['data'] for p in procesador_texto.partes_imagen if 'data' in p])
            
            # Guardar la imagen
            ruta_salida = f"Datos/Imagenes/imagen_recibida_{id_imagen}.{tipo_imagen}"
            print(f"Guardando imagen recibida como {ruta_salida}")
            
            # CORRECCIÓN: No pasar self como argumento
            self.cadena_a_imagen(cadena_completa, ruta_salida)
            
            print(f"Imagen {id_imagen} guardada exitosamente")
        else:
            print(f"Faltan partes de la imagen. Esperadas: {procesador_texto.partes_esperadas}, Recibidas: {len(procesador_texto.partes_imagen)}")
            print(f"Partes recibidas: {[p.get('part', '?') for p in procesador_texto.partes_imagen]}")
        
        # Limpiar estado
        procesador_texto.flag_imagen = False
        procesador_texto.partes_imagen = []
        procesador_texto.partes_esperadas = 0
        procesador_texto.id_actual = None