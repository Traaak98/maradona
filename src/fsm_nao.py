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

verbose = True

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


def search():
    detect_, x, y, w, h = recv_data_ball(s)
    direction = 1

    if not detect_:
        # Check if we should change turn direction
        head_yaw = motion.getAngles("HeadYaw", True)[0]
        # Change direction if we are too close to the limit
        if abs(head_yaw * 180 / np.pi) > 118:
            direction *= -1
        # Turn head
        if verbose:
            print "Moving head : direction = ", direction * 0.05
        control.headControl(motion, head_yaw + direction * 0.05, 0, verbose=False)
        return "noDetectBall"
    else:
        if verbose:
            print "detect = ", detect_
            print "x = ", x
            print "y = ", y
            print "w = ", w
            print "h = ", h
            print "Found Ball"
        return "detectBall"


def walk():
    # Get detect bool from image detection
    detect_, x, y, w, h = recv_data_ball(s)
    while detect_:
        # Update image
        nao_drv.get_image()
        nao_drv.show_image(key=1)     # 1 s
        # Walk
        control.attain_ball(motion, x, y, w, h, verbose=False)
        # Detect ball
        detect_, x, y, w, h = recv_data_ball(s)

    motion.stopMove()
    return


def alignHead():
    global verbose
    # Center the ball in the image to align the head
    detect_, x, y, w, h = recv_data_ball(s)
    err_x, err_y = 100, 100
    dt_loop = 0.05
    t0_loop = time.time()
    if not detect_:
        return "noDetectBall"

    if abs(err_x) > 5 or abs(err_y) > 5:
        err_x = nao_drv.image_width / 2 - x
        err_y = y - nao_drv.image_height / 2
        yaw = 0.05 * np.sign(err_x) # / nao_drv.image_width
        pitch = 0.05 * np.sign(err_y) # / nao_drv.image_height
        if verbose:
            print "Error head : err_x = ", err_x, " / err_y = ", err_y
            print "Moving head : yaw = ", yaw, " / pitch = ", pitch
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)

        control.headControl(motion, head_yaw + yaw, head_pitch + pitch, verbose=False)
        detect_, x, y, w, h = recv_data_ball(s)
        # # Waiting time
        # dt = dt_loop-(time.time()-t0_loop)
        # if dt > 0:
        #     time.sleep(dt)
        return "noAlignHeadDetectBall"
    else:
        print "Ball aligned"
        return "alignHeadDetectBall"


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
