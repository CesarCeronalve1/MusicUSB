import os
from mutagen import File

class Cancion:
    def __init__(self, ruta, carpeta=""):
        self.ruta = ruta
        self.carpeta = carpeta
        self.metadatos = self.obtener_metadatos()

    def nombre(self):
        return os.path.basename(self.ruta)

    def obtener_metadatos(self):
        try:
            audio = File(self.ruta, easy=True)
            if audio is None:
                return {}
            return {
                "titulo": audio.get("title", [self.nombre()])[0],
                "artista": audio.get("artist", ["Desconocido"])[0],
                "album": audio.get("album", ["Desconocido"])[0],
                "duracion": int(audio.info.length) if audio.info else 0
            }
        except Exception:
            return {}
