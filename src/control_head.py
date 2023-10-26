#import nao_yolo # python module for tiny YOLO neural network
import nao_driver
#import nao_improc # python module for image processing
#import nao_ctrl # python module for robot control algorithms
import time
import sys

# set default IP nd port on simulated robot
robot_ip = "localhost"
robot_port = 11212

# start the nao driver
nao_drv = nao_driver.NaoDriver(nao_ip=robot_ip, nao_port=robot_port)

# Important !!! define the path to the folder V-REP uses to store the camera images
if nao_drv.vnao:
    nao_drv.set_virtual_camera_path("/home/clara/Desktop/visual_servoing/UE52-VS-IK/imgs")
nao_drv.set_nao_at_rest()

# set top camera (cam_num: top=0, bottom=1)
cam_num = 0
nao_drv.change_camera(cam_num)

# acquire the image before the motion
img_ok, cv_img, image_width, image_height = nao_drv.get_image()

# Insert head control here
# ...

# set back NAO in a safe position
nao_drv.set_nao_at_rest()
