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

# Head_yaw et head_pitch global
head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
camera_global = "front"


def recv_data_ball(client, camera):
    # send request
    if camera == "front":
        # print "FRONT"
        client.sendall("REQUEST BALL FRONT")
    elif camera == "bottom":
        # print "BOTTOM"
        client.sendall("REQUEST BALL BOTTOM")
    # receive and store data
    message = client.recv(4096)
    # print "message received "
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
    global camera_global, head_yaw, head_pitch
    # control.headControl(motion, head_yaw, head_pitch, verbose=False)
    detect_, x, y, w, h = False, 0, 0, 0, 0
    direction = 1
    nb_tour = 0

    while not detect_:
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
            print "SEARCHING"
            print "Moving head : direction = ", direction * 0.1, "nb_tour = ", nb_tour
            print "head_yaw = ", head_yaw * 180 / np.pi, "head_pitch = ", head_pitch * 180 / np.pi
        control.headControl(motion, head_yaw + direction * 0.1, head_pitch, verbose=False)

        detect_, x, y, w, h = recv_data_ball(s, "bottom")
        if detect_:
            camera_global = "bottom"
            break

        detect_, x, y, w, h = recv_data_ball(s, "front")
        if detect_:
            # on reste sur la camera du haut
            camera_global = "front"
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if verbose:
        print "camera gloabl = ", camera_global
        print "detect = ", detect_
        print "x = ", x
        print "y = ", y
        print "w = ", w
        print "h = ", h
        print "Found Ball"
        print "____________________________________________________________________________"
    return


def align(verbose=False):
    global camera_global, head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # Center the ball in the image to align the head
    # Detect ball
    detect_, x, y, w, h = recv_data_ball(s, camera_global)
    err_x = nao_drv.image_width / 2 - x
    err_y = y - nao_drv.image_height / 2
    while abs(err_x) > 20 or abs(err_y) > 15:
        if detect_:
            yaw = 0.05 * err_x / nao_drv.image_width
            pitch = - 0.05 * err_y / nao_drv.image_height
            head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
            if verbose:
                print "ALIGNING"
                print "Error head : err_x = ", err_x, " / err_y = ", err_y
                print "x : ", x, "y : ", y
                # print "Moving head : yaw = ", yaw, " / pitch = ", pitch
                print "head_yaw = ", head_yaw * 180 / np.pi, " / head_pitch = ", head_pitch * 180 / np.pi

            control.headControl(motion, head_yaw + yaw, head_pitch + pitch, verbose=False)
            # Detect ball
            detect_, x, y, w, h = recv_data_ball(s, camera_global)
            err_x = nao_drv.image_width / 2 - x
            err_y = y - nao_drv.image_height / 2
        else:
            print "Align head : No ball detected"
            search(verbose=True)
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if verbose:
        print "Ball centered"
        print "____________________________________________________________________________"
    return


def alignBody(verbose=False):
    global camera_global, head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # Tourner le corps du meme angle que la tete
    # head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    x, y, theta = motion.getRobotPosition(False)
    err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))
    if verbose:
        print "Erreur angulaire : ", err_theta * 180 / np.pi
    while abs(err_theta * 180 / np.pi) > 2:
        if verbose:
            print "ALIGN BODY"
            print "Erreur angulaire : ", err_theta * 180 / np.pi

        motion.moveTo(0, 0, 0.1 * np.sign(err_theta))
        x, y, theta = motion.getRobotPosition(False)
        err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))
    control.headControl(motion, 0, head_pitch, verbose=False)
    # print "After Robot Position: ", theta * 180 / np.pi, ", ", head_yaw * 180 / np.pi
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if verbose:
        print "Body aligned"
        print "____________________________________________________________________________"
    return


def walkToBall(verbose=False):
    global camera_global, head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # Walk until the ball is big enough
    # Detect ball
    detect_, x, y, w, h = recv_data_ball(s, camera_global)
    err_x = nao_drv.image_width / 2 - x
    err_y = y - nao_drv.image_height / 2
    w_max = 60
    if verbose:
        print "Walk to ball"
        print "x : ", x

    while w < w_max:
        # Detect ball
        detect_, x, y, w, h = recv_data_ball(s, camera_global)
        if abs(err_x - nao_drv.image_width / 2 - x) > 50:
            # Saut dans l'erreur
            print "STOP Saut dans l'erreur"

        err_x = nao_drv.image_width / 2 - x
        err_y = y - nao_drv.image_height / 2

        if abs(err_x) > 100 or abs(err_y) > 100:
            if verbose:
                print "Stop walking to center ball"
                print "align : err_x = ", err_x, " / err_y = ", err_y
            motion.stopMove()
            # search(verbose=True)
            align(verbose=True)
            alignBody(verbose=True)

        else:
            if verbose:
                print "Marche en cours ; Taille balle : w = ", w
                print "Position balle : err_x = ", err_x, " / err_y = ", err_y
            vx, vy, vtheta = 0.5, 0, 0
            motion.moveToward(vx, vy, vtheta)

        if not detect_:
            search(verbose=True)

    motion.stopMove()
    # print "start align"
    # align(verbose=True)
    # print "start alignBody"
    # alignBody(verbose=True)
    return


if __name__ == "__main__":
    search(verbose=True)
    align(verbose=True)
    alignBody(verbose=True)
    # print "AlignBODY done"
    walkToBall(verbose=True)
    # print "FINISH"
