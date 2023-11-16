import numpy as np
import time
import sys

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

    try:
        postureProxy = ALProxy("ALRobotPosture", robot_ip, robot_port)
    except Exception, e:
        print "Could not create proxy to ALRobotPosture"
        print "Error was: ", e
        exit()

    motionProxy.wakeUp()


# Insert head control here
def headControl(motionProxy, yaw, pitch, verbose=False):
    head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
    if verbose:
        print "HeadYaw: ", head_yaw * 180 / np.pi, " / HeadPitch: ", head_pitch * 180 / np.pi
    fractionMaxSpeed = 0.8
    motionProxy.setAngles(["HeadYaw", "HeadPitch"], [yaw, pitch], fractionMaxSpeed)
    if verbose:
        time.sleep(0.5) # attendre la fin du deplacement avant de reprendre les donnees
        head_yaw, head_pitch = motionProxy.getAngles(["HeadYaw", "HeadPitch"], True)
        print("HeadYaw: ", head_yaw * 180 / np.pi, " / HeadPitch: ", head_pitch * 180 / np.pi)

# set back NAO in a safe position
# il sautille un peu a cause de cette fonction et une fois sur deux il tombe
# nao_drv.set_nao_at_rest()


def openEyes(robot_ip, robot_port):
    # start the nao driver
    nao_drv = nao_driver.NaoDriver(nao_ip=robot_ip, nao_port=robot_port)
    # nao_drv.set_nao_at_rest()

    # Important !!! define the path to the folder V-REP uses to store the camera images
    if nao_drv.vnao:
         nao_drv.set_virtual_camera_path("/home/clara/Desktop/visual_servoing/UE52-VS-IK/imgs")

    # set top camera (cam_num: top=0, bottom=1)
    cam_num = 0
    nao_drv.change_camera(cam_num)

    # acquire the image before the motion
    img_ok, cv_img, image_width, image_height = nao_drv.get_image()


# create client
# client.py
import socket

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
    s.close()


def send_image():


    # Adjust the image sending logic based on your needs
    with open('hihi.jpg', 'rb') as img_file:
        image_data = img_file.read()

    # Send the image data in chunks
    print "Sending image data..."
    chunk_size = 4096
    for i in range(0, len(image_data), chunk_size):
        s.sendall(image_data[i:i + chunk_size])

    # Indicate the end of the image file
    s.sendall(b'')
    print "Image sent successfully!"

    # Receive coordinates from the server
    data = s.recv(4096)
    if data:
        coordinates = eval(data.decode())
        print "Received coordinates: ", coordinates

    s.close()
