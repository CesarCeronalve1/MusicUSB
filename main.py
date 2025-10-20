import sys
from PyQt5.QtWidgets import QApplication
from controller.controller import PlaylistController

def main():
    app = QApplication(sys.argv)
    
    controller = PlaylistController()
    controller.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()