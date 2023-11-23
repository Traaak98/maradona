import socket
import control_head as control


# Voir comment lancer automatiquement le serveur de detection
# Reception des donnes envoyees par la detection
yolo_host, yolo_port = '127.0.0.1', 6666
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((yolo_host, yolo_port))


def recv_data(client):
    # send request
    client.sendall("REQUEST BALL")
    # receive and store data
    answer = client.recv(4096)
    # booleen de detection, position, largeur et hauteur de la balle
    ok, x, y, w, h = answer.split(" ")
    return ok, x, y, w, h


def search():
    # Get detect bool from image detection
    detect_, x, y, w, h = recv_data(s)
    while not detect_:
        # Turn head
        control.headControl(0.2, 0, verbose=False)
        # Detect ball
        detect_, x, y, w, h = recv_data(s)
    return


if __name__ == "__main__":

    search()
