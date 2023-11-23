import numpy as np
import time
import sys
import socket

from naoqi import ALProxy
import nao_driver


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
    #postureProxy.goToPosture("StandInit", 0.5)

    # Enable arms control by Walk algorithm
    motionProxy.setWalkArmsEnabled(True, True)

    # allow to stop motion when losing ground contact, NAO stops walking
    # when lifted  (True is default)
    motionProxy.setMotionConfig([["ENABLE_FOOT_CONTACT_PROTECTION", True]])
    

    motionProxy.moveInit()
    return motionProxy


def center_ball(motionProxy, px, py, width, height):
    """Function used to center the ball in the image by moving the head / Control computation / Guidage"""
    err_x = width / 2 - px
    err_y = py - height / 2
    delta_angle = 0.05  # correction en radians
    delta_err = 5       # tolerance en pixels
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
    head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
    if verbose:
        print "HeadYaw: ", head_yaw * 180 / np.pi, " / HeadPitch: ", head_pitch * 180 / np.pi
    fractionMaxSpeed = 0.8
    motionProxy.setAngles(["HeadYaw", "HeadPitch"], [yaw, pitch], fractionMaxSpeed)
    if verbose:
        time.sleep(0.5) # attendre la fin du deplacement avant de reprendre les donnees
        head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
        print("HeadYaw: ", head_yaw * 180 / np.pi, " / HeadPitch: ", head_pitch * 180 / np.pi)


def attain_ball(motionProxy, verbose=False):
    """How to compute x and y ?"""
    # Tourner le corps du meme angle que la tete
    head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
    motionProxy.
    motionProxy.
    return


def walkTo(motionProxy, vx, vy, w, verbose=False):
    """Communication with the drivers"""
    return


def openEyes(robot_ip, robot_port):
    """Start the NAO driver"""
    nao_drv = nao_driver.NaoDriver(nao_ip=robot_ip, nao_port=robot_port)
    # nao_drv.set_nao_at_rest()

    # Important !!! define the path to the folder V-REP uses to store the camera images
    if nao_drv.vnao:
         nao_drv.set_virtual_camera_path("/home/clara/Desktop/visual_servoing/UE52-VS-IK/imgs")

    # set top camera (cam_num: top=0, bottom=1)
    cam_num = 0
    nao_drv.change_camera(cam_num)

    # headControl(motionProxy, 10, 0.2, verbose=True)
    # acquire the image before the motion
    img_ok, cv_img, image_width, image_height = nao_drv.get_image()
    # nao_drv.show_image(key=1)
    return nao_drv


# Pas besoin d'envoyer l'image au serveur : juste reception des informations
"""def send_image():
    image = "hihi.jpg"

    host = '127.0.0.1'
    port = 6666

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    try:
        # open image
        myfile = open(image, 'rb')
        bytes = myfile.read()
        size = len(bytes)

        # send image size to server
        s.sendall("SIZE %s" % size)
        answer = s.recv(4096)

        print 'answer = %s' % answer

        # send image to server
        if answer == 'GOT SIZE':
            # s.sendall(bytes)
            chunk_size = 4096
            for i in range(0, size, chunk_size):
                print("Sending %s" % i)
                s.sendall(bytes[i:i + chunk_size])
                answer_wait = s.recv(4096)
            print("Sending EOF")
            s.sendall("EOF")

            # check what server send
            answer = s.recv(4096)
            print 'answer = %s' % answer

            if answer == 'GOT IMAGE':
                s.sendall("BYE BYE ")
                print 'Image successfully send to server'

        myfile.close()

    finally:
        s.close()"""


# Reception des donnes envoyees par la detection -> FSM
yolo_host, yolo_port = '127.0.0.1', 6666
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((yolo_host, yolo_port))
def recv_data(client):
    # send request
    client.sendall("REQUEST BALL")
    # receive and store data
    answer = client.recv(4096)
    # booleen de detection, position et rayon de la balle
    ok, x, y, r = answer.split(" ")
    return ok, x, y, r


if __name__ == "__main__":
    # create NAO driver
    nao_drv = openEyes(robot_ip, robot_port)
    motion = wakeUp(robot_ip, robot_port)

    # put NAO in safe position
    # nao_drv.set_nao_at_rest()

    # Important  when using virtual NAO !!! set path to the folder where V-REP stores the camera images
    #nao_drv.set_virtual_camera_path("/home/newubu/Robotics/nao/vnao/plugin-v2/imgs")
    nao_drv.set_virtual_camera_path("/home/clara/Desktop/visual_servoing/UE52-VS-IK/imgs")

    fps = 4
    dt_loop = 1./fps
    # infinite test loop, stops with Ctrl-C
    while True:
        t0_loop = time.time()

        img_ok,img,nx,ny = nao_drv.get_image()
        nao_drv.show_image(key=1)


        dt = dt_loop-(time.time()-t0_loop)
        if dt > 0:
            time.sleep(dt)
