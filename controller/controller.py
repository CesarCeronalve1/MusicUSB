import os
import shutil
import time
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from model.model import Playlist, Song
from view.view import PlaylistView
from mutagen import File
from mutagen.id3 import ID3, TALB, TCON, COMM, APIC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis

class USBCopyThread(QThread):
    progress_updated = pyqtSignal(int, int, str)
    finished_success = pyqtSignal()
    finished_error = pyqtSignal(str)
    
    def __init__(self, songs, usb_path, metadata_config):
        super().__init__()
        self.songs = songs
        self.usb_path = usb_path
        self.metadata_config = metadata_config
        self._is_cancelled = False
        self._is_paused = False
        self.mutex = QMutex()
    
    def cancel(self):
        self._is_cancelled = True
    
    def set_paused(self, paused):
        self.mutex.lock()
        self._is_paused = paused
        self.mutex.unlock()
    
    def run(self):
        try:
            total_files = len(self.songs)
            
            for i, song in enumerate(self.songs):
                if self._is_cancelled:
                    break
                
                # Esperar si está pausado
                while True:
                    self.mutex.lock()
                    paused = self._is_paused
                    self.mutex.unlock()
                    if not paused or self._is_cancelled:
                        break
                    time.sleep(0.1)  # Pequeña pausa para no consumir muchos recursos
                
                if self._is_cancelled:
                    break
                
                # Emitir progreso
                self.progress_updated.emit(i + 1, total_files, song.file_path)
                
                # Determinar ruta destino
                dest_path = self._get_destination_path(song.destination, song.file_name)
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Copiar archivo
                shutil.copy2(song.file_path, dest_path)
                
                # Aplicar metadatos si se especificaron
                if any(self.metadata_config.values()):
                    self._apply_metadata(dest_path)
            
            if not self._is_cancelled:
                self.finished_success.emit()
                
        except Exception as e:
            self.finished_error.emit(str(e))
    
    def _get_destination_path(self, destination, file_name):
        """Construye la ruta destino completa"""
        if not destination or destination == "/":
            # Copiar directamente a la raíz
            return os.path.join(self.usb_path, file_name)
        else:
            # Crear estructura de carpetas
            return os.path.join(self.usb_path, destination, file_name)
    
    def _apply_metadata(self, file_path):
        """Aplica metadatos al archivo copiado"""
        try:
            # Primero intentar con easy=True para metadatos básicos
            audio = File(file_path, easy=True)
            if audio is None:
                return
            
            # Aplicar álbum
            if self.metadata_config['album']:
                audio['album'] = [self.metadata_config['album']]
            
            # Aplicar género
            if self.metadata_config['genre']:
                audio['genre'] = [self.metadata_config['genre']]
            
            # Aplicar comentario
            if self.metadata_config['comment']:
                # audio['comment'] = [self.metadata_config['comment']]
                print("aqui iria el comentario pero que hueva")
            # Guardar cambios
            audio.save()
            
            # Aplicar portada si se especificó
            if self.metadata_config['cover_path'] and os.path.exists(self.metadata_config['cover_path']):
                self._apply_cover(file_path)
                
        except Exception as e:
            print(f"Error aplicando metadatos a {file_path}: {e}")
    
 
    def _apply_cover(self, file_path):
        """Aplica portada al archivo de audio"""
        try:
            # Leer imagen
            with open(self.metadata_config['cover_path'], 'rb') as f:
                cover_data = f.read()

            # Obtener la extensión del archivo de portada para determinar el MIME type
            cover_ext = os.path.splitext(self.metadata_config['cover_path'])[1].lower()
            mime_type = 'image/jpeg'
            if cover_ext == '.png':
                mime_type = 'image/png'
            elif cover_ext == '.bmp':
                mime_type = 'image/bmp'

            # Detectar tipo de archivo de audio y aplicar portada según el formato
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.mp3':
                self._apply_cover_mp3(file_path, cover_data, mime_type)
            elif file_ext in ['.m4a', '.mp4']:
                self._apply_cover_mp4(file_path, cover_data, mime_type)
            elif file_ext == '.flac':
                self._apply_cover_flac(file_path, cover_data, mime_type)
            elif file_ext in ['.ogg', '.oga']:
                self._apply_cover_ogg(file_path, cover_data, mime_type)
            else:
                # Para otros formatos, intentar con el método easy
                self._apply_cover_generic(file_path, cover_data, mime_type)

        except Exception as e:
            print(f"Error aplicando portada a {file_path}: {e}")

    def _apply_cover_mp3(self, file_path, cover_data, mime_type):
        """Aplica portada a archivo MP3"""
        from mutagen.id3 import ID3, APIC

        try:
            audio = ID3(file_path)
        except:
            audio = ID3()

        # Eliminar portadas existentes
        audio.delall('APIC')

        # Agregar nueva portada
        audio.add(APIC(
            encoding=3,  # UTF-8
            mime=mime_type,
            type=3,  # Cover (front)
            desc='Cover',
            data=cover_data
        ))
        audio.save(file_path)

    def _apply_cover_mp4(self, file_path, cover_data, mime_type):
        """Aplica portada a archivo MP4/M4A"""
        from mutagen.mp4 import MP4, MP4Cover

        audio = MP4(file_path)
        cover_format = MP4Cover.FORMAT_JPEG if mime_type == 'image/jpeg' else MP4Cover.FORMAT_PNG
        audio['covr'] = [MP4Cover(cover_data, imageformat=cover_format)]
        audio.save()

    def _apply_cover_flac(self, file_path, cover_data, mime_type):
        """Aplica portada a archivo FLAC"""
        from mutagen.flac import FLAC, Picture

        audio = FLAC(file_path)

        # Crear objeto picture
        picture = Picture()
        picture.data = cover_data
        picture.type = 3  # Cover (front)
        picture.mime = mime_type
        picture.desc = 'Cover'

        # Limpiar imágenes existentes y agregar nueva
        audio.clear_pictures()
        audio.add_picture(picture)
        audio.save()

    def _apply_cover_ogg(self, file_path, cover_data, mime_type):
        """Aplica portada a archivo OGG"""
        import base64
        from mutagen.oggvorbis import OggVorbis

        audio = OggVorbis(file_path)

        # Crear objeto picture FLAC
        from mutagen.flac import Picture
        picture = Picture()
        picture.data = cover_data
        picture.type = 3
        picture.mime = mime_type
        picture.desc = 'Cover'

        # Codificar en base64
        picture_data = base64.b64encode(picture.write()).decode('ascii')
        audio['metadata_block_picture'] = [picture_data]
        audio.save()

    def _apply_cover_generic(self, file_path, cover_data, mime_type):
        """Intenta aplicar portada usando el método easy de mutagen"""
        audio = File(file_path, easy=True)
        if audio is not None:
            # Para algunos formatos, se puede usar el tag 'coverart' o 'cover'
            if 'coverart' in audio:
                audio['coverart'] = cover_data
            elif 'cover' in audio:
                audio['cover'] = cover_data
            audio.save()



class PlaylistController:
    def __init__(self):
        self.model = Playlist()
        self.view = PlaylistView()
        
        # Conectar señales de la vista
        self.view.files_dropped.connect(self.handle_files_dropped)
        self.view.song_selection_changed.connect(self.handle_selection_changed)
        self.view.delete_selected_requested.connect(self.delete_selected_songs)
        self.view.delete_unselected_requested.connect(self.delete_unselected_songs)
        self.view.change_destination_requested.connect(self.change_destination)
        self.view.rename_destination_requested.connect(self.rename_destination)
        self.view.remove_destination_requested.connect(self.remove_destination)
        self.view.save_playlist_requested.connect(self.save_playlist)
        self.view.load_playlist_requested.connect(self.load_playlist)
        self.view.new_playlist_requested.connect(self.new_playlist)
        self.view.close_playlist_requested.connect(self.close_playlist)
        self.view.copy_to_usb_requested.connect(self.copy_to_usb)
        self.view.base_changed.connect(self.on_base_changed)
        self.view.pause_state_changed.connect(self.on_pause_state_changed)
        
        # Estado actual
        self.selected_indices = []
        self.base_1024 = True
        self.copy_thread = None
        
        # Actualizar vista inicial
        self.update_view()
    
    def on_base_changed(self, base_1024):
        self.base_1024 = base_1024
        self.update_view()
    
    def on_pause_state_changed(self, paused):
        """Maneja cambios en el estado de pausa"""
        if self.copy_thread:
            self.copy_thread.set_paused(paused)
    
    def handle_files_dropped(self, file_paths):
        new_songs = []
        
        for path in file_paths:
            if os.path.isfile(path):
                # Es un archivo individual
                if self.is_audio_file(path):
                    new_songs.append(Song(file_path=path))
            elif os.path.isdir(path):
                # Es una carpeta, explorar recursivamente
                folder_songs = self.get_audio_files_from_folder(path)
                for song_path in folder_songs:
                    # Usar el nombre de la carpeta como destino
                    folder_name = os.path.basename(path)
                    new_songs.append(Song(file_path=song_path, destination=folder_name))
        
        self.model.add_songs(new_songs)
        self.update_view()
    
    def is_audio_file(self, file_path):
        audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'}
        return any(file_path.lower().endswith(ext) for ext in audio_extensions)
    
    def get_audio_files_from_folder(self, folder_path):
        audio_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if self.is_audio_file(file):
                    audio_files.append(os.path.join(root, file))
        return audio_files
    
    def handle_selection_changed(self, indices):
        self.selected_indices = indices
    
    def delete_selected_songs(self):
        if self.selected_indices:
            self.model.remove_songs(self.selected_indices)
            self.selected_indices = []
            self.update_view()
    
    def delete_unselected_songs(self):
        if self.selected_indices:
            self.model.remove_unselected_songs(self.selected_indices)
            self.selected_indices = []
            self.update_view()
        else:
            # Si no hay selección, eliminar todas
            self.model.songs.clear()
            self.update_view()
    
    def change_destination(self, indices, new_destination):
        if not indices or not new_destination:
            return
        
        self.model.update_destination(indices, new_destination)
        self.update_view()
    
    def rename_destination(self, old_destination, new_destination):
        if old_destination and new_destination:
            self.model.rename_destination(old_destination, new_destination)
            self.update_view()
    
    def remove_destination(self, destination):
        if destination:
            self.model.remove_destination(destination)
            self.update_view()
    
    def save_playlist(self):
        if not self.model.songs:
            self.view.show_message("Error", "No hay canciones para guardar", True)
            return
        
        filename = self.view.get_save_filename()
        if filename:
            try:
                self.model.save_to_m3u(filename)
                self.view.show_message("Éxito", "Playlist guardada correctamente")
            except Exception as e:
                self.view.show_message("Error", f"No se pudo guardar: {str(e)}", True)
    
    def load_playlist(self):
        filename = self.view.get_load_filename()
        if filename:
            try:
                self.model.load_from_m3u(filename)
                self.update_view()
                self.view.show_message("Éxito", "Playlist cargada correctamente")
            except Exception as e:
                self.view.show_message("Error", f"No se pudo cargar: {str(e)}", True)
    
    def new_playlist(self):
        self.model = Playlist()
        self.selected_indices = []
        self.update_view()
    
    def close_playlist(self):
        self.model = Playlist()
        self.selected_indices = []
        self.update_view()
    
    def copy_to_usb(self, usb_path, metadata_config):
        """Implementa la copia a USB con configuración de metadatos"""
        if not self.model.songs:
            self.view.show_message("Error", "No hay canciones para copiar", True)
            return
        
        # Crear y mostrar diálogo de progreso
        total_files = len(self.model.songs)
        self.progress_dialog = self.view.show_copy_progress(total_files)
        
        # Conectar señales del diálogo de progreso
        self.progress_dialog.rejected.connect(self.on_copy_cancelled)
        
        # Crear y ejecutar hilo de copia
        self.copy_thread = USBCopyThread(self.model.songs, usb_path, metadata_config)
        self.copy_thread.progress_updated.connect(self.on_copy_progress_updated)
        self.copy_thread.finished_success.connect(self.on_copy_finished)
        self.copy_thread.finished_error.connect(self.on_copy_error)
        self.copy_thread.start()
    
    def on_copy_progress_updated(self, current, total, current_file):
        """Actualiza el progreso de copia"""
        self.view.update_copy_progress(current, total, current_file)
    
    def on_copy_finished(self):
        """Maneja la finalización exitosa de la copia"""
        self.view.close_copy_progress()
        self.view.show_message("Éxito", "Copia a USB completada")
        self.copy_thread = None
    
    def on_copy_error(self, error_message):
        """Maneja errores durante la copia"""
        self.view.close_copy_progress()
        self.view.show_message("Error", f"Error durante la copia: {error_message}", True)
        self.copy_thread = None
    
    def on_copy_cancelled(self):
        """Maneja la cancelación de la copia"""
        if self.copy_thread and self.copy_thread.isRunning():
            self.copy_thread.cancel()
            self.copy_thread.wait(1000)  # Esperar máximo 1 segundo
        self.view.close_copy_progress()
        self.copy_thread = None
    
    def update_view(self):
        self.view.display_playlist(self.model)
        self.view.update_playlist_info(self.model)
    
    def show(self):
        self.view.show()