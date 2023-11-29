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


def recv_data_ball(client):
    # send request
    client.sendall("REQUEST BALL")
    # receive and store data
    message = client.recv(4096)
    message.decode()
    message = message.split(";")
    ok = int(message[0])
    x = float(message[1])
    y = float(message[2])
    w = float(message[3])
    h = float(message[4])
    # client.sendall("BYE BYE")
    return ok, x, y, w, h


def search(verbose=False):
    # Get detect bool from image detection
    detect_, x, y, w, h = False, 0, 0, 0, 0
    direction = 1

    while not detect_:
        # Check if we should change turn direction
        head_yaw = motion.getAngles("HeadYaw", True)[0]
        # Change direction if we are too close to the limit
        if abs(head_yaw * 180 / np.pi) > 118:
            direction *= -1

        # Turn head
        if verbose:
            print "Moving head : direction = ", direction * 0.05
        control.headControl(motion, head_yaw + direction * 0.05, 0, verbose=False)
        # Detect ball
        detect_, x, y, w, h = recv_data_ball(s)

    if verbose:
        print "detect = ", detect_
        print "x = ", x
        print "y = ", y
        print "w = ", w
        print "h = ", h
        print "Answer received"
    return


def walk():
    # Get detect bool from image detection
    w_image, h_image = 320, 240
    detect_, x, y, w, h = recv_data_ball(s)
    while detect_:
        # Update image
        nao_drv.get_image()
        nao_drv.show_image(key=1)     # 1 s
        # Walk
        control.attain_ball(motion, x, y, w_image, h_image, verbose=False)
        # Detect ball
        detect_, x, y, w, h = recv_data_ball(s)

    motion.stopMove()
    return


if __name__ == "__main__":
    search()
