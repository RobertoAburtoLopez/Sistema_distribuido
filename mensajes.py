"""
===============================================================================
Nombre del programa : comunicación_nodos.py
Autor               : Aburto López Roberto 
Fecha de creación   : [10/04/2025]
Última modificación : [14/04/2025]
Descripción         : 
    Este programa implementa comunicación entre "n" nodos virtuales utilizando 
    sockets TCP. Cada nodo puede enviar y recibir mensajes de forma paralela 
    mediante programación con hilos (threading). Los mensajes incluyen la marca 
    de tiempo del nodo emisor y se almacenan tanto en el nodo que envía como 
    en el que recibe.

Características:
    - Envío de mensajes escritos por el usuario a otros nodos por IP.
    - Confirmación automática de recepción.
    - Almacenamiento local de todos los mensajes (enviados y recibidos).
    - Registro de tiempo del nodo emisor incluido en cada mensaje.
    - Conexiones concurrentes gestionadas con hilos.

Requisitos:
    - Python 3.x
    - Red local configurada (IP local accesible entre nodos)
    - Puertos abiertos para conexión entre nodos (por defecto: 65123)

Uso:
    Ejecutar este script en cada nodo participante.
    El usuario podrá ingresar la IP de destino y el mensaje a enviar.

Notas:
    Asegúrese de ejecutar todos los nodos antes de intentar enviar mensajes.
===============================================================================
"""


import socket
import threading
from datetime import datetime

HOST = "192.168.1.41"  # Direccion de loopback
PORT = 65123        # > 1023 (puerto escucha)
HEADER = 10

def guardar_mensaje(origen, mensaje, tipo="recibido"):
    with open(f"mensajes.txt", "a") as f:
        f.write(f"De [{origen}] [{tipo}]: {mensaje}\n")

def servidor():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print (f"Soy el nodo {HOST} . Esperando conexiones...")

    while True:
        conn, addr = s.accept()
        data_len = conn.recv(HEADER)
        
        data = conn.recv(int(data_len))
        mensaje = data.decode()

        print(f"[RECIBIDO] de {addr}: {mensaje}")
        guardar_mensaje(addr[0], mensaje, "recibido")

        conn.sendall("Recibido".encode())
        conn.close()



def cliente():
    while True:
        ip = input("IP destino o 'salir': ")
        if ip == "salir":
            break
        data = input("Mensaje a enviar: ")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje_con_hora = f"[{timestamp}] {data}"  # <-- Aquí se incluye la hora
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, PORT))
            
            strData = str(mensaje_con_hora)
            data_len = str(len(mensaje_con_hora))
            mensaje = f"{data_len:<{HEADER}}{strData}".encode()

            guardar_mensaje(ip, data, "enviado") 

            s.sendall(mensaje)

            respuesta = s.recv(8).decode() #el numero 8 es porque la palabra "recibido" son 8 letras
            print(f"[RESPUESTA]: {respuesta}")
            s.close()

        except Exception as e:
            print (f"[ERROR]: {e}")

threading.Thread(target=servidor, daemon=True).start() # En un hilo se pone el modo servidor

cliente() #Cliente es el hilo principal