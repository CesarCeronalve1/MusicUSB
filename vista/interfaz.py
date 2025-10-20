import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

class Interfaz:
    def __init__(self, controlador):
        self.controlador = controlador
        self.ventana = TkinterDnD.Tk()
        self.ventana.title("Organizador de Playlist")

        self.lista = tk.Listbox(self.ventana, width=100, selectmode=tk.SINGLE)
        self.lista.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Soporte para arrastrar archivos y carpetas
        self.lista.drop_target_register(DND_FILES)
        self.lista.dnd_bind('<<Drop>>', self.drop_archivos)

        botones = tk.Frame(self.ventana)
        botones.pack()

        tk.Button(botones, text="Agregar Canción", command=self.agregar_cancion).pack(side=tk.LEFT)
        tk.Button(botones, text="Mover a Carpeta", command=self.mover_cancion).pack(side=tk.LEFT)
        tk.Button(botones, text="Eliminar", command=self.eliminar_cancion).pack(side=tk.LEFT)
        tk.Button(botones, text="Guardar M3U", command=self.guardar_playlist).pack(side=tk.LEFT)

    def iniciar(self):
        self.ventana.mainloop()

    def actualizar_lista(self, canciones):
        self.lista.delete(0, tk.END)
        for i, cancion in enumerate(canciones):
            info = f"[{cancion.carpeta}] {cancion.metadatos.get('titulo', cancion.nombre())} - {cancion.metadatos.get('artista', '')}"
            self.lista.insert(tk.END, info)

    def agregar_cancion(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos de audio", "*.mp3 *.wav *.flac")])
        if archivo:
            carpeta = simpledialog.askstring("Carpeta", "¿En qué carpeta?")
            self.controlador.agregar_cancion(archivo, carpeta or "")

    def mover_cancion(self):
        seleccion = self.lista.curselection()
        if seleccion:
            indice = seleccion[0]
            nueva = simpledialog.askstring("Mover a", "Nueva carpeta:")
            if nueva is not None:
                self.controlador.mover_cancion(indice, nueva)

    def eliminar_cancion(self):
        seleccion = self.lista.curselection()
        if seleccion:
            self.controlador.eliminar_cancion(seleccion[0])

    def guardar_playlist(self):
        archivo = filedialog.asksaveasfilename(defaultextension=".m3u")
        if archivo:
            self.controlador.guardar_playlist(archivo)
            messagebox.showinfo("Guardado", "Playlist guardada correctamente.")

    def drop_archivos(self, evento):
        rutas = self.ventana.tk.splitlist(evento.data)
        for ruta in rutas:
            if os.path.isfile(ruta):
                self.controlador.agregar_cancion(ruta, "")
            elif os.path.isdir(ruta):
                for root, _, files in os.walk(ruta):
                    for f in files:
                        if f.lower().endswith((".mp3", ".wav", ".flac")):
                            self.controlador.agregar_cancion(os.path.join(root, f), "")
        self.controlador.actualizar_vista()
