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

# Función para recibir archivos y aplicar cambios en la carpeta local
def start_receiver(local_addr, port):
    try:
        server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        server_sock.bind((local_addr, port))
        server_sock.listen(1)
        print("Esperando conexiones...")

        while True:
            client_sock, _ = server_sock.accept()
            with client_sock:
                # Recibir comando
                command = client_sock.recv(1024).decode()
                if command.startswith("SEND"):
                    _, relative_path, data_len = command.split("|")
                    data_len = int(data_len)
                    data = client_sock.recv(data_len)

                    # Guardar archivo
                    local_path = os.path.join(LOCAL_FOLDER, relative_path)
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, "wb") as f:
                        f.write(data)
                    print(f"Archivo recibido y guardado: {relative_path}")

                elif command.startswith("DELETE"):
                    _, relative_path = command.split("|")
                    local_path = os.path.join(LOCAL_FOLDER, relative_path)
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    print(f"Archivo eliminado localmente: {relative_path}")

    except Exception as e:
        print(f"Error en el receptor: {e}")

# Función principal
def main():
    # Iniciar receptor en un hilo separado
    receiver_thread = threading.Thread(target=start_receiver, args=(local_addr, port))
    receiver_thread.daemon = True
    receiver_thread.start()

    # Configurar observador para la carpeta local
    event_handler = FolderSyncHandler(peer_addr, port)
    observer = Observer()
    observer.schedule(event_handler, LOCAL_FOLDER, recursive=True)
    observer.start()

    try:
        print("Sincronización iniciada. Presiona Ctrl+C para salir.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Cerrando sincronización...")
        observer.stop()
    observer.join()

main()