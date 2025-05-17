import socket
import threading
from datetime import datetime

PORT = 65123
HEADER = 10

# Diccionario de nombres de nodos
NODOS = {
    "Roberto": "192.168.1.13",
    "Jimena": "192.168.1.30",
    "Michelle": "192.168.1.43",
    "Arturo": "192.168.1.44"
}

MI_NOMBRE = "Roberto"  # Cambia esto en cada computadora/nodo
HOST = NODOS[MI_NOMBRE]


def guardar_mensaje(origen, mensaje, tipo="recibido"):
    with open(f"mensajes.txt", "a") as f:
        f.write(f"[{origen}] [{tipo}]: {mensaje}\n")

def servidor():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Protocolo TCP IP
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Soy el nodo {MI_NOMBRE} ({HOST}). Esperando conexiones...")

    while True:
        conn, addr = s.accept()

        data_len = conn.recv(HEADER)
        data = conn.recv(int(data_len))
        mensaje = data.decode()

        ip_origen = addr[0]
        nombre_origen = next((nombre for nombre, ip in NODOS.items() if ip == ip_origen), ip_origen)

        print(f"[RECIBIDO] de {nombre_origen}: {mensaje}")
        guardar_mensaje(nombre_origen, mensaje, "recibido")

        # Respuesta de "recibido" con timestamp y nombre del nodo
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        respuesta = f"Recibido [{timestamp} {MI_NOMBRE}]"
        conn.sendall(respuesta.encode())
        conn.close()

def mostrar_menu():
    print("\n------ MENU ------")
    print("1. Enviar mensaje")
    print("2. Ver mensajes guardados")
    print("3. Salir")
    print("------------------")

def cliente():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opcion: ")

        if opcion == "1":
            print("Nodos disponibles:")
            for nombre, ip in NODOS.items():
                if nombre != MI_NOMBRE:
                    print(f"- {nombre} ({ip})")

            destino = input("Nombre del nodo destino: ")
            if destino not in NODOS or destino == MI_NOMBRE:
                print("[ERROR] Nodo invalido.")
                continue

            ip = NODOS[destino]
            data = input("Mensaje a enviar: ")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mensaje_con_hora = f"[{timestamp}] {data}"  # Mensaje con hora

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, PORT))

                strData = str(mensaje_con_hora)
                data_len = str(len(mensaje_con_hora))
                mensaje = f"{data_len:<{HEADER}}{strData}".encode('utf-8')

                guardar_mensaje(destino, data, "enviado")  # Guarda mensaje sin timestamp

                s.sendall(mensaje)

                respuesta = s.recv(1024).decode()  # Recibe respuesta completa
                print(f"[RESPUESTA]: {respuesta}")
                s.close()

            except Exception as e:
                print(f"[ERROR]: {e}")

        elif opcion == "2":
            try:
                with open("mensajes.txt", "r") as f:
                    print("\n--- Mensajes guardados ---")
                    print(f.read())
            except FileNotFoundError:
                print("[INFO] No hay mensajes guardados aun.")

        elif opcion == "3":
            print("Saliendo...")
            break
        else:
            print("[ERROR] Opcion invalida.")

# Inicia el servidor en un hilo
threading.Thread(target=servidor, daemon=True).start()

# Inicia el cliente en el hilo principal
cliente()
