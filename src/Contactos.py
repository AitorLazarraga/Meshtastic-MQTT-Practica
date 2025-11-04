import pandas as pd
import os

class Contactos:
    def __init__(self):
        self.rutapag = "Datos/PaginasAmarillas.csv"
        columnas = ["ID", "Nombre"]

        if os.path.exists(self.rutapag):
            self.lista_contactos = pd.read_csv(self.rutapag)
        else:
            self.lista_contactos = pd.DataFrame(columns=columnas)
            self.lista_contactos.to_csv(self.rutapag, index=False)

    def _guardar(self):
        """Guarda la lista de contactos en el CSV."""
        self.lista_contactos.to_csv(self.rutapag, index=False)

    def anadir_contacto(self, contacto_id, nombre=None):
        """Añade un contacto si no existe."""
        # Asegurar que el ID sea string (para evitar errores de pandas)
        contacto_id = str(contacto_id)

        # Si ya existe, no lo añadimos
        if (self.lista_contactos["ID"] == contacto_id).any():
            return

        if nombre is None:
            return

        nombre = nombre.lower()

        nuevo = pd.DataFrame([{"ID": contacto_id, "Nombre": nombre}])
        self.lista_contactos = pd.concat([self.lista_contactos, nuevo], ignore_index=True)
        self._guardar()
        print(f"Contacto '{nombre}' añadido correctamente.")

    def mostrar_contactos(self):
        """Muestra todos los contactos."""
        self.lista_contactos = pd.read_csv(self.rutapag, converters={
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
        self.lista_contactos = pd.read_csv(self.rutapag, converters={
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
        
    def contactoNum(self, numero):
        numero = str(numero)
        self.lista_contactos = pd.read_csv(self.rutapag, dtype={"ID": str, "Nombre": str})

        resultado = self.lista_contactos[self.lista_contactos["ID"] == numero]
        if not resultado.empty:
            return resultado.iloc[0]["Nombre"]
        return None

        