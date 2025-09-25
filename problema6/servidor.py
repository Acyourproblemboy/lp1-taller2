import socket
import threading
import json
import os

# Datos en memoria
usuarios = {}  # socket -> {'nombre': 'usuario', 'sala': 'nombre_sala'}
salas = {}     # nombre_sala -> [sockets]

ARCHIVO_SALAS = 'salas.json'

def cargar_salas():
    global salas
    if os.path.exists(ARCHIVO_SALAS):
        with open(ARCHIVO_SALAS, 'r') as f:
            datos = json.load(f)
            salas = {sala: [] for sala in datos.keys()}
    else:
        salas = {}

def guardar_salas():
    datos = {sala: [] for sala in salas}
    with open(ARCHIVO_SALAS, 'w') as f:
        json.dump(datos, f)

def manejar_cliente(conn, addr):
    conn.sendall(b'Escribe tu nombre de usuario: ')
    nombre = conn.recv(1024).decode().strip()
    usuarios[conn] = {'nombre': nombre, 'sala': None}
    conn.sendall(b'Bienvenido al chat! Usa /CREATE, /JOIN, /LEAVE, /MSG, /PM\n')

    while True:
        try:
            mensaje = conn.recv(1024).decode().strip()
            if not mensaje:
                break

            if mensaje.startswith('/CREATE'):
                _, nombre_sala = mensaje.split(maxsplit=1)
                if nombre_sala not in salas:
                    salas[nombre_sala] = []
                    conn.sendall(f'Sala {nombre_sala} creada.\n'.encode())
                    guardar_salas()
                else:
                    conn.sendall(f'Sala {nombre_sala} ya existe.\n'.encode())

            elif mensaje.startswith('/JOIN'):
                _, nombre_sala = mensaje.split(maxsplit=1)
                if nombre_sala in salas:
                    # Salir de la sala anterior
                    sala_anterior = usuarios[conn]['sala']
                    if sala_anterior and conn in salas[sala_anterior]:
                        salas[sala_anterior].remove(conn)
                        broadcast(sala_anterior, f'{usuarios[conn]["nombre"]} ha salido de la sala.\n')

                    # Unirse a la nueva
                    salas[nombre_sala].append(conn)
                    usuarios[conn]['sala'] = nombre_sala
                    conn.sendall(f'Te uniste a {nombre_sala}\n'.encode())
                    broadcast(nombre_sala, f'{usuarios[conn]["nombre"]} se ha unido a la sala.\n')
                else:
                    conn.sendall(b'Sala no existe.\n')

            elif mensaje.startswith('/LEAVE'):
                sala = usuarios[conn]['sala']
                if sala:
                    salas[sala].remove(conn)
                    broadcast(sala, f'{usuarios[conn]["nombre"]} ha salido de la sala.\n')
                    usuarios[conn]['sala'] = None
                    conn.sendall(b'Salida de la sala exitosa.\n')
                else:
                    conn.sendall('No estás en ninguna sala.\n'.encode('utf-8'))

            elif mensaje.startswith('/MSG'):
                _, msg = mensaje.split(' ', 1)
                sala = usuarios[conn]['sala']
                if sala:
                    broadcast(sala, f'{usuarios[conn]["nombre"]}: {msg}\n', conn)
                else:
                    conn.sendall(b'Debes unirte a una sala para enviar mensajes.\n')

            elif mensaje.startswith('/PM'):
                _, destinatario, msg = mensaje.split(' ', 2)
                enviado = False
                for sock, data in usuarios.items():
                    if data['nombre'] == destinatario:
                        sock.sendall(f'[PM de {usuarios[conn]["nombre"]}]: {msg}\n'.encode())
                        enviado = True
                        break
                if not enviado:
                    conn.sendall(b'Usuario no encontrado.\n')

            else:
                conn.sendall(b'Comando no reconocido.\n')
        except:
            break

    # Desconectar
    sala = usuarios[conn]['sala']
    if sala and conn in salas[sala]:
        salas[sala].remove(conn)
        broadcast(sala, f'{usuarios[conn]["nombre"]} ha salido del chat.\n')
    print(f'{usuarios[conn]["nombre"]} desconectado.')
    del usuarios[conn]
    conn.close()

def broadcast(sala, mensaje, emisor=None):
    for cliente in salas[sala]:
        if cliente != emisor:
            try:
                cliente.sendall(mensaje.encode())
            except:
                pass

def iniciar_servidor(host='localhost', puerto=9000):
    cargar_salas()
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, puerto))
    servidor.listen()
    print(f'Servidor escuchando en {host}:{puerto}')

    try:
        while True:
            conn, addr = servidor.accept()
            print(f'Conexión de {addr}')
            threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print('Apagando servidor...')
        guardar_salas()
        servidor.close()

if __name__ == '__main__':
    iniciar_servidor()
