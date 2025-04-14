===============================================================================
Nombre del programa : mensajes.py
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
