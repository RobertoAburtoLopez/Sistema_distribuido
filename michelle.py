import socket
import threading
import json
import os
import time
from datetime import datetime

PORT = 65123
HEADER = 10

# Diccionario de nodos y sus IPs
NODOS = {
    "Roberto": "192.168.62.135",
    "Jimena": "192.168.62.134",
    "Michelle": "192.168.62.136",
    "Arturo": "192.168.62.137"
}

# Pesos de prioridad (mayor = más alto)
PESOS = {
    "Michelle": 4,
    "Roberto": 3,
    "Jimena": 2,
    "Arturo": 1
}

MI_NOMBRE = "Michelle"  # Cambiar en cada nodo
HOST = NODOS[MI_NOMBRE]
MAESTRO = "Michelle"
coordinador_actual = MAESTRO  # Coordinador actual

inventario_file = "inventario.json"
clientes_file = "clientes.json"
guias_file = "guias.json"

PENDIENTES_DIR = "pendientes"
os.makedirs(PENDIENTES_DIR, exist_ok=True)

# ================= FUNCIONES UTILITARIAS =================

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def guardar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def cargar_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_mensaje(origen, mensaje, tipo="recibido"):
    with open("mensajes.txt", "a", encoding="utf-8") as f:
        f.write(f"[{origen}] [{tipo}]: {mensaje}\n")

def generar_serie():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def guardar_guia(id_articulo, sucursal, id_cliente):
    guias = cargar_json(guias_file)
    serie = generar_serie()
    guia = {
        "id_guia": f"{id_articulo}-{serie}-{sucursal}-{id_cliente}",
        "articulo": id_articulo,
        "cliente": id_cliente,
        "sucursal": sucursal,
        "serie": serie
    }
    guias.append(guia)
    guardar_json(guias_file, guias)
    print(f"\n[INFO] Guía generada: {guia['id_guia']}")

# =================== BULLY ALGORITHM =====================

def iniciar_eleccion():
    global coordinador_actual
    print(f"[BULLY] Iniciando elección desde {MI_NOMBRE}...")
    respuestas = []

    for nombre, ip in NODOS.items():
        if PESOS[nombre] > PESOS[MI_NOMBRE]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((ip, PORT))
                    msg = json.dumps({"tipo": "eleccion", "origen": MI_NOMBRE})
                    s.sendall(f"{len(msg):<{HEADER}}".encode() + msg.encode())
                    resp = s.recv(1024).decode()
                    if resp == "OK":
                        respuestas.append(nombre)
            except:
                continue

    if not respuestas:
        coordinador_actual = MI_NOMBRE
        notificar_nuevo_coordinador()
    else:
        print(f"[BULLY] Esperando al nodo con mayor peso a responder.")

def notificar_nuevo_coordinador():
    global coordinador_actual
    for nombre, ip in NODOS.items():
        if nombre == MI_NOMBRE:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, PORT))
                msg = json.dumps({
                    "tipo": "nuevo_coordinador",
                    "nombre": MI_NOMBRE,
                    "origen": MI_NOMBRE 
                })
                s.sendall(f"{len(msg):<{HEADER}}".encode() + msg.encode())
        except:
            continue
    print(f"[BULLY] Soy el nuevo coordinador: {MI_NOMBRE}")

def verificar_maestro():
    global coordinador_actual
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((NODOS[coordinador_actual], PORT))
            mensaje = json.dumps({"tipo": "ping"}).encode()
            s.sendall(f"{len(mensaje):<{HEADER}}".encode() + mensaje)
    except:
        print("[FALLO] Nodo maestro no responde. Iniciando elección...")
        iniciar_eleccion()


def distribuir_articulo_equitativamente(articulo):
    total = articulo["cantidad"]
    nodos_activos = [n for n in NODOS]
    cantidad_por_nodo = total // len(nodos_activos)

    for nodo in NODOS:
        articulo_repartido = dict(articulo)
        articulo_repartido["cantidad"] = cantidad_por_nodo
        if nodo == MI_NOMBRE:
            inventario = cargar_json(inventario_file)
            inventario = actualizar_o_agregar_articulo(inventario, articulo_repartido)
            guardar_json(inventario_file, inventario)
        else:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                    s2.connect((NODOS[nodo], PORT))
                    mensaje = json.dumps({
                        "tipo": "actualizar_inventario",
                        "articulo": articulo_repartido
                    }).encode()
                    s2.sendall(f"{len(mensaje):<{HEADER}}".encode() + mensaje)
                    print(f"[SYNC] Enviado a {nodo}: {articulo['nombre']}")
            except:
                print(f"[WARN] {nodo} está desconectado. Guardando pendiente.")
                guardar_pendiente(nodo, articulo_repartido)


def actualizar_o_agregar_articulo(inventario, articulo):
    for item in inventario:
        if item["id"] == articulo["id"]:
            item["cantidad"] += articulo["cantidad"]
            return inventario
    inventario.append(articulo)
    return inventario

def obtener_cantidad_local(articulo_id):
    inventario = cargar_json(inventario_file)
    for item in inventario:
        if item["id"] == articulo_id:
            return item["cantidad"]
    return 0


def propagar_cliente_a_nodos(cliente):
    for nodo in NODOS:
        if nodo != MI_NOMBRE:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((NODOS[nodo], PORT))
                mensaje = {
                    "tipo": "cliente_propagado",
                    "cliente": cliente
                }
                data = json.dumps(mensaje).encode()
                s.sendall(f"{len(data):<{HEADER}}".encode() + data)
                s.close()
            except Exception as e:
                print(f"[ERROR] No se pudo propagar a {nodo}: {e}")

def solicitar_stock_remoto(nombre_nodo, articulo_id):
    ip = NODOS[nombre_nodo]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        mensaje = json.dumps({
            "tipo": "consultar_stock",
            "id": articulo_id
        }).encode()
        s.connect((ip, PORT))
        s.sendall(f"{len(mensaje):<{HEADER}}".encode() + mensaje)
        data_len = s.recv(HEADER)
        data = s.recv(int(data_len))
        return int(data.decode())


def solicitar_clientes():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            mensaje = json.dumps({"tipo": "solicitar_clientes"}).encode()
            s.connect((NODOS[coordinador_actual], PORT))
            s.sendall(f"{len(mensaje):<{HEADER}}".encode() + mensaje)
            data_len = s.recv(HEADER)
            data = s.recv(int(data_len))
            clientes_recibidos = json.loads(data.decode())
            guardar_json(clientes_file, clientes_recibidos)
            print("[INFO] Clientes sincronizados al arrancar.")
    except Exception as e:
        print(f"[ERROR] No se pudo sincronizar clientes: {e}")

# ================== MONITOREO AUTOMÁTICO ==================

def monitor_maestro(intervalo=10):
    while True:
        time.sleep(intervalo)
        verificar_maestro()
# ==================== FUNCIONES SERVIDOR ======================

def servidor():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Soy el nodo {MI_NOMBRE} ({HOST}). Esperando conexiones...")

    while True:
        conn, addr = s.accept()
        try:
            data_len = conn.recv(HEADER)
            data = conn.recv(int(data_len))
            mensaje = data.decode()
            json_data = json.loads(mensaje)
            tipo = json_data.get("tipo")

            if tipo == "ping":
                conn.sendall("pong".encode())

            elif tipo == "eleccion":
                conn.sendall("OK".encode())
                iniciar_eleccion()
                
            elif tipo == "nuevo_coordinador":
                nuevo = json_data["nombre"]
                global coordinador_actual
                coordinador_actual = nuevo
                print(f"[COORDINADOR] El nuevo coordinador es: {nuevo}")

                if nuevo == MI_NOMBRE:
                    anterior = json_data.get("origen")
                    if anterior and anterior != MI_NOMBRE:
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                solicitud = json.dumps({
                                    "tipo": "transferencia_estado",
                                    "solicitante": MI_NOMBRE
                                }).encode()
                                s.connect((NODOS[anterior], PORT))
                                s.sendall(f"{len(solicitud):<{HEADER}}".encode() + solicitud)
                                print(f"[TRANSFERENCIA] Solicitando estado al coordinador anterior {anterior}...")
                        except Exception as e:
                            print(f"[ERROR] No se pudo solicitar estado: {e}")

            elif tipo == "transferencia_estado":
                solicitante = json_data["solicitante"]

                estado = {
                    "tipo": "estado_completo",
                    "clientes": cargar_json(clientes_file),
                    "pendientes": {}
                }

                for archivo in os.listdir(PENDIENTES_DIR):
                    nombre = archivo.replace(".json", "")
                    with open(os.path.join(PENDIENTES_DIR, archivo), "r") as f:
                        estado["pendientes"][nombre] = json.load(f)

                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                        s2.connect((NODOS[solicitante], PORT))
                        mensaje_estado = json.dumps(estado).encode()
                        s2.sendall(f"{len(mensaje_estado):<{HEADER}}".encode() + mensaje_estado)
                        print(f"[TRANSFERENCIA] Estado enviado a nuevo coordinador {solicitante}")
                except Exception as e:
                    print(f"[ERROR] No se pudo enviar estado: {e}")


            elif tipo == "estado_completo":
                guardar_json(clientes_file, json_data["clientes"])
                for nodo, pendientes in json_data["pendientes"].items():
                    with open(ruta_pendientes(nodo), "w") as f:
                        json.dump(pendientes, f, indent=4)
                print("[TRANSFERENCIA] Estado del sistema sincronizado tras asumir como coordinador.")


            elif tipo == "solicitar_clientes":
                clientes = cargar_json(clientes_file)
                respuesta = json.dumps(clientes).encode()
                conn.sendall(f"{len(respuesta):<{HEADER}}".encode() + respuesta)
                
            elif tipo == "consultar_stock":
                articulo_id = json_data["id"]
                cantidad = obtener_cantidad_local(articulo_id)
                respuesta = str(cantidad).encode()
                conn.sendall(f"{len(respuesta):<{HEADER}}".encode() + respuesta)

            elif tipo == "actualizar_inventario":
                if MI_NOMBRE == coordinador_actual:
                    print("[ACTUALIZADO] Repartiendo artículo recibido.")
                    distribuir_articulo_equitativamente(json_data["articulo"])
                else:
                    inventario = cargar_json(inventario_file)
                    inventario = actualizar_o_agregar_articulo(inventario, json_data["articulo"])
                    guardar_json(inventario_file, inventario)
                    print("[INFO] Artículo sincronizado desde el coordinador.")
                    
            elif tipo == "estado_completo":
                print("[TRANSFERENCIA] Recibiendo estado del coordinador anterior...")

                # Guardar clientes
                guardar_json(clientes_file, json_data["clientes"])

                # Guardar pendientes
                for nodo, pendientes in json_data["pendientes"].items():
                    with open(ruta_pendientes(nodo), "w") as f:
                        json.dump(pendientes, f, indent=4)

                print("[TRANSFERENCIA] Estado sincronizado. Asumiendo rol de coordinador.")

                    
            elif tipo == "nuevo_cliente":
                cliente = json_data["cliente"]
                if MI_NOMBRE == coordinador_actual:
                    clientes = cargar_json(clientes_file)
                    if not any(c["id"] == cliente["id"] for c in clientes):
                        clientes.append(cliente)
                        guardar_json(clientes_file, clientes)
                        print(f"[COORDINADOR] Cliente agregado: {cliente}")
                        propagar_cliente_a_nodos(cliente)
                    else:
                        print("[COORDINADOR] Cliente ya existe, no se agrega.")
                else:
                    print("[INFO] Nodo no coordinador ignoró nuevo_cliente.")
                    
            elif tipo == "cliente_propagado":
                cliente = json_data["cliente"]
                clientes = cargar_json(clientes_file)
                if not any(c["id"] == cliente["id"] for c in clientes):
                    clientes.append(cliente)
                    guardar_json(clientes_file, clientes)
                    print(f"[INFO] Cliente propagado recibido y registrado: {cliente}")
                else:
                    print("[INFO] Cliente ya estaba registrado, no se duplicó.")
                    
            elif tipo == "reconexion":
                nodo = json_data["nodo"]
                print(f"[INFO] Nodo reconectado: {nodo}")
                
                # Enviar clientes actualizados
                clientes = cargar_json(clientes_file)
                respuesta_clientes = json.dumps({
                    "tipo": "sync_clientes",
                    "clientes": clientes
                }).encode()
                conn.sendall(f"{len(respuesta_clientes):<{HEADER}}".encode() + respuesta_clientes)

                time.sleep(0.5)  # Evitar solapamiento de mensajes en buffer

                # Enviar inventario pendiente si lo hay
                pendientes = cargar_pendientes(nodo)

                if pendientes:
                    print(f"[SYNC] Enviando {len(pendientes)} artículos pendientes a {nodo}")
                    for id_, cantidad in pendientes.items():
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                                s2.connect((NODOS[nodo], PORT))
                                
                                inventario_global = cargar_json(inventario_file)
                                info = pendientes[id_]
                                nombre_articulo = info.get("nombre", f"Artículo {id_}")
                                cantidad = info["cantidad"]

                                articulo_sync = {
                                    "id": id_,
                                    "nombre": nombre_articulo,
                                    "cantidad": cantidad
                                }

                                mensaje_inv = json.dumps({
                                    "tipo": "actualizar_inventario",
                                    "articulo": articulo_sync
                                }).encode()
                                s2.sendall(f"{len(mensaje_inv):<{HEADER}}".encode() + mensaje_inv)
                                print(f"[SYNC] Enviado {cantidad} de {id_} a {nodo}")
                        except Exception as e:
                            print(f"[ERROR] No se pudo enviar {id_} a {nodo}: {e}")
                else:
                    print(f"[SYNC] No hay pendientes de inventario para {nodo}")
                borrar_pendientes(nodo)
            elif tipo == "sync_clientes":
                nuevos = json_data["clientes"]
                guardar_json(clientes_file, nuevos)
                print("[SYNC] Lista de clientes actualizada tras reconexión.")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            conn.close()
 

# =================== FUNCIONES DE CLIENTE =====================

def mostrar_menu():
    print(f"\n------ MENÚ {MI_NOMBRE.upper()} (Coordinador: {coordinador_actual}) ------")
    print("1. Comprar artículo")
    print("2. Ver clientes")
    print("3. Registrar cliente")
    print("4. Ver guías de envío")
    print("5. Ver inventario")
    print("6. Agregar artículo al maestro")
    print("7. Salir")

def cliente():
    while True:
        limpiar_pantalla()
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            verificar_maestro()
            comprar_articulo()
        elif opcion == "2":
            ver_clientes()
        elif opcion == "3":
            agregar_cliente()
        elif opcion == "4":
            ver_guias()
        elif opcion == "5":
            ver_inventario()
        elif opcion == "6":
            enviar_articulo_maestro()
        elif opcion == "7":
            break
        else:
            print("[ERROR] Opción inválida.")

# =================== FUNCIONES OPERATIVAS =====================

def ver_clientes():
    clientes = cargar_json(clientes_file)
    print("\n--- CLIENTES REGISTRADOS ---")
    if not clientes:
        print("No hay clientes.")
    for cli in clientes:
        print(f"- ID: {cli['id']}, Nombre: {cli['nombre']}")
    input("Presiona Enter para continuar...")

def agregar_cliente():
    clientes = cargar_json(clientes_file)
    nuevo_id = input("ID del nuevo cliente: ").strip()
    nombre = input("Nombre del cliente: ").strip()
    if any(cli["id"] == nuevo_id for cli in clientes):
        print("[ERROR] El ID ya existe.")
        return
    cliente = {"id": nuevo_id, "nombre": nombre}
    clientes.append(cliente)
    guardar_json(clientes_file, clientes)
    sincronizar_cliente(cliente)
    print("[OK] Cliente registrado y sincronizado.")

def sincronizar_cliente(cliente):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            mensaje = json.dumps({"tipo": "nuevo_cliente", "cliente": cliente}).encode()
            s.connect((NODOS[coordinador_actual], PORT))
            s.sendall(f"{len(mensaje):<{HEADER}}".encode() + mensaje)
    except:
        print("[WARN] No se pudo sincronizar con el coordinador.")

def obtener_cliente():
    clientes = cargar_json(clientes_file)
    if not clientes:
        print("[INFO] No hay clientes. Registra uno nuevo.")
        agregar_cliente()
        clientes = cargar_json(clientes_file)
    for i, cli in enumerate(clientes):
        print(f"{i+1}. {cli['nombre']} ({cli['id']})")
    print(f"{len(clientes)+1}. Registrar nuevo cliente")
    opcion = int(input("Opción: "))
    if opcion == len(clientes) + 1:
        agregar_cliente()
        return obtener_cliente()
    return clientes[opcion - 1]["id"]

def comprar_articulo():
    inventario = cargar_json(inventario_file)
    print("\n--- INVENTARIO DISPONIBLE ---")
    for art in inventario:
        print(f"- {art['id']} ({art['nombre']}) : {art['cantidad']} unidades")
    id_art = input("ID del artículo a comprar: ").strip()
    cliente = obtener_cliente()
    for art in inventario:
        if art["id"] == id_art and art["cantidad"] > 0:
            art["cantidad"] -= 1
            guardar_json(inventario_file, inventario)
            guardar_guia(id_art, HOST, cliente)
            print("[ÉXITO] Compra realizada.")
            break
    else:
        print("[ERROR] Artículo no encontrado o sin stock.")
    input("Presiona Enter para continuar...")

def ver_guias():
    guias = cargar_json(guias_file)
    print("\n--- GUÍAS DE ENVÍO ---")
    if not guias:
        print("No hay guías registradas.")
    for g in guias:
        print(f"{g['id_guia']} - Cliente: {g['cliente']} - Artículo: {g['articulo']}")
    input("Presiona Enter para continuar...")

def ver_inventario():
    inventario = cargar_json(inventario_file)
    print("\n--- INVENTARIO LOCAL ---")
    if not inventario:
        print("No hay artículos en el inventario.")
    for item in inventario:
        print(f"{item['id']} - {item['nombre']} : {item['cantidad']} unidades")
    input("Presiona Enter para continuar...")

def enviar_articulo_maestro():
    id_art = input("ID del artículo: ").strip()
    nombre = input("Nombre del artículo: ").strip()
    cantidad = int(input("Cantidad: "))
    articulo = {"id": id_art, "nombre": nombre, "cantidad": cantidad}
    mensaje_dict = {"tipo": "actualizar_inventario", "articulo": articulo}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            mensaje = json.dumps(mensaje_dict).encode()
            s.connect((NODOS[coordinador_actual], PORT))
            s.sendall(f"{len(mensaje):<{HEADER}}".encode() + mensaje)
            print(f"[OK] Artículo enviado al nodo coordinador.")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar el artículo: {e}")
    input("Presiona Enter para continuar...")
    
#================== Recuperacion de la informacion =======================
def anunciar_reconexion():
    if MI_NOMBRE == coordinador_actual:
        return  # Coordinador no se reconecta consigo mismo
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            mensaje = json.dumps({
                "tipo": "reconexion",
                "nodo": MI_NOMBRE
            }).encode()
            s.connect((NODOS[coordinador_actual], PORT))
            s.sendall(f"{len(mensaje):<{HEADER}}".encode() + mensaje)
    except Exception as e:
        print(f"[ERROR] No se pudo anunciar reconexión: {e}")
 
#====
def ruta_pendientes(nombre):
    return os.path.join(PENDIENTES_DIR, f"{nombre}.json")

def guardar_pendiente(nombre, articulo):
    ruta = ruta_pendientes(nombre)
    datos = {}
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            datos = json.load(f)
    id_ = articulo["id"]
    nombre_articulo = articulo["nombre"]

    if id_ in datos:
        datos[id_]["cantidad"] += articulo["cantidad"]
    else:
        datos[id_] = {
            "nombre": nombre_articulo,
            "cantidad": articulo["cantidad"]
        }

    with open(ruta, "w") as f:
        json.dump(datos, f, indent=4)


def cargar_pendientes(nombre):
    ruta = ruta_pendientes(nombre)
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            return json.load(f)
    return {}

def borrar_pendientes(nombre):
    ruta = ruta_pendientes(nombre)
    if os.path.exists(ruta):
        os.remove(ruta)


# =================== INICIO DEL SISTEMA =====================

if __name__ == "__main__":
    threading.Thread(target=servidor, daemon=True).start()
    time.sleep(2)
    solicitar_clientes()  #  Sincroniza lista de clientes al arrancar
    iniciar_eleccion()
    anunciar_reconexion()
    threading.Thread(target=monitor_maestro, daemon=True).start()
    cliente()