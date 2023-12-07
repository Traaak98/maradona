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

# Head_yaw et head_pitch global
head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
camera_global = "front"
state = "searchBall"

verbose = True

# direction rotation tete
direction = 1
nb_tour = 0


def recv_data_ball(client, camera):
    # send request
    if camera == "front":
        client.sendall("REQUEST BALL FRONT")
    elif camera == "bottom":
        client.sendall("REQUEST BALL BOTTOM")
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


def searchBall():
    # Initialisation position tete
    global head_yaw, head_pitch, direction, nb_tour, camera_global, verbose

    if verbose:
        print "--- Search Ball ---"

    detect_, x, y, w, h = recv_data_ball(s, "bottom")
    if detect_:
        camera_global = "bottom"
        return "detectBall"

    detect_, x, y, w, h = recv_data_ball(s, "front")
    if detect_:
        # on reste sur la camera du haut
        camera_global = "front"

    if not detect_:
        # Check if we should change turn direction
        head_yaw = motion.getAngles("HeadYaw", True)[0]
        # Change direction if we are too close to the limit
        if abs(head_yaw * 180 / np.pi) > 118:
            direction *= -1
            nb_tour += 1
        if nb_tour > 2:
            head_pitch += 0.1
            nb_tour = 0
        # Turn head
        if verbose:
            print "Moving head : direction = ", direction * 0.1, "nb_tour = ", nb_tour
            print "head_yaw = ", head_yaw * 180 / np.pi, "head_pitch = ", head_pitch * 180 / np.pi
        control.headControl(motion, head_yaw + direction * 0.1, head_pitch, verbose=False)
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        return "noDetectBall"
    else:
        if verbose:
            print "camera gloabl = ", camera_global
            print "detect = ", detect_
            print "x = ", x
            print "y = ", y
            print "w = ", w
            print "h = ", h
            print "Found Ball"
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        return "detectBall"


def walkToBall():
    global head_yaw, head_pitch, camera_global, verbose, state

    if verbose:
        print "--- walk To Ball ---"

    control.headControl(motion, head_yaw, head_pitch, verbose=False)

    # Detect ball
    detect_, x, y, w, h = recv_data_ball(s, camera_global)
    if not detect_:
        return "noDetectBall"

    w_max = 60
    if verbose:
        print "Walk to ball"

    while w < w_max:
        detect_, x, y, w, h = recv_data_ball(s, camera_global)
        if not detect_:
            return "noDetectBall"
        err_x = nao_drv.image_width / 2 - x
        err_y = y - nao_drv.image_height / 2
        if abs(err_x) > 100 or abs(err_y) > 100:
            if verbose:
                print "Stop walking to center ball"
                print "align : err_x = ", err_x, " / err_y = ", err_y
            motion.stopMove()
            return "alignBall"
        else:
            if verbose:
                print "Marche en cours ; Taille balle : w = ", w
                print "Position balle : err_x = ", err_x, " / err_y = ", err_y
            vx, vy, vtheta = 0.5, 0, 0
            motion.moveToward(vx, vy, vtheta)
    motion.stopMove()
    state = "attainBall"
    return "attainBall"


def doWait():
    global verbose, head_yaw, head_pitch
    if verbose:
        print "--- Wait ---"
    time_dodo = 2
    motion.stopMove()
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # motion.rest()
    time.sleep(time_dodo)
    return "go"


def doStop():
    global verbose
    if verbose:
        print "--- Stop ---"
    motion.stopMove()
    motion.rest()
    event = None
    return event


def alignHead():
    global verbose, head_yaw, head_pitch, camera_global
    control.headControl(motion, head_yaw, head_pitch, verbose=False)

    if verbose:
        print "--- Align Head ---"

    # Center the ball in the image to align the head
    # Detect ball
    detect_, x, y, w, h = recv_data_ball(s, camera_global)
    err_x = nao_drv.image_width / 2 - x
    err_y = y - nao_drv.image_height / 2

    if not detect_:
        return "noDetectBall"

    if abs(err_x) > 20 or abs(err_y) > 15:
        yaw = 0.05 * err_x / nao_drv.image_width
        pitch = - 0.05 * err_y / nao_drv.image_height
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        if verbose:
            print "ALIGNING"
            print "Error head : err_x = ", err_x, " / err_y = ", err_y
            print "head_yaw = ", head_yaw * 180 / np.pi, " / head_pitch = ", head_pitch * 180 / np.pi
            print "yaw = ", yaw * 180 / np.pi, " / pitch = ", pitch * 180 / np.pi
        control.headControl(motion, head_yaw + yaw, head_pitch + pitch, verbose=False)
        time.sleep(0.05)
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        if verbose:
            print "head_yaw = ", head_yaw * 180 / np.pi, " / head_pitch = ", head_pitch * 180 / np.pi
        return "noAlignHeadDetectBall"
    else:
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        return "alignHeadDetectBall"


def alignBody():
    global head_yaw, head_pitch, camera_global, verbose, state
    control.headControl(motion, head_yaw, head_pitch, verbose=False)

    x, y, theta = motion.getRobotPosition(False)
    err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))
    if verbose:
        print "--- Align Body ---"
        print "Erreur angulaire : ", err_theta

    while err_theta * 180 / np.pi > 2:
        if verbose:
            print "ALIGN BODY"
            print "Erreur angulaire : ", err_theta * 180 / np.pi

        motion.moveTo(0, 0, 0.1 * np.sign(err_theta))
        x, y, theta = motion.getRobotPosition(False)
        err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))

    control.headControl(motion, 0, head_pitch, verbose=False)
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if verbose:
        print "Body aligned"
        print "____________________________________________________________________________"
    if state == "attainBall":
        return "attainBall"
    else:
        return "alignBodyDetectBall"


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
