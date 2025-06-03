@@ -0,0 +1,93 @@

# Sistema Distribuido de Inventario y Logística

Este proyecto implementa un sistema distribuido de inventario y logística utilizando Python y sockets TCP. Permite el registro y sincronización de clientes, la distribución automática de artículos, compras con exclusión mutua, generación de guías de envío, y un algoritmo de elección de nodo maestro en caso de fallo.

---

## 📦 Estructura del Proyecto

```
/proyecto
├── nodo_michelle.py        # Nodo maestro
├── nodo_roberto.py         # Nodo sucursal
├── nodo_jimena.py          # Nodo sucursal
├── nodo_arturo.py          # Nodo sucursal
├── clientes.json           # Lista distribuida de clientes
├── inventario.json         # Inventario local de sucursal
├── inventario_maestro.json# Inventario del nodo maestro
├── guias.json              # Guías de envío generadas por cada compra
├── estado.json             # Estado de bloqueo para exclusión mutua
├── fallas.log              # Registro de fallas detectadas por el maestro
```

---

## 🚀 Instrucciones de uso

### 1. Clona este repositorio en cada nodo (máquina virtual)

```bash
git clone <REPO_URL>
cd proyecto
```

> Asegúrate de editar `MI_NOMBRE` en cada archivo `.py` según el nodo que se ejecuta (Michelle, Roberto, Jimena o Arturo).

---

### 2. Ejecuta primero el nodo maestro (Roberto)

```bash
python3 roberto.py
```

---

### 3. Luego ejecuta los nodos sucursales (en sus respectivas máquinas)

```bash
python3 michelle.py
python3 jimena.py
python3 arturo.py
```

---

## 🧪 Funcionalidades por nodo

### Nodo Maestro (Roberto)
- Distribuye artículos entre sucursales.
- Sincroniza clientes.
- Coordina exclusión mutua.
- Detecta fallos y ejecuta elecciones.

### Nodos Sucursal (Arturo, Michelle, Jimena, Roberto)
- Comprar artículos con control de concurrencia.
- Ver, agregar y sincronizar clientes.
- Ver inventario y guías de envío.
- Enviar artículos al maestro para distribución.

---

## 📝 Requisitos
- Python 3.x
- Red local configurada (mismo rango de IP)
- Puerto TCP 65123 habilitado entre nodos

---

## 🔄 Algoritmo de Elección
Si Roberto falla, los nodos ejecutan el algoritmo de bully y eligen un nuevo coordinador automáticamente.

---

## ✍️ Autores
- Roberto Aburto, Jimena Hernández, Michelle Barrios, Arturo Ciriaco
- Proyecto Final de Sistemas Distribuidos

---

## 📁 Inicialización de archivos
Incluye archivos `.json` vacíos iniciales como `clientes.json`, `guias.json`, `inventario.json`, etc.
Add comment
