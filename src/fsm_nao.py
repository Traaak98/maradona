import socket
import time
import fsm
import logging as log

import numpy as np
import control_head as control

# Initialisation fsm
f = fsm.fsm()

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


def search():
    # Get detect bool from image detection
    print "Client request"
    detect_, x, y, w, h = recv_data(s)
    print "detect = ", detect_
    print "x = ", x
    print "y = ", y
    print "w = ", w
    print "h = ", h
    print "Answer received"

    direction = 1
    while not detect_:
        # Update image
        nao_drv.get_image()
        nao_drv.show_image(key=1)     # 1 s
        # Check if we should change turn direction
        head_yaw = motion.getAngles("HeadYaw", True)[0]
        print "HeadYaw: ", head_yaw * 180 / np.pi
        # Change direction if we are too close to the limit
        if abs(head_yaw * 180 / np.pi) > 118:
            direction *= -1
        # Turn head
        print "motion = ", motion
        print "direction = ", direction*0.1
        control.headControl(motion, head_yaw + direction * 0.1, 0, verbose=True)
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
        nao_drv.show_image(key=1)     # 1 s
        # Walk
        control.attain_ball(motion, x, y, w, h, verbose=False)
        # Detect ball
        detect_, x, y, w, h = recv_data(s)

    motion.stopMove()
    return


if __name__ == "__main__":
    # Config fichier log
    log.basicConfig(filename="turn_review.log", format='%(asctime)s %(levelname)s: %(message)s  ', level=log.DEBUG)
    log.debug("_______________GO_______________")

    # load fsm definition from a text file
    f.load_fsm_from_file("fsm.txt")

    # fsm loop
    run = True
    while (run):
        funct = f.run()  # function to be executed in the new state
        if f.curState != f.endState:
            newEvent = funct()  # new event when state action is finished
            print("New Event : ", newEvent)
            if newEvent is None:
                break
            else:
                f.set_event(newEvent)  # set new event for next transition
        else:
            funct()
            run = False

    log.debug("_______________END_______________")

    print("End of the programm")
