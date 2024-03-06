import socket
import threading
import ssl
import tkinter as tk

HEADER = 64
PORT = 5051
SERVER = "192.168.64.40"  # Change this to the IP address of your server
hostname='example.com'
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

CLIENT_CERTIFICATE = "D:\sem4\cn\cnwhiteboard\client.crt"
SERVER_CERTIFICATE = "D:\sem4\cn\cnwhiteboard\server.crt"

CLIENT_KEY = "D:\sem4\cn\cnwhiteboard\client.key"

# Create an SSL context for the client
#context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#context.load_cert_chain(certfile=CLIENT_CERTIFICATE)

# Create an SSL context for the server
context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=SERVER_CERTIFICATE)
context.load_cert_chain(certfile=CLIENT_CERTIFICATE,keyfile=CLIENT_KEY)
#server_context.load_verify_locations(cafile=SERVER_CERTIFICATE)

# Wrap the socket in an SSL context
client_socket = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM),server_side=False, server_hostname=hostname)
client_socket.connect(ADDR)


class Whiteboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Whiteboard")
        self.selected_color = "black"

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)

        self.last_x, self.last_y = None, None
        self.drawing_color = "black"
        self.eraser_mode = False

        self.color_buttons_frame = tk.Frame(self.root)
        self.color_buttons_frame.pack(side=tk.BOTTOM)

        colors = ["black", "red", "blue", "green", "yellow"]
        for color in colors:
            button = tk.Button(self.color_buttons_frame, bg=color, width=2, command=lambda c=color: self.set_color(c))
            button.pack(side=tk.LEFT)

        self.eraser_button = tk.Button(self.color_buttons_frame, text="Eraser", command=self.toggle_eraser)
        self.eraser_button.pack(side=tk.LEFT)

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            if self.eraser_mode:
                self.canvas.create_line(self.last_x, self.last_y, x, y, width=20, fill="white")
                send_data(f"ERASE|{self.last_x},{self.last_y}|{x},{y}")
            else:
                self.canvas.create_line(self.last_x, self.last_y, x, y, width=2, fill=self.selected_color)
                send_data(f"DRAW|{self.last_x},{self.last_y}|{x},{y}|{self.selected_color}")
        self.last_x, self.last_y = x, y

    def set_color(self, color):
        self.selected_color = color
        send_data(f"COLOR|{self.selected_color}")

    def toggle_eraser(self):
        self.eraser_mode = not self.eraser_mode
        if self.eraser_mode:
            self.eraser_button.config(relief=tk.SUNKEN)
        else:
            self.eraser_button.config(relief=tk.RAISED)
            self.selected_color = "black"


def send_data(data):
    message = data.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client_socket.send(send_length)
    client_socket.send(message)


def receive_data():
    while True:
        try:
            data = client_socket.recv(1024).decode(FORMAT)
            if data:
                print("Received data:", data)
                handle_data(data)
        except Exception as e:
            print("[ERROR] (receive data)", e)
            break


def handle_data(data):
    print("Received data:(handle data)", data)
    parts = data.split("|")
    if parts[0] == "DRAW":
        start_coords, end_coords, color = parts[1], parts[2], parts[3]
        start_x, start_y = map(int, start_coords.split(","))
        end_x, end_y = map(int, end_coords.split(","))
        whiteboard.canvas.create_line(start_x, start_y, end_x, end_y, width=2, fill=color)
    elif parts[0] == "ERASE":
        start_coords, end_coords = parts[1], parts[2]
        start_x, start_y = map(int, start_coords.split(","))
        end_x, end_y = map(int, end_coords.split(","))
        whiteboard.canvas.create_line(start_x, start_y, end_x, end_y, width=20, fill="white")
    elif parts[0] == "COLOR":
        whiteboard.selected_color = parts[1]
    elif data == "CONNECTED":
        print("Connected to server")
    else:
        print("Unknown data format:", data)


if __name__ == "__main__":
    root = tk.Tk()
    whiteboard = Whiteboard(root)

    receive_thread = threading.Thread(target=receive_data)
    receive_thread.daemon = True
    receive_thread.start()

    root.mainloop()

    send_data(DISCONNECT_MESSAGE)
