import socket
import time
import fsm

import numpy as np
import control_utils as control
import pickle

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

# Variables globales
head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
camera_global = "front"
verbose = True
state = None

# direction rotation tete pour searchBall
direction = 1
nb_tour = 0


def searchBall():
    # Initialisation position tete
    global direction, nb_tour, camera_global, verbose, state, head_yaw, head_pitch
    state = "searchBall"

    detect_, x, y, w, h = control.recv_data_ball(s, "bottom")
    if detect_:
        camera_global = "bottom"
        if verbose:
            print "camera gloabl = ", camera_global
            print "detect = ", detect_
            print "x = ", x
            print "y = ", y
            print "w = ", w
            print "h = ", h
            print "Found Ball"
        return "detectBall"

    detect_, x, y, w, h = control.recv_data_ball(s, "front")
    if detect_:
        camera_global = "front"
        if verbose:
            print "camera gloabl = ", camera_global
            print "detect = ", detect_
            print "x = ", x
            print "y = ", y
            print "w = ", w
            print "h = ", h
            print "Found Ball"
        return "detectBall"

    if not detect_:
        # Check if we should change turn direction
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        # Change direction if we are too close to the limit
        if abs(head_yaw * 180 / np.pi) > 118:
            direction *= -1
            nb_tour += 1
        if nb_tour > 2:
            head_pitch += 0.1
            nb_tour = 0
        # Turn head
        if verbose:
            print "--- Search Ball ---"
            print "Moving head : direction = ", direction * 0.1, "nb_tour = ", nb_tour
            print "head_yaw = ", head_yaw * 180 / np.pi, "head_pitch = ", head_pitch * 180 / np.pi
        control.headControl(motion, head_yaw + direction * 0.1, head_pitch, verbose=False)
        # head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        return "noDetectBall"


def walkToBall():
    global camera_global, verbose, state    #, head_yaw, head_pitch
    state = "walkToBall"
    # control.headControl(motion, head_yaw, head_pitch, verbose=False)

    # Detect ball
    detect_, x, y, w, h = control.recv_data_ball(s, camera_global)
    if not detect_:
        return "noDetectBall"
    w_max = 50

    while w < w_max:
        detect_, x, y, w, h = control.recv_data_ball(s, camera_global)
        if not detect_:
            motion.stopMove()
            return "noDetectBall"
        err_x = nao_drv.image_width / 2 - x
        err_y = nao_drv.image_height / 2 - y
        vx, vy, vtheta = 1, 0, 0
        # Si on est decentres en x
        if abs(err_x) > 10:
            vtheta = 0.1 * np.sign(err_x)
        # Si la balle est trop basse dans l'image
        if y < 15:
            pitch = 0.05 * err_y / nao_drv.image_height
            head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
            if verbose:
                print "Balle trop basse, pencher la tete"
                print "y = ", y, "pitch = ", (head_pitch + pitch) * 180 / np.pi
            control.headControl(motion, head_yaw + 0, head_pitch + pitch, verbose=False)
        # if abs(err_x) > 100 or abs(err_y) > 100:
        #     if verbose:
        #         print "Stop walking to center ball"
        #         print "align : err_x = ", err_x, " / err_y = ", err_y
        #     motion.stopMove()
        #     return "alignBall"
        if verbose:
            print "--- Walk to Ball ---"
            print "Marche en cours ; Taille balle : w = ", w
            print "Position balle : err_x = ", err_x, " / err_y = ", err_y
            print "Vitesse : v = [", vx, vy, vtheta, "]"
        motion.moveToward(vx, vy, vtheta)
    motion.stopMove()
    return "attainBall"


def doWait():
    global verbose
    if verbose:
        print "--- Wait ---"
    time_dodo = 2
    motion.stopMove()
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
    global verbose, camera_global, state    #, head_yaw, head_pitch
    state = "alignHead"

    # Center the ball in the image to align the head
    # Detect ball
    detect_, x, y, w, h = control.recv_data_ball(s, camera_global)
    err_x = nao_drv.image_width / 2 - x
    err_y = nao_drv.image_height / 2 - y

    if not detect_:
        return "noDetectBall"

    if abs(err_x) > 20 or abs(err_y) > 15:
        yaw = 0.05 * err_x / nao_drv.image_width
        pitch = 0.05 * err_y / nao_drv.image_height
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        if verbose:
            print "--- Align Head ---"
            print "Error head : err_x = ", err_x, " / err_y = ", err_y
            print "head_yaw = ", head_yaw * 180 / np.pi, " / head_pitch = ", head_pitch * 180 / np.pi
        control.headControl(motion, head_yaw + yaw, head_pitch + pitch, verbose=False)
        # time.sleep(0.05)
        # head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        # if verbose:
        #     print "head_yaw = ", head_yaw * 180 / np.pi, " / head_pitch = ", head_pitch * 180 / np.pi
        return "noAlignHeadDetectBall"
    else:
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        print "ALIGN HEAD : head_yaw = ", head_yaw * 180 / np.pi
        return "alignHeadDetectBall"


def alignBody():
    global camera_global, verbose, state    #, head_yaw, head_pitch
    state = "alignBody"
    # control.headControl(motion, head_yaw, head_pitch, verbose=False)

    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    print "ALIGN BODY : head_yaw = ", head_yaw * 180 / np.pi

    x, y, theta0 = motion.getRobotPosition(False)
    print "theta = ", theta0 * 180 / np.pi
    err_theta = 2 * np.arctan(np.tan(head_yaw / 2))
    # print "--- Align Body ---"
    # print "err_theta = ", err_theta * 180 / np.pi
    # print "head_yaw = ", head_yaw * 180 / np.pi
    # print "head_pitch = ", head_pitch * 180 / np.pi
    # print "theta = ", theta * 180 / np.pi

    while abs(err_theta * 180 / np.pi) > 5:
        if verbose:
            print "--- Align Body ---"
            print "Erreur angulaire : ", err_theta * 180 / np.pi

        motion.moveTo(0, 0, 0.1 * np.sign(err_theta))
        x, y, theta = motion.getRobotPosition(False)
        err_theta = 2 * np.arctan(np.tan((theta0 + head_yaw - theta) / 2))

    control.headControl(motion, 0, head_pitch, verbose=False)
    # head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)

    return "alignBodyDetectBall"


def turnArround():
    global state, verbose
    state = "turnArround"

    if verbose:
        print "TURNING AROUND"

    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    print "head_yaw = ", head_yaw * 180 / np.pi
    control.align_x(motion, nao_drv, s, camera_global, head_yaw, head_pitch, verbose=verbose)
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    print "head_yaw = ", head_yaw * 180 / np.pi
    control.alignBody_end(motion, head_yaw, head_pitch, verbose=verbose)
    print "head_yaw = ", head_yaw * 180 / np.pi
    control.headControl(motion, 0, 0, verbose=False)

    if verbose:
        print "BODY GOOD"

    # On tourne autour de la balle tant que le but n'est pas detecte et centre :
    while not control.searchGoal(s, verbose=verbose):
        if verbose:
            print "MOVE"
        vx = 0
        vy = -0.6
        vtheta = 0.06
        motion.move(vx, vy, vtheta)
        x, y, theta = motion.getRobotPosition(False)
        if verbose:
            print "Position : ", x, y, theta

    motion.stopMove()
    if verbose:
        print "END TURNING AROUND"
    return "detectGoal"


def doShoot():
    global verbose, state
    state = "shoot"
    if verbose:
        print "SHOOT"
    # verifier alignement corps / balle
    motion.move(5, 0, 0)
    t_stop = 11
    time.sleep(t_stop)
    return "goal"


if __name__ == "__main__":

    # load fsm definition from a text file
    f.load_fsm_from_file("fsm.txt")

    # fsm loop
    run = True
    while run:
        funct = f.run()  # function to be executed in the new state
        if f.curState != f.endState:
            newEvent = funct()  # new event when state action is finished
            print " ** New Event : ", newEvent, " ** "
            if newEvent is None:
                break
            else:
                f.set_event(newEvent)  # set new event for next transition
        else:
            funct()
            run = False

    print("End of the programm")
