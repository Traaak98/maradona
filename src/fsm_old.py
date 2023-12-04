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
    print "message received "
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
    global head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
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
            print "Moving head : direction = ", direction * 0.05, "nb_tour = ", nb_tour
            print "head_yaw = ", head_yaw * 180 / np.pi, "head_pitch = ", head_pitch * 180 / np.pi
        control.headControl(motion, head_yaw + direction * 0.05, head_pitch, verbose=False)

        # Detect ball
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        if head_pitch * 180 / np.pi < 24:
            detect_, x, y, w, h = recv_data_ball(s, "front")
        else:
            detect_, x, y, w, h = recv_data_ball(s, "bottom")
        if not detect_:
            detect_, x, y, w, h = recv_data_ball(s, "bottom")

    if verbose:
        print "detect = ", detect_
        print "x = ", x
        print "y = ", y
        print "w = ", w
        print "h = ", h
        print "Found Ball"
    return


def align(verbose=False):
    global head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # Center the ball in the image to align the head
    # Detect ball
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    if head_pitch * 180 / np.pi > 24:
        detect_, x, y, w, h = recv_data_ball(s, "bottom")
    else:
        detect_, x, y, w, h = recv_data_ball(s, "front")
    err_x, err_y = 100, 100
    dt_loop = 0.05
    t0_loop = time.time()
    while abs(err_x) > 12 or abs(err_y) > 10:
        if detect_:
            err_x = nao_drv.image_width / 2 - x
            err_y = y - nao_drv.image_height / 2
            yaw = 0.05 * err_x / nao_drv.image_width
            pitch = - 0.05 * err_y / nao_drv.image_height

            head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
            if verbose:
                print "Error head : err_x = ", err_x, " / err_y = ", err_y
                print "Moving head : yaw = ", yaw, " / pitch = ", pitch
                print "head_yaw = ", head_yaw * 180 / np.pi, " / head_pitch = ", head_pitch * 180 / np.pi

            control.headControl(motion, head_yaw + yaw, head_pitch + pitch, verbose=False)

            # Detect ball
            head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
            if head_pitch * 180 / np.pi > 24:
                detect_, x, y, w, h = recv_data_ball(s, "bottom")
            else:
                detect_, x, y, w, h = recv_data_ball(s, "front")

            # # Waiting time
            # dt = dt_loop-(time.time()-t0_loop)
            # if dt > 0:
            #     time.sleep(dt)

        else:
            print "No ball detected"
            search(verbose=True)
    print "Ball aligned"
    return


def alignBody(verbose=False):
    global head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # Tourner le corps du meme angle que la tete
    x, y, theta = motion.getRobotPosition(False)
    err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))
    if verbose:
        print "Align Body"
        print "Erreur angulaire : ", err_theta

    while err_theta * 180 / np.pi > 1:
        # print "Robot Position: ", theta * 180 / np.pi, ", ", head_yaw * 180 / np.pi
        err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))
        # print "Error theta: ", err_theta
        if verbose:
            print "Erreur angulaire : ", err_theta
        motion.moveTo(0, 0, theta + err_theta)
        x, y, theta = motion.getRobotPosition(False)

    control.headControl(motion, 0, head_pitch, verbose=False)
    head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    # print "After Robot Position: ", theta * 180 / np.pi, ", ", head_yaw * 180 / np.pi


def walkToBall(verbose=False):
    global head_yaw, head_pitch
    control.headControl(motion, head_yaw, head_pitch, verbose=False)
    # Get detect bool from image detection
    w_image, h_image = nao_drv.image_width, nao_drv.image_height
    # Detect ball
    detect_, x, y, w, h = recv_data_ball(s, "front")
    if not detect_:
        detect_, x, y, w, h = recv_data_ball(s, "bottom")

    w_max = 60
    if verbose:
        print "w = ", w
        print "Walk to ball"

    while w < w_max:
        # Detect ball
        head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
        if head_pitch * 180 / np.pi > 24:
            detect_, x, y, w, h = recv_data_ball(s, "bottom")
        else:
            detect_, x, y, w, h = recv_data_ball(s, "front")
        err_x = nao_drv.image_width / 2 - x
        err_y = y - nao_drv.image_height / 2

        if abs(err_x) > 150 or abs(err_y) > 150:
            print "align : err_x = ", err_x, " / err_y = ", err_y
            motion.stopMove()
            # search(verbose=True)
            align(verbose=True)
            alignBody(verbose=True)
        else:
            print "avance : w = ", w
            vx, vy, vtheta = 0.5, 0, 0
            motion.moveToward(vx, vy, vtheta)

    motion.stopMove()
    print "start align"
    align(verbose=True)
    print "start alignBody"
    alignBody(verbose=True)

    return


if __name__ == "__main__":
    search(verbose=True)
    align(verbose=True)
    alignBody(verbose=True)
    print "AlignBODY done"
    walkToBall(verbose=True)
    print "FINISH"
