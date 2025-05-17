import os
import socket
import threading
from datetime import datetime

PORT = 65123
HEADER = 10

# Diccionario de nombres de nodos
NODOS = {
    "Roberto": "192.168.62.135",
    "Jimena": "192.168.62.134",
    "Michelle": "192.168.62.136",
    "Arturo": "192.168.62.137"
}

MI_NOMBRE = "Roberto"  # Cambia esto en cada computadora/nodo
HOST = NODOS[MI_NOMBRE]


# ───────────────────────── UTILIDADES ──────────────────────────

def clear():
    """Limpia la consola de forma portable (Windows/Linux/Mac)."""
    os.system("cls" if os.name == "nt" else "clear")


def guardar_mensaje(origen: str, mensaje: str, tipo: str = "recibido") -> None:
    with open("mensajes.txt", "a", encoding="utf-8") as f:
        f.write(f"[{origen}] [{tipo}]: {mensaje}\n")


# ─────────────────────────── SERVIDOR ──────────────────────────

def servidor() -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Protocolo TCP/IP
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Soy el nodo {MI_NOMBRE} ({HOST}).\nEsperando conexiones...\n")

    while True:
        conn, addr = s.accept()
        try:
            data_len = conn.recv(HEADER)
            if not data_len:
                continue
            data = conn.recv(int(data_len))
            mensaje = data.decode()

            ip_origen = addr[0]
            nombre_origen = next((n for n, ip in NODOS.items() if ip == ip_origen), ip_origen)

            print(f"\n[RECIBIDO] de {nombre_origen}: {mensaje}\n")
            guardar_mensaje(nombre_origen, mensaje, "recibido")

            # Respuesta de "recibido" con timestamp y nombre del nodo
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            respuesta = f"Recibido [{timestamp} {MI_NOMBRE}]"
            conn.sendall(respuesta.encode())
        finally:
            conn.close()


# ─────────────────────────── CLIENTE ──────────────────────────

def mostrar_menu() -> None:
    print("+" + "-" * 28 + "+")
    print("| {:^26} |".format("MENÚ PRINCIPAL"))
    print("+" + "-" * 28 + "+")
    print("| 1) Enviar mensaje           |")
    print("| 2) Ver mensajes guardados    |")
    print("| 3) Salir                     |")
    print("+" + "-" * 28 + "+")


def cliente() -> None:
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            clear()
            print("─" * 50)
            print("Nodos disponibles:")
            for nombre, ip in NODOS.items():
                if nombre != MI_NOMBRE:
                    print(f"- {nombre} ({ip})")
            print("─" * 50)

            destino = input("Nombre del nodo destino: ").strip()
            if destino not in NODOS or destino == MI_NOMBRE:
                print("[ERROR] Nodo inválido.\n")
                continue

            ip = NODOS[destino]
            data = input("Mensaje a enviar: ").strip()
            if not data:
                print("[WARN] Mensaje vacío.\n")
                continue

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mensaje_con_hora = f"[{timestamp}] {data}"

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, PORT))
                    data_len = f"{len(mensaje_con_hora):<{HEADER}}"
                    s.sendall(f"{data_len}{mensaje_con_hora}".encode())

                    guardar_mensaje(destino, data, "enviado")

                    respuesta = s.recv(1024).decode()
                    print(f"\n[RESPUESTA] {respuesta}\n")
            except Exception as e:
                print(f"[ERROR] {e}\n")

        elif opcion == "2":
            clear()
            print("\n--- Mensajes guardados ---\n")
            try:
                with open("mensajes.txt", "r", encoding="utf-8") as f:
                    contenido = f.read().strip() or "(vacío)"
                    print(contenido)
            except FileNotFoundError:
                print("(aún no hay mensajes)")
            print("\n" + "─" * 50 + "\n")
            input("Presiona Enter para volver al menú...")
            clear()

        elif opcion == "3":
            print("Saliendo... ¡Hasta luego!")
            break
        else:
            print("[ERROR] Opción inválida.\n")


# ─────────────────────────── INICIO ───────────────────────────

if __name__ == "__main__":
    # Inicia el servidor en un hilo
    threading.Thread(target=servidor, daemon=True).start()

    # Limpia pantalla antes de empezar
    clear()

    # Inicia el cliente en el hilo principal
    cliente()
