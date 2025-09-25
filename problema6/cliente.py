import socket
import threading

def recibir(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print(data.decode(), end='')
        except:
            break

def cliente():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 9000))

    threading.Thread(target=recibir, args=(sock,), daemon=True).start()

    try:
        while True:
            mensaje = input()
            if mensaje.lower() == '/salir':
                break
            sock.sendall(mensaje.encode())
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

if __name__ == '__main__':
    cliente()
