from modelo.gestor_playlist import GestorPlaylist

class Controlador:
    def __init__(self, vista):
        self.vista = vista
        self.modelo = GestorPlaylist()

    def agregar_cancion(self, ruta, carpeta=""):
        self.modelo.agregar_cancion(ruta, carpeta)
        self.actualizar_vista()

    def mover_cancion(self, indice, nueva_carpeta):
        self.modelo.mover_cancion(indice, nueva_carpeta)
        self.actualizar_vista()

    def eliminar_cancion(self, indice):
        self.modelo.eliminar_cancion(indice)
        self.actualizar_vista()

    def guardar_playlist(self, ruta_archivo):
        self.modelo.guardar_como_m3u(ruta_archivo)

    def actualizar_vista(self):
        self.vista.actualizar_lista(self.modelo.canciones)
