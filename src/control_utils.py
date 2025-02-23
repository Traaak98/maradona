import numpy as np
import time
import sys
import socket
import os

from naoqi import ALProxy
import nao_driver
import pickle


# set default IP nd port on simulated robot
robot_ip = "localhost"
robot_port = 11212


def wakeUp(robot_ip, robot_port):
    try:
        motionProxy = ALProxy("ALMotion", robot_ip, robot_port)
    except Exception, e:
        print "Could not create proxy to ALMotion"
        print "Error was: ", e
        exit()

    # try:
    #     postureProxy = ALProxy("ALRobotPosture", robot_ip, robot_port)
    # except Exception, e:
    #     print "Could not create proxy to ALRobotPosture"
    #     print "Error was: ", e
    #     exit()

    motionProxy.wakeUp()

    # Send NAO to Pose Init : it not standing then standing up
    # postureProxy.goToPosture("StandInit", 0.5)

    # Enable arms control by Walk algorithm
    motionProxy.setWalkArmsEnabled(True, True)

    # allow to stop motion when losing ground contact, NAO stops walking
    # when lifted  (True is default)
    motionProxy.setMotionConfig([["ENABLE_FOOT_CONTACT_PROTECTION", True]])

    # motionProxy.moveInit()
    return motionProxy


def center_ball(motionProxy, px, py, width, height):
    """Function used to center the ball in the image by moving the head / Control computation / Guidage"""
    err_x = width / 2 - px
    err_y = py - height / 2
    delta_angle = 0.05  # correction en radians
    delta_err = 5  # tolerance en pixels
    yaw = 0
    pitch = 0
    if err_x > delta_err:
        yaw = delta_angle
    elif err_x < -delta_err:
        yaw = -delta_angle
    if err_y > delta_err:
        pitch = delta_angle
    elif err_y < -delta_err:
        pitch = - delta_angle

    headControl(motionProxy, yaw, pitch, verbose=False)
    time.sleep(0.1)
    return


def headControl(motionProxy, yaw, pitch, verbose=False):
    """Function used to control the head / Communication with the drivers."""
    fractionMaxSpeed = 0.8
    motionProxy.setAngles(["HeadYaw", "HeadPitch"], [yaw, pitch], fractionMaxSpeed)
    if verbose:
        head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
        print "HeadYaw: ", head_yaw * 180 / np.pi, " / HeadPitch: ", head_pitch * 180 / np.pi


def attain_ball(motionProxy, x, y, w, h, verbose=False):
    # Garder la balle centree dans l'image
    center_ball(motionProxy, x, y, w, h)

    # Tourner le corps du meme angle que la tete
    head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
    x, y, theta = motionProxy.getRobotPosition(False)

    # print "Robot Position: ", theta * 180 / np.pi, ", ", head_yaw * 180 / np.pi
    err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))
    print "Error theta: ", err_theta
    vx, vy, w = 0, 0, 0
    if err_theta * 180 / np.pi > 5:
        w = np.sign(err_theta) * 0.1
    print "Vitesse angulaire : ", w

    motionProxy.moveToward(vx, vy, w)
    headControl(motionProxy, 0, head_pitch, verbose=False)
    x, y, theta = motionProxy.getRobotPosition(False)
    # print "After Robot Position: ", theta * 180 / np.pi, ", ", head_yaw * 180 / np.pi
    return


def openEyes(robot_ip, robot_port):
    """Start the NAO driver"""
    nao_drv = nao_driver.NaoDriver(nao_ip=robot_ip, nao_port=robot_port)
    # nao_drv.set_nao_at_rest()

    # Important !!! define the path to the folder V-REP uses to store the camera images
    if nao_drv.vnao:
        path = os.getcwd()[0:-12]
        nao_drv.set_virtual_camera_path(path + "imgs")

    # set top camera (cam_num: top=0, bottom=1)
    cam_num = 0
    nao_drv.change_camera(cam_num)

    # headControl(motionProxy, 10, 0.2, verbose=True)
    # acquire the image before the motion
    img_ok, cv_img, image_width, image_height = nao_drv.get_image()
    # nao_drv.show_image(key=1)
    return nao_drv


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


def searchGoal(s, verbose=False):
    if verbose:
        print "SEARCHING GOAL"
    detect_, x, y, w, h, nb_corner = recv_data_goal(s)
    if nb_corner >= 3:
        if verbose:
            print "GOAL FOUND"
        # Calcul des differences selon y pour trouver les deux coins opposes.
        diff = np.array([y[0] - y[1], y[0] - y[2], y[1] - y[2]])
        id = np.argmax(diff)
        if verbose:
            print "id = ", id
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
                corners_op = np.array([1, 2])
            else:
                corners_op = np.array([2, 1])

        # Calcul milieu du segment entre les deux coins opposes.
        milieu_x = x[corners_op[0]] + (x[corners_op[1]] - x[corners_op[0]]) / 2

        if verbose:
            print "milieu_x = ", milieu_x

        # Verifier que ce milieu est quasi au centre de l'image.
        borne_x_min = 320 / 2 - 6 # TODO : trouver les bonnes bornes
        borner_x_max = 320 / 2 + 6
        if borne_x_min < milieu_x < borner_x_max:
            if verbose:
                print "GOAL CENTERED"
            return True
        else:
            if verbose:
                print "GOAL NOT CENTERED"
            return False
    else:
        if verbose:
            print "NO GOAL"
        return False


def alignBody_end(motionProxy, head_yaw, head_pitch, verbose=False):
    # headControl(motionProxy, head_yaw, head_pitch, verbose=False)
    # Tourner le corps du meme angle que la tete
    # head_yaw, head_pitch = motion.getAngles(["HeadYaw", "HeadPitch"], True)
    x, y, theta0 = motionProxy.getRobotPosition(False)
    print "ALIGN BODY END : head_yaw = ", head_yaw * 180 / np.pi
    print "theta = ", theta0 * 180 / np.pi
    # err_theta = 2 * np.arctan(np.tan((head_yaw - theta) / 2))
    # commade = theta + head_yaw
    # valeur = theta - theta0
    err_theta = 2 * np.arctan(np.tan(head_yaw / 2))
    if verbose:
        print "Erreur angulaire : ", err_theta * 180 / np.pi
    while abs(err_theta * 180 / np.pi) > 5:
        if verbose:
            print "ALIGN BODY"
            print "Erreur angulaire : ", err_theta * 180 / np.pi

        motionProxy.moveTo(0, 0, 0.05 * np.sign(err_theta))
        x, y, theta = motionProxy.getRobotPosition(False)
        err_theta = 2 * np.arctan(np.tan((theta0 + head_yaw - theta) / 2))
    # headControl(motionProxy, 0, head_pitch, verbose=False)
    # print "After Robot Position: ", theta * 180 / np.pi, ", ", head_yaw * 180 / np.pi
    head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
    if verbose:
        print "Body aligned"
        print "____________________________________________________________________________"
    return


def align_x(motionProxy, nao_drv, s, camera_global, head_yaw, head_pitch, verbose=False):
    # headControl(motionProxy, head_yaw, head_pitch, verbose=False)
    # Center the ball in the image to align the head
    # Detect ball
    detect_, x, y, w, h = recv_data_ball(s, camera_global)
    err_x = nao_drv.image_width / 2 - x
    while abs(err_x) > 20:
        if detect_:
            yaw = 0.05 * err_x / nao_drv.image_width
            head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
            if verbose:
                print "ALIGNING"
                print "Error head : err_x = ", err_x
                print "x : ", x
                # print "Moving head : yaw = ", yaw, " / pitch = ", pitch
                print "head_yaw = ", head_yaw * 180 / np.pi

            headControl(motionProxy, head_yaw + yaw, head_pitch, verbose=False)
            # Detect ball
            detect_, x, y, w, h = recv_data_ball(s, camera_global)
            err_x = nao_drv.image_width / 2 - x
        else:
            print "Align head : No ball detected"
            # search(verbose=True)
    if verbose:
        print "ALIGN X : head_yaw = ", head_yaw * 180 / np.pi
        print "Ball centered"
        print "____________________________________________________________________________"

    return


if __name__ == "__main__":
    path = os.getcwd()[0:-12]
    print("path = ", path)
    # create NAO driver
    nao_drv = openEyes(robot_ip, robot_port)
    motion = wakeUp(robot_ip, robot_port)

    # put NAO in safe position
    # nao_drv.set_nao_at_rest()

    # Important  when using virtual NAO !!! set path to the folder where V-REP stores the camera images
    # nao_drv.set_virtual_camera_path("/home/newubu/Robotics/nao/vnao/plugin-v2/imgs")
    nao_drv.set_virtual_camera_path(path + "imgs")

    fps = 4
    dt_loop = 1. / fps
    # infinite test loop, stops with Ctrl-C
    while True:
        t0_loop = time.time()

        img_ok, img, nx, ny = nao_drv.get_image()
        nao_drv.show_image(key=1)

        headControl(motion, 1, 0, verbose=True)
        time.sleep(0.5)
        attain_ball(motion)

        break

        dt = dt_loop - (time.time() - t0_loop)
        if dt > 0:
            time.sleep(dt)
