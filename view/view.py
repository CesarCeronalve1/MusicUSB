import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTreeWidget, QTreeWidgetItem, QLabel, QProgressBar,
                             QPushButton, QMenu, QAction, QMessageBox, QFileDialog,
                             QAbstractItemView, QSplitter, QFrame, QHeaderView,
                             QMenuBar, QInputDialog, QApplication, QCheckBox,
                             QDialog, QLineEdit, QTextEdit, QGroupBox, QProgressDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QColor, QFont, QDragEnterEvent, QDropEvent, QBrush
from utils.utils import get_folder_color, find_suitable_usb_size, format_size, bytes_to_mb

class USBCopyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Copia a USB")
        self.setModal(True)
        self.resize(400, 500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Grupo de metadatos
        metadata_group = QGroupBox("Metadatos (aplicar a todas las canciones)")
        metadata_layout = QVBoxLayout(metadata_group)
        
        # Álbum
        album_layout = QHBoxLayout()
        album_layout.addWidget(QLabel("Álbum:"))
        self.album_edit = QLineEdit()
        album_layout.addWidget(self.album_edit)
        metadata_layout.addLayout(album_layout)
        
        # Género
        genre_layout = QHBoxLayout()
        genre_layout.addWidget(QLabel("Género:"))
        self.genre_edit = QLineEdit()
        genre_layout.addWidget(self.genre_edit)
        metadata_layout.addLayout(genre_layout)
        
        # Comentarios
        comment_layout = QVBoxLayout()
        comment_layout.addWidget(QLabel("Comentarios:"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setMaximumHeight(80)
        comment_layout.addWidget(self.comment_edit)
        metadata_layout.addLayout(comment_layout)
        
        # Portada
        cover_layout = QHBoxLayout()
        cover_layout.addWidget(QLabel("Portada:"))
        self.cover_path_edit = QLineEdit()
        self.cover_path_edit.setReadOnly(True)
        self.browse_cover_btn = QPushButton("Examinar...")
        self.browse_cover_btn.clicked.connect(self.browse_cover)
        cover_layout.addWidget(self.cover_path_edit)
        cover_layout.addWidget(self.browse_cover_btn)
        metadata_layout.addLayout(cover_layout)
        
        layout.addWidget(metadata_group)
        
        # Botones
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Copiar")
        self.cancel_btn = QPushButton("Cancelar")
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # Conectar botones
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
    
    def browse_cover(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar portada", "", 
            "Imágenes (*.jpg *.jpeg *.png *.bmp)"
        )
        if file_path:
            self.cover_path_edit.setText(file_path)
    
    def get_metadata(self):
        return {
            'album': self.album_edit.text().strip(),
            'genre': self.genre_edit.text().strip(),
            'comment': self.comment_edit.toPlainText().strip(),
            'cover_path': self.cover_path_edit.text().strip()
        }
class USBCopyProgressDialog(QDialog):
    pause_state_changed = pyqtSignal(bool)  # Señal para pausa
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Copiando a USB")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.is_paused = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Etiqueta principal
        self.main_label = QLabel("Preparando copia...")
        layout.addWidget(self.main_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Etiqueta del archivo actual
        self.current_file_label = QLabel("")
        self.current_file_label.setWordWrap(True)
        layout.addWidget(self.current_file_label)
        
        # Botones
        button_layout = QHBoxLayout()
        self.pause_btn = QPushButton("Pausar")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.pause_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
    
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.setText("Reanudar")
            self.main_label.setText("COPIA PAUSADA")
        else:
            self.pause_btn.setText("Pausar")
            self.main_label.setText("Copiando...")
        
        # Emitir señal de pausa/reanudación
        self.pause_state_changed.emit(self.is_paused)
    
    def update_progress(self, current, total, current_file):
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        if not self.is_paused:
            self.main_label.setText(f"Copiando... {current}/{total} archivos")
        self.current_file_label.setText(f"Archivo: {os.path.basename(current_file)}")



class PlaylistView(QMainWindow):
    # Señales
    files_dropped = pyqtSignal(list)
    song_selection_changed = pyqtSignal(list)
    delete_selected_requested = pyqtSignal()
    delete_unselected_requested = pyqtSignal()
    change_destination_requested = pyqtSignal(list, str)
    rename_destination_requested = pyqtSignal(str, str)
    remove_destination_requested = pyqtSignal(str)
    save_playlist_requested = pyqtSignal()
    load_playlist_requested = pyqtSignal()
    new_playlist_requested = pyqtSignal()
    close_playlist_requested = pyqtSignal()
    copy_to_usb_requested = pyqtSignal(str, dict)
    base_changed = pyqtSignal(bool)  # True = base 1024, False = base 1000
    pause_state_changed = pyqtSignal(bool)  # Nueva señal para pausa
    
    def __init__(self):
        super().__init__()
        self.sort_orders = {}
        self.base_1024 = True  # Por defecto usamos base 1024
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Organizador de Playlists")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de menú
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Archivo')
        
        new_action = QAction('Nueva Playlist', self)
        load_action = QAction('Cargar Playlist', self)
        save_action = QAction('Guardar Playlist', self)
        close_action = QAction('Cerrar Playlist', self)
        copy_usb_action = QAction('Copiar a USB', self)
        
        file_menu.addAction(new_action)
        file_menu.addAction(load_action)
        file_menu.addAction(save_action)
        file_menu.addAction(close_action)
        file_menu.addSeparator()
        file_menu.addAction(copy_usb_action)
        
        # Conectar acciones del menú
        new_action.triggered.connect(self.new_playlist_requested.emit)
        load_action.triggered.connect(self.load_playlist_requested.emit)
        save_action.triggered.connect(self.save_playlist_requested.emit)
        close_action.triggered.connect(self.close_playlist_requested.emit)
        copy_usb_action.triggered.connect(self.on_copy_to_usb)
        
        # TreeWidget para mostrar canciones agrupadas
        self.song_tree = QTreeWidget()
        self.song_tree.setColumnCount(8)
        self.song_tree.setHeaderLabels([
            "Título", "Artista", "Álbum", "Género", 
            "Ruta", "kbps", "Duración", "Tamaño"
        ])
        
        # Configurar el árbol
        self.song_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.song_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.song_tree.setSortingEnabled(True)
        self.song_tree.header().setSectionsMovable(True)
        self.song_tree.header().setSectionResizeMode(QHeaderView.Interactive)
        
        # Conectar la señal de clic en el encabezado para ordenar
        self.song_tree.header().sectionClicked.connect(self.on_header_clicked)
        
        # Inicializar órdenes de clasificación (ascendente por defecto)
        for i in range(self.song_tree.columnCount()):
            self.sort_orders[i] = Qt.AscendingOrder
        
        # Información de la playlist
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Box)
        info_layout = QVBoxLayout(info_frame)
        
        # Checkbox para cambiar base de cálculo
        base_layout = QHBoxLayout()
        self.base_checkbox = QCheckBox("Usar base de fabricantes (1000 en lugar de 1024)")
        self.base_checkbox.setChecked(not self.base_1024)
        self.base_checkbox.stateChanged.connect(self.on_base_changed)
        base_layout.addWidget(self.base_checkbox)
        base_layout.addStretch()
        
        # Información de capacidad USB
        usb_layout = QHBoxLayout()
        self.usb_label = QLabel("USB más pequeña que cabe: ")
        self.usb_size_label = QLabel("2 GB")
        usb_layout.addWidget(self.usb_label)
        self.usb_size_label.setStyleSheet("font-weight: bold;")
        usb_layout.addWidget(self.usb_size_label)
        usb_layout.addStretch()
        
        # Información de tamaño
        size_layout = QHBoxLayout()
        self.size_label = QLabel("Tamaño total: ")
        self.size_value_label = QLabel("0 MB")
        size_layout.addWidget(self.size_label)
        self.size_value_label.setStyleSheet("font-weight: bold;")
        size_layout.addWidget(self.size_value_label)
        size_layout.addStretch()
        
        # Información de espacio disponible
        space_layout = QHBoxLayout()
        self.space_label = QLabel("Espacio disponible en USB: ")
        self.space_value_label = QLabel("0 MB")
        space_layout.addWidget(self.space_label)
        self.space_value_label.setStyleSheet("font-weight: bold;")
        space_layout.addWidget(self.space_value_label)
        space_layout.addStretch()
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        info_layout.addLayout(base_layout)
        info_layout.addLayout(usb_layout)
        info_layout.addLayout(size_layout)
        info_layout.addLayout(space_layout)
        info_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(self.song_tree)
        main_layout.addWidget(info_frame)
        
        # Conectar señales
        self.song_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.song_tree.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Habilitar drag and drop
        self.setAcceptDrops(True)
    
    def on_copy_to_usb(self):
        """Maneja la solicitud de copia a USB"""
        usb_path = self.get_usb_destination()
        if not usb_path:
            return
        
        metadata_config = self.get_usb_copy_config()
        if metadata_config is None:  # Usuario canceló
            return
        
        self.copy_to_usb_requested.emit(usb_path, metadata_config)
    
    def get_usb_copy_config(self):
        """Muestra el diálogo para configurar la copia a USB"""
        dialog = USBCopyDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_metadata()
        return None
    
    def get_usb_destination(self):
        """Obtiene el directorio USB destino"""
        return QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar destino USB", 
            "",
            QFileDialog.ShowDirsOnly
        )
    
    def show_copy_progress(self, total_files):
        """Muestra el diálogo de progreso"""
        self.progress_dialog = USBCopyProgressDialog(self)
        self.progress_dialog.show()
        return self.progress_dialog
    
    def update_copy_progress(self, current, total, current_file):
        """Actualiza el progreso de copia"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.update_progress(current, total, current_file)
            # Forzar actualización de la UI
            QApplication.processEvents()
    
    def close_copy_progress(self):
        """Cierra el diálogo de progreso"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
    
    def on_base_changed(self, state):
        self.base_1024 = (state == Qt.Unchecked)
        self.base_changed.emit(self.base_1024)
    
    def on_header_clicked(self, column):
        # Cambiar el orden de clasificación para esta columna
        if column in self.sort_orders:
            self.sort_orders[column] = Qt.DescendingOrder if self.sort_orders[column] == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.sort_orders[column] = Qt.AscendingOrder
        
        # Ordenar por la columna seleccionada
        self.song_tree.sortItems(column, self.sort_orders[column])
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        self.files_dropped.emit(file_paths)
        event.acceptProposedAction()
    
    def show_context_menu(self, position):
        menu = QMenu()
        selected_items = self.song_tree.selectedItems()
        
        if not selected_items:
            return
        
        # Determinar si la selección incluye grupos o canciones individuales
        has_groups = any(item.parent() is None for item in selected_items)
        has_songs = any(item.parent() is not None for item in selected_items)
        
        # Opciones para grupos
        if has_groups:
            group_action = QAction("Colapsar/Expandir destino", self)
            group_action.triggered.connect(self.toggle_group_expansion)
            menu.addAction(group_action)
            
            rename_group_action = QAction("Renombrar destino", self)
            rename_group_action.triggered.connect(self.on_rename_destination)
            menu.addAction(rename_group_action)
            
            delete_group_action = QAction("Borrar destino", self)
            delete_group_action.triggered.connect(self.on_delete_destination)
            menu.addAction(delete_group_action)
            
            menu.addSeparator()
        
        # Opciones para canciones
        if has_songs:
            change_dest_action = QAction("Cambiar destino", self)
            change_dest_action.triggered.connect(self.on_change_destination)
            menu.addAction(change_dest_action)
            
            delete_action = QAction("Eliminar seleccionadas", self)
            delete_action.triggered.connect(self.delete_selected_requested.emit)
            menu.addAction(delete_action)
        
        menu.exec_(self.song_tree.mapToGlobal(position))
    
    def toggle_group_expansion(self):
        selected_items = self.song_tree.selectedItems()
        for item in selected_items:
            if item.parent() is None:  # Es un grupo
                item.setExpanded(not item.isExpanded())
    
    def on_rename_destination(self):
        selected_items = self.song_tree.selectedItems()
        if not selected_items or selected_items[0].parent() is not None:
            return
        
        group_item = selected_items[0]
        old_destination = group_item.text(0)
        new_dest = self.get_new_destination(old_destination)
        if new_dest:
            self.rename_destination_requested.emit(old_destination, new_dest)
    
    def on_delete_destination(self):
        selected_items = self.song_tree.selectedItems()
        if not selected_items or selected_items[0].parent() is not None:
            return
        
        group_item = selected_items[0]
        destination = group_item.text(0)
        
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que quieres eliminar todas las canciones del destino '{destination}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.remove_destination_requested.emit(destination)
    
    def on_change_destination(self):
        selected_items = self.song_tree.selectedItems()
        song_indices = []
        
        for item in selected_items:
            if item.parent() is not None:  # Es una canción
                if hasattr(item, 'song_index'):
                    song_indices.append(item.song_index)
        
        if song_indices:
            # Pedir el nuevo destino
            new_dest = self.get_new_destination()
            if new_dest:
                self.change_destination_requested.emit(song_indices, new_dest)
    
    def get_selected_song_indices(self):
        """Obtiene los índices de las canciones seleccionadas en el modelo"""
        selected_items = self.song_tree.selectedItems()
        indices = []
        
        for item in selected_items:
            if hasattr(item, 'song_index') and item.song_index is not None:
                indices.append(item.song_index)
        
        return indices
    
    def on_selection_changed(self):
        selected_indices = self.get_selected_song_indices()
        self.song_selection_changed.emit(selected_indices)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            if event.modifiers() & Qt.ShiftModifier:
                self.delete_unselected_requested.emit()
            else:
                self.delete_selected_requested.emit()
        else:
            super().keyPressEvent(event)
    
    def display_playlist(self, playlist):
        self.song_tree.clear()
        
        # Limpiar los índices de canciones
        self.song_indices_map = {}
        
        # Agrupar canciones por destino
        songs_by_dest = playlist.get_songs_by_destination()
        
        # Crear grupos para cada destino
        for destination, songs in songs_by_dest.items():
            # Nombre del grupo (usar "/" para raíz)
            group_name = destination if destination else "/"
            
            # Crear item de grupo
            group_item = QTreeWidgetItem(self.song_tree)
            group_item.setText(0, group_name)
            group_item.setExpanded(True)  # Expandido por defecto
            
            # Aplicar color al grupo
            bg_color, text_color = get_folder_color(destination)
            for col in range(self.song_tree.columnCount()):
                group_item.setBackground(col, QBrush(QColor(bg_color)))
                group_item.setForeground(col, QBrush(QColor(text_color)))
            
            # Hacer que el grupo sea más visible
            font = group_item.font(0)
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            group_item.setFont(0, font)
            
            # Agregar canciones como hijos del grupo
            for i, song in enumerate(songs):
                song_item = QTreeWidgetItem(group_item)
                
                # Almacenar el índice de la canción en el modelo
                song_index = playlist.songs.index(song)
                song_item.song_index = song_index
                self.song_indices_map[song_index] = song_item
                
                # Llenar las celdas con los datos de la canción
                song_item.setText(0, song.title)
                song_item.setText(1, song.artist)
                song_item.setText(2, song.album)
                song_item.setText(3, song.genre)
                song_item.setText(4, song.file_path)
                song_item.setText(5, str(song.bitrate))
                song_item.setText(6, song.duration_formatted)
                song_item.setText(7, song.size_formatted(self.base_1024))
                
                # Aplicar color más claro para las canciones
                lighter_bg = self.lighten_color(bg_color)
                for col in range(self.song_tree.columnCount()):
                    song_item.setBackground(col, QBrush(QColor(lighter_bg)))
                    song_item.setForeground(col, QBrush(QColor(text_color)))
    
    def lighten_color(self, hex_color, factor=0.3):
        """Aclara un color hex"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_playlist_info(self, playlist):
        total_size_mb = playlist.total_size_mb(self.base_1024)
        usb_size_gb = find_suitable_usb_size(total_size_mb, self.base_1024)
        
        # Calcular espacio disponible en MB
        if self.base_1024:
            # Base binaria
            usb_size_mb = usb_size_gb * 1024
        else:
            # Base decimal (fabricantes)
            usb_size_mb = usb_size_gb * 1000
        
        available_mb = usb_size_mb - total_size_mb
        
        # Actualizar labels (siempre en MB)
        self.usb_size_label.setText(f"{usb_size_gb} GB")
        self.size_value_label.setText(f"{total_size_mb:.2f} MB")
        self.space_value_label.setText(f"{available_mb:.2f} MB")
        
        # Actualizar barra de progreso
        usage_percentage = (total_size_mb / usb_size_mb) * 100
        self.progress_bar.setValue(int(usage_percentage))
        
        # Cambiar color de la barra según el uso
        if usage_percentage > 90:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
        elif usage_percentage > 70:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
        else:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")
    
    def get_new_destination(self, current_destination=""):
        new_dest, ok = QInputDialog.getText(
            self, "Cambiar Destino", 
            "Ingrese el nuevo destino (carpeta):", 
            text=current_destination
        )
        
        if ok and new_dest:
            return new_dest
        return None
    
    def show_message(self, title, message, is_error=False):
        if is_error:
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def get_save_filename(self):
        return QFileDialog.getSaveFileName(
            self, "Guardar Playlist", "", "Playlist Files (*.m3u)"
        )[0]
    
    def get_load_filename(self):
        return QFileDialog.getOpenFileName(
            self, "Cargar Playlist", "", "Playlist Files (*.m3u)"
        )[0]