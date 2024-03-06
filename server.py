import socket
import threading
import ssl

HEADER = 64
PORT = 5051
SERVER =socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
CERTIFICATE = "D:\sem4\cn\cnwhiteboard\server.crt"
KEY = "D:\sem4\cn\cnwhiteboard\server.key"
CLIENT_CERTIFICATE = "D:\sem4\cn\cnwhiteboard\client.crt"


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# Wrap the socket in an SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=CERTIFICATE, keyfile=KEY)
context.load_verify_locations(cafile=CLIENT_CERTIFICATE)


clients = []

def broadcast(message):
    for client in clients:
        try:
            client.send(message.encode(FORMAT))
        except OSError:
            clients.remove(client)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    try:
        connected = True
        while connected:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)
                if msg == DISCONNECT_MESSAGE:
                    connected = False
                else:
                    broadcast(msg)
    except ConnectionResetError:
        pass

    conn.close()
    print(f"[DISCONNECTED] {addr} disconnected.")
    clients.remove(conn)

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        conn = context.wrap_socket(conn, server_side=True)
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {len(clients)}")

print("[STARTING] Server is starting...")
start()
