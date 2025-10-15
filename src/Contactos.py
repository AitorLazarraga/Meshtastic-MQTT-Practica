import pandas as pd
import os

class Contactos:
    def __init__(self):
        self.ruta = "Datos/PaginasAmarillas.csv"
        columnas = ["ID", "Nombre"]

        if os.path.exists(self.ruta):
            self.lista_contactos = pd.read_csv(self.ruta)
        else:
            self.lista_contactos = pd.DataFrame(columns=columnas)
            self.lista_contactos.to_csv(self.ruta, index=False)

    def _guardar(self):
        """Guarda la lista de contactos en el CSV."""
        self.lista_contactos.to_csv(self.ruta, index=False)

    def anadir_contacto(self, contacto_id, nombre=None):
        """Añade un contacto si no existe."""
        try:
            contacto_id = str(contacto_id)
            if "!" in contacto_id:
                contacto_id = int(contacto_id.replace("!", ""), 16)
        except ValueError:
            pass
        
        if (self.lista_contactos["ID"] == contacto_id).any():
            return

        if nombre is None:
            nombre = input("Añade un nombre para el nuevo contacto: ")

        nombre = nombre.lower()

        nuevo = pd.DataFrame([{"ID": contacto_id, "Nombre": nombre}])
        self.lista_contactos = pd.concat([self.lista_contactos, nuevo], ignore_index=True)
        self._guardar()
        print(f"Contacto '{nombre}' añadido correctamente.")

    def mostrar_contactos(self):
        """Muestra todos los contactos."""
        self.lista_contactos = pd.read_csv(self.ruta, converters={
    "ID": lambda x: x.strip('"'),
    "Nombre": lambda x: x.strip('"')
})
        if self.lista_contactos.empty:
            print("No hay contactos registrados.")
            return
        for _, fila in self.lista_contactos.iterrows():
            print(f"ID: {fila['ID']} - Nombre: {fila['Nombre']}")

    def elegir_contacto(self, nombre):
        """Busca y devuelve un contacto por nombre."""
        nombre = nombre.lower()
        self.lista_contactos = pd.read_csv(self.ruta, converters={
    "ID": lambda x: x.strip('"'),
    "Nombre": lambda x: x.strip('"')
})
        print(self.lista_contactos)
        resultado = self.lista_contactos[self.lista_contactos["Nombre"].str.lower() == nombre]
        if resultado.empty:
            print("No se encontró ningún contacto con ese nombre.")
            return None
        else:
            contacto = resultado.iloc[0].to_dict()
            return contacto["ID"]
