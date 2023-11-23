import socket
import time

import numpy as np
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
    ok = client.recv(4096)
    x = client.recv(4096)
    y = client.recv(4096)
    w = client.recv(4096)
    h = client.recv(4096)
    # client.sendall("BYE BYE")
    return ok, x, y, w, h


def search():
    # Get detect bool from image detection
    detect_, x, y, w, h = recv_data(s)
    direction = 1
    while not detect_:
        # Update image
        nao_drv.get_image()
        nao_drv.show_image(key=0.5)     # 0.5 s
        # Check if we should change turn direction
        head_yaw = motion.getAngles("HeadYaw", True)
        print "HeadYaw: ", head_yaw * 180 / np.pi
        if abs(head_yaw * 180 / np.pi) > 118:
            direction *= -1
        # Turn head
        control.headControl(motion, direction * 0.1, 0, verbose=False)
        time.sleep(0.1)
        # Detect ball
        detect_, x, y, w, h = recv_data(s)
        print "Detect: ", detect_
    return


def walk():
    # Get detect bool from image detection
    detect_, x, y, w, h = recv_data(s)
    while detect_:
        # Update image
        nao_drv.get_image()
        nao_drv.show_image(key=0.5)     # 0.5 s
        # Walk
        control.attain_ball(motion, x, y, w, h, verbose=False)
        # Detect ball
        detect_, x, y, w, h = recv_data(s)

    motion.stopMove()
    return


if __name__ == "__main__":

    search()
