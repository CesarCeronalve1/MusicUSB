from vista.interfaz import Interfaz
from controlador.controlador import Controlador

if __name__ == "__main__":
    vista = Interfaz(None)
    controlador = Controlador(vista)
    vista.controlador = controlador
    vista.iniciar()
