import socket
import control_head as control


# Voir comment lancer automatiquement le serveur de detection
# Reception des donnes envoyees par la detection
yolo_host, yolo_port = '127.0.0.1', 6666
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((yolo_host, yolo_port))

# Possibilite de initialiser tout ca de maniere plus propre avec une classe ou jsp
# set default IP nd port on simulated robot
robot_ip = "localhost"
robot_port = 11212
motion = control.wakeUp(robot_ip, robot_port)

# Faire tourner la camera en arriere plan en permanence !
nao_drv = control.openEyes(robot_ip, robot_port)


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
        # Update image
        nao_drv.get_image()
        nao_drv.show_image(key=0.5)     # 0.5 s
        # Turn head
        control.headControl(motion, 0.2, 0, verbose=False)
        # Detect ball
        detect_, x, y, w, h = recv_data(s)
    return


if __name__ == "__main__":

    search()
