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

verbose = True

# direction rotation tete
direction = 1
nb_tour = 0

def recv_data_ball(client, camera):
    # send request
    if camera == "front":
        print "FRONT"
        client.sendall("REQUEST BALL FRONT")
    elif camera == "bottom":
        print "BOTTOM"
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
    if verbose:
        print "--- Search Ball ---"

    # Initialisation position tete
    global head_yaw, head_pitch, direction, nb_tour
    control.headControl(motion, head_yaw, head_pitch, verbose=False)

    # Detect Ball
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if head_pitch * 180 / np.pi < 24:
        detect_, x, y, w, h = recv_data_ball(s, "front")
    else:
        detect_, x, y, w, h = recv_data_ball(s, "bottom")
    if not detect_:
        detect_, x, y, w, h = recv_data_ball(s, "bottom")

    if not detect_:
        # Check if we should change turn direction
        head_yaw = motion.getAngles("HeadYaw", True)[0]
        # Change direction if we are too close to the limit
        if abs(head_yaw * 180 / np.pi) > 118:
            direction *= -1
        # Change pitch if we have done 2 turns
        if nb_tour > 2:
            head_pitch += 0.1
            nb_tour = 0
        # Turn head
        if verbose:
            print "Moving head : direction = ", direction * 0.05
        control.headControl(motion, head_yaw + direction * 0.05, head_pitch, verbose=False)
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
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
    global head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)

    # Get detect bool from image detection
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if head_pitch * 180 / np.pi > 24:
        detect_, x, y, w, h = recv_data_ball(s, "bottom")
    else:
        detect_, x, y, w, h = recv_data_ball(s, "front")
    while detect_:
        # Update image
        nao_drv.get_image()
        nao_drv.show_image(key=1)  # 1 s
        # Walk
        control.attain_ball(motion, x, y, w, h, verbose=False)
        # Detect ball
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        if head_pitch * 180 / np.pi > 24:
            detect_, x, y, w, h = recv_data_ball(s, "bottom")
        else:
            detect_, x, y, w, h = recv_data_ball(s, "front")
    motion.stopMove()
    return

def doWait():
    time_dodo = 5
    motion.stopMove()
    control.headControl(motion, 0, 0, verbose=False)
    motion.rest()
    time.sleep(time_dodo)
    event = "go"
    return event


def doStop():
    motion.stopMove()
    motion.rest()
    event = None
    return event


def alignHead():
    global verbose, head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    if verbose:
        print "--- Align Head ---"

    # Center the ball in the image to align the head
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if head_pitch * 180 / np.pi > 24:
        detect_, x, y, w, h = recv_data_ball(s, "bottom")
    else:
        detect_, x, y, w, h = recv_data_ball(s, "front")
    err_x = nao_drv.image_width / 2 - x
    err_y = y - nao_drv.image_height / 2

    if not detect_:
        return "noDetectBall"
    if abs(err_x) > 12 or abs(err_y) > 10:
        yaw = 0.05 * err_x / nao_drv.image_width
        pitch = - 0.05 * err_y / nao_drv.image_height
        if verbose:
            print "Error head : err_x = ", err_x, " / err_y = ", err_y
            print "Moving head : yaw = ", yaw, " / pitch = ", pitch
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)

        control.headControl(motion, head_yaw + yaw, head_pitch + pitch, verbose=False)
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        return "noAlignHeadDetectBall"
    else:
        return "alignHeadDetectBall"


def alignBody():
    global head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # Tourner le corps du meme angle que la tete
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    x, y, theta = motion.getRobotPosition(False)
    err_theta = 2*np.arctan(np.tan((head_yaw - theta)/2))
    if verbose:
        print "--- Align Body ---"
        print "Erreur angulaire : ", err_theta

    while err_theta * 180 / np.pi > 5:
        # print "Robot Position: ", theta * 180 / np.pi, ", ", head_yaw * 180 / np.pi
        err_theta = 2 * np.arctan(np.tan((head_yaw - theta)/2))
        # print "Error theta: ", err_theta
        if verbose:
            print "Erreur angulaire : ", err_theta * 180 / np.pi
        motion.moveTo(0, 0, theta + err_theta)
        x, y, theta = motion.getRobotPosition(False)

    control.headControl(motion, 0, head_pitch, verbose=False)
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if head_pitch * 180 / np.pi > 24:
        detect_, x, y, w, h = recv_data_ball(s, "bottom")
    else:
        detect_, x, y, w, h = recv_data_ball(s, "front")

    if not detect_:
        if verbose:
            print "We lost the ball while turning the body"
        return "noDetectBall"
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
