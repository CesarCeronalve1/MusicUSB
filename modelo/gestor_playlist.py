from modelo.cancion import Cancion
import os

class GestorPlaylist:
    def __init__(self):
        self.canciones = []

    def agregar_cancion(self, ruta, carpeta=""):
        self.canciones.append(Cancion(ruta, carpeta))

    def mover_cancion(self, indice, nueva_carpeta):
        if 0 <= indice < len(self.canciones):
            self.canciones[indice].carpeta = nueva_carpeta

    def eliminar_cancion(self, indice):
        if 0 <= indice < len(self.canciones):
            del self.canciones[indice]

    def obtener_canciones_por_carpeta(self):
        estructura = {}
        for cancion in self.canciones:
            carpeta = cancion.carpeta
            if carpeta not in estructura:
                estructura[carpeta] = []
            estructura[carpeta].append(cancion)
        return estructura

    def guardar_como_m3u(self, ruta_archivo):
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            canciones_por_carpeta = self.obtener_canciones_por_carpeta()
            for carpeta in sorted(canciones_por_carpeta):
                if carpeta:
                    f.write(f"# Carpeta: {carpeta}\n")
                for cancion in canciones_por_carpeta[carpeta]:
                    f.write(f"{cancion.ruta}\n")
