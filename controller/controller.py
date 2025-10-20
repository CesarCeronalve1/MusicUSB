import os
from PyQt5.QtWidgets import QInputDialog
from model.model import Playlist, Song
from view.view import PlaylistView

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
        
        # Estado actual
        self.selected_indices = []
        self.base_1024 = True
        
        # Actualizar vista inicial
        self.update_view()
    
    def on_base_changed(self, base_1024):
        self.base_1024 = base_1024
        self.update_view()
    
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
    
    def copy_to_usb(self):
        # Por implementar en el futuro
        self.view.show_message("Información", "Función de copia a USB aún no implementada")
    
    def update_view(self):
        self.view.display_playlist(self.model)
        self.view.update_playlist_info(self.model)
    
    def show(self):
        self.view.show()