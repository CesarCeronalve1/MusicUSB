import os
from typing import List, Dict, Set
from dataclasses import dataclass
from utils.utils import get_file_size, format_size, get_audio_metadata, format_duration

@dataclass
class Song:
    file_path: str
    destination: str = ""
    
    def __post_init__(self):
        self._metadata = None
    
    @property
    def file_name(self):
        return os.path.basename(self.file_path)
    
    @property
    def size(self):
        return get_file_size(self.file_path)
    
    def size_formatted(self, base_1024: bool = True):
        return format_size(self.size, base_1024)
    
    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = get_audio_metadata(self.file_path)
        return self._metadata
    
    @property
    def title(self):
        return self.metadata.get('title', self.file_name)
    
    @property
    def artist(self):
        return self.metadata.get('artist', 'Desconocido')
    
    @property
    def album(self):
        return self.metadata.get('album', 'Desconocido')
    
    @property
    def genre(self):
        return self.metadata.get('genre', 'Desconocido')
    
    @property
    def bitrate(self):
        return self.metadata.get('bitrate', 0)
    
    @property
    def duration(self):
        return self.metadata.get('duration', 0)
    
    @property
    def duration_formatted(self):
        return format_duration(self.duration)

class Playlist:
    def __init__(self):
        self.songs: List[Song] = []
        self.file_path: str = ""
    
    def add_song(self, song: Song):
        self.songs.append(song)
    
    def add_songs(self, songs: List[Song]):
        self.songs.extend(songs)
    
    def remove_song(self, index: int):
        if 0 <= index < len(self.songs):
            self.songs.pop(index)
    
    def remove_songs(self, indices: List[int]):
        # Ordenar índices de mayor a menor para evitar problemas al eliminar
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(self.songs):
                self.songs.pop(index)
    
    def remove_unselected_songs(self, selected_indices: List[int]):
        all_indices = set(range(len(self.songs)))
        selected_set = set(selected_indices)
        unselected_indices = sorted(all_indices - selected_set, reverse=True)
        
        for index in unselected_indices:
            self.songs.pop(index)
    
    def get_songs_by_destination(self) -> Dict[str, List[Song]]:
        result = {}
        for song in self.songs:
            dest = song.destination if song.destination else "/"
            if dest not in result:
                result[dest] = []
            result[dest].append(song)
        return result
    
    def get_all_destinations(self) -> Set[str]:
        return set(song.destination for song in self.songs)
    
    def update_destination(self, indices: List[int], new_destination: str):
        for index in indices:
            if 0 <= index < len(self.songs):
                self.songs[index].destination = new_destination
    
    def rename_destination(self, old_destination: str, new_destination: str):
        for song in self.songs:
            if song.destination == old_destination:
                song.destination = new_destination
    
    def remove_destination(self, destination: str):
        # Eliminar todas las canciones con este destino
        self.songs = [song for song in self.songs if song.destination != destination]
    
    @property
    def total_size(self):
        return sum(song.size for song in self.songs)
    
    def total_size_mb(self, base_1024: bool = True):
        from utils.utils import bytes_to_mb
        return bytes_to_mb(self.total_size, base_1024)
    
    def total_size_formatted(self, base_1024: bool = True):
        return format_size(self.total_size, base_1024)
    
    def load_from_m3u(self, file_path: str):
        self.file_path = file_path
        self.songs.clear()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            i = 0
            current_destination = ""
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith("#DESTINO:"):
                    current_destination = line[9:].strip()
                elif not line.startswith("#") and line and not line.isspace():
                    # Es una ruta de archivo
                    song = Song(file_path=line, destination=current_destination)
                    self.songs.append(song)
                
                i += 1
                
        except Exception as e:
            print(f"Error loading playlist: {e}")
    
    def save_to_m3u(self, file_path: str = None):
        if file_path:
            self.file_path = file_path
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write("#EXTM3U\n")
                
                songs_by_dest = self.get_songs_by_destination()
                
                for destination, songs in songs_by_dest.items():
                    if destination and destination != "/":
                        file.write(f"#DESTINO:{destination}\n")
                    
                    for song in songs:
                        file.write(f"{song.file_path}\n")
                        
        except Exception as e:
            print(f"Error saving playlist: {e}")
            raise