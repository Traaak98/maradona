import socket
import time

import numpy as np
import control_head as control
import pickle

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


def recv_data_goal(client):
    # send request
    client.sendall("REQUEST CORNER")
    # receive and store data
    message = pickle.loads(client.recv(4096))

    nb_corner = int(message[0])
    ok = int(message[1])
    x = message[2:nb_corner + 2]
    y = message[nb_corner + 2:nb_corner * 2 + 2]
    w = message[nb_corner * 2 + 2:nb_corner * 3 + 2]
    h = message[nb_corner * 3 + 2:nb_corner * 4 + 2]

    return ok, x, y, w, h, nb_corner


def searchGoal(verbose=False):
    global head_yaw, head_pitch
    if verbose:
        print "SEARCHING GOAL"
    detect_, x, y, w, h, nb_corner = recv_data_goal(s)
    if nb_corner >= 3:
        # Calcul des différences selon y pour trouver les deux coins opposés.
        diff = np.array([y[0] - y[1], y[0] - y[2], y[1] - y[2]])
        id = np.argmax(diff)
        if id == 0:
            if x[0] < x[1]:
                corners_op = np.array([0, 1])
            else:
                corners_op = np.array([1, 0])
        elif id == 1:
            if x[0] < x[2]:
                corners_op = np.array([0, 2])
            else:
                corners_op = np.array([2, 0])
        else:
            if x[1] < x[2]:
                corner_op = np.array([1, 2])
            else:
                corner_op = np.array([2, 1])

        # Calcul milieu du segment entre les deux coins opposés.
        milieu_x = x[corners_op[0]] + (x[corners_op[1]] - x[corners_op[0]]) / 2

        # Vérifier que ce milieu est quasi au centre de l'image.
        borne_x_min = 320 / 2 - 20  # TODO : trouver les bonnes bornes
        borner_x_max = 320 / 2 + 20
        if borne_x_min < milieu_x < borner_x_max:
            return True
        else:
            return False
    else:
        return False


def turnArround(verbos=False):
    global head_yaw, head_pitch

    # On oriente la tête vers la balle :
    align(verbose=True)  # TODO : à revoir si on code ou si on repasse par l'état de FSM alignHead.
    motion.headControl(motion, head_yaw, 0, verbose=False)

    # On tourne le corps de 90° vers la balle :
    motion.moveTo(0, 0, np.pi / 2)

    # On tourne autour de la balle tant que le but n'est pas détecté et centré :
    while not searchGoal():
        vx = 5
        vy = 10
        vtheta = 3.14 / 2
        motion.move(vx, vy, vtheta)
    motion.stopMove()
    return


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
    err_y = nao_drv.image_height / 2 - y
    while abs(err_x) > 20 or abs(err_y) > 15:
        if detect_:
            yaw = 0.05 * err_x / nao_drv.image_width
            pitch = 0.05 * err_y / nao_drv.image_height
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
            err_y = nao_drv.image_height / 2 - y
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
    while abs(err_theta * 180 / np.pi) > 5:
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
    err_y = nao_drv.image_height / 2 - y
    w_max = 55
    if verbose:
        print "Walk to ball"
        print "x : ", x

    while w < w_max:
        # Detect ball
        detect_, x, y, w, h = recv_data_ball(s, camera_global)
        # Pour l instant inutile et non fonctionnel
        if abs(err_x - nao_drv.image_width / 2 + x) > 100 or abs(err_y - nao_drv.image_height / 2 + y) > 80:
            # Saut dans l'erreur
            print "align : err_x = ", nao_drv.image_width / 2 - x, " / err_y = ", nao_drv.image_height / 2 - y
            print "STOP Saut dans l'erreur"
            exit()

        err_x = nao_drv.image_width / 2 - x
        err_y = nao_drv.image_height / 2 - y
        vx, vy, vtheta = 0.5, 0, 0
        if abs(err_x) > 10:
            vtheta = 0.1 * np.sign(err_x)
        if y < 15:
            # balle tres basse dans l'image, risques de la perdre
            # align_head ?
            # a voir plus tard !
            # yaw = 0.05 * err_x / nao_drv.image_width
            print "TEST BOUGER TETE"
            print "Balle trop basse, bouger tete"
            print "err_x = ", err_x, " / err_y = ", err_y
            pitch = 0.05 * err_y / nao_drv.image_height
            head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
            print "y = ", y, "pitch = ", (head_pitch + pitch) * 180 / np.pi
            control.headControl(motion, head_yaw + 0, head_pitch + pitch, verbose=False)
            pass

        elif abs(err_x) > 130 or abs(err_y) > 90:
            if verbose:
                print "Stop walking to center ball"
                print "align : err_x = ", err_x, " / err_y = ", err_y
            # motion.stopMove()
            # # search(verbose=True)
            # align(verbose=True)
            # alignBody(verbose=True)

        # else:
        if verbose:
            print "* WALKING *"
            print "Marche en cours ; Taille balle : w = ", w
            print "Position balle : err_x = ", err_x, " / err_y = ", err_y
            print "Vitesse angulaire : vtheta = ", vtheta
        motion.moveToward(vx, vy, vtheta)

        if not detect_:
            search(verbose=True)

    motion.stopMove()
    # print "start align"
    # align(verbose=True)
    # print "start alignBody"
    # alignBody(verbose=True)
    return


"""
def walk():
    global verbose, camera_global, head_yaw, head_pitch
    # Correct head position
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    detect_, x, y, w, h = recv_data_ball(s, camera_global)
    w_max = 55      # entre 55 et 60, voir par rapport au tir

    # Walk until the ball is big enough
    while w < w_max:
        # Detect ball
        detect_, x, y, w, h = recv_data_ball(s, camera_global)
        err_x = nao_drv.image_width / 2 - x
        err_y = nao_drv.image_height / 2 - y
        vx, vy, vtheta = 0.5, 0, 0

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

        if verbose:
            print "* WALKING *"
            print "Marche en cours ; Taille balle : w = ", w
            print "Position balle : err_x = ", err_x, " / err_y = ", err_y
            print "Vitesse : v = [", vx, vy, vtheta, "]"
        motion.moveToward(vx, vy, vtheta)

        if not detect_:
            return "noDetectBall"

    motion.stopMove()
    return "attainBall"
"""

if __name__ == "__main__":
    recv_data_goal(s)
