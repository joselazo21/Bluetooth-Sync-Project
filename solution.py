import os
import time
import socket
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuración
LOCAL_FOLDER = "C:/Users/17863/Desktop/bluetooth"  
PEER_FOLDER = "/home/jose/ax"  
local_addr = "70:A8:D3:A5:85:B0"  
peer_addr = "F4:26:79:7C:41:3C"  
port = 11  

# Clase para manejar eventos de sincronización
class FolderSyncHandler(FileSystemEventHandler):
    def __init__(self, peer_addr, port):
        self.peer_addr = peer_addr
        self.port = port

    def send_file(self, src_path):
        try:
            relative_path = os.path.relpath(src_path, LOCAL_FOLDER)
            with open(src_path, "rb") as f:
                data = f.read()
            # Enviar archivo con ruta relativa
            with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as sock:
                sock.connect((self.peer_addr, self.port))
                sock.send(f"SEND|{relative_path}|{len(data)}".encode())
                sock.send(data)
            print(f"Archivo enviado: {relative_path}")
        except Exception as e:
            print(f"Error al enviar archivo: {e}")

    def send_delete(self, src_path):
        try:
            relative_path = os.path.relpath(src_path, LOCAL_FOLDER)
            # Notificar eliminación
            with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as sock:
                sock.connect((self.peer_addr, self.port))
                sock.send(f"DELETE|{relative_path}".encode())
            print(f"Archivo eliminado notificado: {relative_path}")
        except Exception as e:
            print(f"Error al notificar eliminación: {e}")

    def on_modified(self, event):
        if not event.is_directory:
            print(f"Archivo modificado: {event.src_path}")
            self.send_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            print(f"Archivo creado: {event.src_path}")
            self.send_file(event.src_path)

    def on_deleted(self, event):
        print(f"Archivo eliminado: {event.src_path}")
        self.send_delete(event.src_path)