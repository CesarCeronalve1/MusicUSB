import os
import colorsys
from typing import Tuple, Dict, Any
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from mutagen.asf import ASF

def get_file_size(file_path: str) -> int:
    """Obtiene el tamaño de un archivo en bytes"""
    try:
        return os.path.getsize(file_path)
    except (OSError, FileNotFoundError):
        return 0

def format_size(size_bytes: int, base_1024: bool = True) -> str:
    """Formatea el tamaño de bytes a una representación legible"""
    if base_1024:
        # Base binaria (1024)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    else:
        # Base decimal (1000) - como lo marcan los fabricantes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1000.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1000.0
        return f"{size_bytes:.2f} TB"

def bytes_to_mb(size_bytes: int, base_1024: bool = True) -> float:
    """Convierte bytes a megabytes"""
    if base_1024:
        return size_bytes / (1024 * 1024)
    else:
        return size_bytes / (1000 * 1000)

def bytes_to_gb(size_bytes: int, base_1024: bool = True) -> float:
    """Convierte bytes a gigabytes"""
    if base_1024:
        return size_bytes / (1024 * 1024 * 1024)
    else:
        return size_bytes / (1000 * 1000 * 1000)

def get_folder_color(folder_name: str) -> Tuple[str, str]:
    """
    Genera un color para una carpeta basado en la última letra
    Retorna: (color_fondo, color_texto)
    """
    if not folder_name:
        return "#3498db", "#ffffff"
    
    # Usamos la última letra para generar un color
    last_char = folder_name[-1].lower()
    
    # Mapeo de letras a colores
    color_map = {
        'a': '#e74c3c', 'b': '#3498db', 'c': '#2ecc71', 'd': '#f39c12',
        'e': '#9b59b6', 'f': '#1abc9c', 'g': '#d35400', 'h': '#c0392b',
        'i': '#2980b9', 'j': '#27ae60', 'k': '#f1c40f', 'l': '#8e44ad',
        'm': '#16a085', 'n': '#e67e22', 'o': '#2c3e50', 'p': '#7f8c8d',
        'q': '#e84393', 'r': '#00cec9', 's': '#fd79a8', 't': '#e17055',
        'u': '#0984e3', 'v': '#00b894', 'w': '#6c5ce7', 'x': '#fdcb6e',
        'y': '#e84393', 'z': '#636e72'
    }
    
    # Color por defecto si no está en el mapa
    bg_color = color_map.get(last_char, '#3498db')
    
    # Calcular luminosidad para determinar el color del texto
    r = int(bg_color[1:3], 16) / 255.0
    g = int(bg_color[3:5], 16) / 255.0
    b = int(bg_color[5:7], 16) / 255.0
    
    # Fórmula de luminosidad relativa
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    
    # Elegir color de texto basado en contraste
    text_color = "#ffffff" if luminance < 0.5 else "#000000"
    
    return bg_color, text_color

def find_suitable_usb_size(total_size_mb: float, base_1024: bool = True) -> int:
    """
    Encuentra el tamaño mínimo de USB que puede contener la playlist
    Tamaños: 2, 4, 8, 16, 32, 64, 128, 256 GB
    """
    usb_sizes = [2, 4, 8, 16, 32, 64, 128, 256]  # en GB
    
    if base_1024:
        # Base binaria
        total_size_gb = total_size_mb / 1024
    else:
        # Base decimal (fabricantes)
        total_size_gb = total_size_mb / 1000
    
    for size in usb_sizes:
        if total_size_gb <= size:
            return size
    
    return 256  # Tamaño máximo

def get_audio_metadata(file_path: str) -> Dict[str, Any]:
    """
    Obtiene los metadatos de un archivo de audio de manera robusta
    """
    metadata = {
        'title': '',
        'artist': '',
        'album': '',
        'genre': '',
        'bitrate': 0,
        'duration': 0
    }
    
    try:
        # Obtener el nombre del archivo sin extensión como título por defecto
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        metadata['title'] = file_name
        
        audio = File(file_path, easy=True)
        if audio is None:
            return metadata
        
        # Función auxiliar para obtener valores de tags
        def get_tag(tag_name, default=''):
            if tag_name in audio:
                value = audio[tag_name]
                if isinstance(value, list):
                    return value[0] if value else default
                return str(value)
            return default
        
        # Obtener metadatos básicos
        metadata['title'] = get_tag('title', file_name)
        metadata['artist'] = get_tag('artist', 'Desconocido')
        metadata['album'] = get_tag('album', 'Desconocido')
        metadata['genre'] = get_tag('genre', 'Desconocido')
        
        # Información técnica
        if hasattr(audio.info, 'bitrate'):
            metadata['bitrate'] = audio.info.bitrate // 1000 if audio.info.bitrate > 0 else 0
        
        if hasattr(audio.info, 'length'):
            metadata['duration'] = int(audio.info.length)
        
        # Si no se encontraron metadatos con easy=True, intentar con tags específicos por formato
        if metadata['artist'] == 'Desconocido' or metadata['album'] == 'Desconocido':
            # Intentar con el archivo sin easy=True para acceder a tags específicos
            audio_detailed = File(file_path)
            if audio_detailed:
                # Para MP3
                if isinstance(audio_detailed, MP3):
                    if 'TPE1' in audio_detailed:  # Artista
                        metadata['artist'] = str(audio_detailed['TPE1'])
                    if 'TALB' in audio_detailed:  # Álbum
                        metadata['album'] = str(audio_detailed['TALB'])
                    if 'TCON' in audio_detailed:  # Género
                        metadata['genre'] = str(audio_detailed['TCON'])
                
                # Para FLAC
                elif isinstance(audio_detailed, FLAC):
                    if 'artist' in audio_detailed:
                        metadata['artist'] = audio_detailed['artist'][0] if audio_detailed['artist'] else 'Desconocido'
                    if 'album' in audio_detailed:
                        metadata['album'] = audio_detailed['album'][0] if audio_detailed['album'] else 'Desconocido'
                    if 'genre' in audio_detailed:
                        metadata['genre'] = audio_detailed['genre'][0] if audio_detailed['genre'] else 'Desconocido'
                
                # Para MP4
                elif isinstance(audio_detailed, MP4):
                    if '\xa9ART' in audio_detailed:
                        metadata['artist'] = audio_detailed['\xa9ART'][0] if audio_detailed['\xa9ART'] else 'Desconocido'
                    if '\xa9alb' in audio_detailed:
                        metadata['album'] = audio_detailed['\xa9alb'][0] if audio_detailed['\xa9alb'] else 'Desconocido'
                    if '\xa9gen' in audio_detailed:
                        metadata['genre'] = audio_detailed['\xa9gen'][0] if audio_detailed['\xa9gen'] else 'Desconocido'
                
                # Para Ogg Vorbis
                elif isinstance(audio_detailed, OggVorbis):
                    if 'artist' in audio_detailed:
                        metadata['artist'] = audio_detailed['artist'][0] if audio_detailed['artist'] else 'Desconocido'
                    if 'album' in audio_detailed:
                        metadata['album'] = audio_detailed['album'][0] if audio_detailed['album'] else 'Desconocido'
                    if 'genre' in audio_detailed:
                        metadata['genre'] = audio_detailed['genre'][0] if audio_detailed['genre'] else 'Desconocido'
        
    except Exception as e:
        print(f"Error reading metadata for {file_path}: {e}")
        # En caso de error, al menos tenemos el nombre del archivo como título
    
    return metadata

def format_duration(seconds: int) -> str:
    """Formatea la duración de segundos a MM:SS"""
    if seconds <= 0:
        return "00:00"
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"