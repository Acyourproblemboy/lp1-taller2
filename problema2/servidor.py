#!/usr/bin/env python3
"""
Problema 2: Comunicación bidireccional - Servidor
Objetivo: Crear un servidor TCP que devuelva exactamente lo que recibe del cliente
"""

import socket

# TODO: Definir la dirección y puerto del servidor
HOST = 'localhost'
PORT = 9000
# TODO: Crear un socket TCP/IP
# AF_INET: socket de familia IPv4
# SOCK_STREAM: socket de tipo TCP (orientado a conexión)
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# TODO: Enlazar el socket a la dirección y puerto especificados
servidor.bind((HOST, PORT))
# TODO: Poner el socket en modo escucha
servidor.listen()
# El parámetro define el número máximo de conexiones en cola

# Bucle infinito para manejar múltiples conexiones (una a la vez)
while True:

    print("Servidor a la espera de conexiones ...")
    
    # TODO: Aceptar una conexión entrante
    # accept() bloquea hasta que llega una conexión
    # conn: nuevo socket para comunicarse con el cliente
    # addr: dirección y puerto del cliente
    cliente, addr = servidor.accept()
    print(f"Conexión realizada por {addr}")

    # TODO: Recibir datos del cliente (hasta 1024 bytes)
    data = cliente.recv(1024)
    # Si no se reciben datos, salir del bucle
    if not data:
        break

    # Mostrar los datos recibidos (en formato bytes)
    print("Datos recibidos:", data)
    
    # TODO: Enviar los mismos datos de vuelta al cliente (echo)
    cliente.sendall(data)
    print("Datos enviados de vuelta al cliente.")
    # TODO: Cerrar la conexión con el cliente actual
    cliente.close()
