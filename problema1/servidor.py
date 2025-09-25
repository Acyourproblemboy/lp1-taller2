#!/usr/bin/env python3
"""
Problema 1: Sockets básicos - Servidor
Objetivo: Crear un servidor TCP que acepte una conexión y intercambie mensajes básicos
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
# El parámetro define el número máximo de conexiones en cola
servidor.listen()
print("Servidor a la espera de conexiones ...")

# TODO: Aceptar una conexión entrante
# accept() bloquea hasta que llega una conexión
# conn: nuevo socket para comunicarse con el cliente
# addr: dirección y puerto del cliente
cliente, addr = servidor.accept()
print(f"Un cliente {cliente} se conecto desde la direccion {addr}")

# TODO: Recibir datos del cliente (hasta 1024 bytes)
datos = cliente.recv(1024)
# TODO: Enviar respuesta al cliente (convertida a bytes)
# sendall() asegura que todos los datos sean enviados
cliente.sendall(b"Hola! " + datos)
# TODO: Cerrar la conexión con el cliente
cliente.close()
