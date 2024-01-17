#!/usr/bin/env python3

import random
import socket, select
from time import gmtime, strftime, time
from random import randint
from detect import detect_goal, detect_ball, load_model
import cv2 as cv
import os
import numpy as np
import pickle

HOST = '127.0.0.1'
PORT = 6666

connected_clients_sockets = []

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10)

connected_clients_sockets.append(server_socket)
buffer_size = 4096

# Load model :
model = load_model()
t0 = time()

# Type de camera :
camera = ""

# Find image :
path = os.getcwd()[0:-12]
bottom_image = path + "imgs/out_down_11212.ppm"
front_image = path + "imgs/out_11212.ppm"
camera_id = "front"
reel = True

while True:

    read_sockets, write_sockets, error_sockets = select.select(connected_clients_sockets, [], [])

    for sock in read_sockets:
        if sock == server_socket:
            sockfd, client_address = server_socket.accept()
            connected_clients_sockets.append(sockfd)
        else:
            try:
                print('Buffer size is %s' % buffer_size)

                # print(path)

                # MESSAGE :
                t1 = time() - t0
                # print("Avant requete client : ", t1)
                data = sock.recv(buffer_size)
                txt = str(data)     # b'blabla' to blabla
                txt1 = txt[2:14]
                txt2 = txt[15:-1]
                txt3 = txt[2:-1]

                if txt1 == "REQUEST BALL":
                    # Check camera
                    if txt2 == "FRONT":
                        image = cv.imread(path + "imgs/out_11212.ppm")
                        camera = "front"
                    elif txt2 == "BOTTOM":
                        image = cv.imread(path + "imgs/out_down_11212.ppm")
                        camera = "bottom"
                    #t2 = time() - t0
                    #print("Avant utilisation modele : ", t2)
                    print("camera = ", image)
                    new_image, detect_, x, y, w, h = detect_ball(image, model)
                    if image is None:
                        new_image, detect_, x, y, w, h = None, False, 0, 0, 0, 0
                        message = b"%d;%2f;%2f;%2f;%.2f" % (detect_, x, y, w, h)
                        sock.send(message)
                        continue
                    #t3 = time() - t0
                    #print("Entre modele et imwrite : ", t3)
                    if camera == "front":
                        cv.imwrite(path + "imgs/out_11212_detect_ball.ppm", new_image)
                    elif camera == "bottom":
                        cv.imwrite(path + "imgs/out_down_11212_detect_ball.ppm", new_image)

                    #t4 = time() - t0
                    #print("Avant envoi : ", t4)
                    message = b"%d;%2f;%2f;%2f;%.2f" % (detect_, x, y, w, h)
                    sock.send(message)
                    print("detect = ", detect_)
                    print("x = ", x)
                    print("y = ", y)
                    print("w = ", w)
                    print("h = ", h)

                    #t5 = time() - t0
                    #print("Fin requete client : ", t5)

                elif txt3 == "REQUEST CORNER":
                    image = cv.imread(path + "imgs/out_11212.ppm")
                    if image is None:
                        new_image, detect_, x, y, w, h, nb_corner = None, False, np.array([]), np.array([]), np.array([]), np.array([]), 0
                        message = np.concatenate((np.array([nb_corner]), np.array([detect_]), x, y, w, h), axis=0)
                        sock.send(pickle.dumps(message, protocol=2))
                        continue
                    new_image, detect_, x, y, w, h, nb_corner = detect_goal(image, model)
                    print("detect = ", detect_)
                    print("x = ", x)
                    print("y = ", y)
                    print("w = ", w)
                    print("h = ", h)
                    print("nb_corner = ", nb_corner)
                    message = np.concatenate((np.array([nb_corner]), np.array([detect_]), x, y, w, h), axis=0)
                    sock.send(pickle.dumps(message, protocol=2))
                    cv.imwrite(path + "imgs/out_11212_detect_goal.ppm", new_image)

                elif txt == 'BYE':
                    print('got BYE')
                    sock.shutdown()

                elif txt3[0:6] == "SIZE F":
                    if reel:
                        if os.path.exists(front_image):
                            os.remove(front_image)
                        tmp = txt3.split()
                        size = int(tmp[-1])

                        print('got size')
                        print('size is %s' % size)

                        sock.send(b"GOT SIZE")
                        # Now set the buffer size for the image
                        buffer_size = 40960000

                elif txt3[0:6] == "SIZE B":
                    if reel:
                        if os.path.exists(bottom_image):
                            os.remove(bottom_image)
                        tmp = txt3.split()
                        size = int(tmp[-1])

                        print('got size')
                        print('size is %s' % size)

                        sock.send(b"GOT SIZE")
                        # Now set the buffer size for the image
                        buffer_size = 40960000

                else:
                    if reel and camera_id == "front":
                        # myfile = open(front_image, 'ab')
                        data = pickle.loads(sock.recv(buffer_size))

                        if not data:
                            print('no data rip')
                            # myfile.close()
                            break

                        if txt3[0:3] == 'EOF':
                            # myfile.close()
                            print('got EOF')
                            sock.send(b"GOT IMAGE")
                            buffer_size = 4096
                            sock.shutdown()

                        print("wrinting something")
                        print(type(data))


                        print(type(data))
                        cv.imwrite(front_image, data)
                        # myfile.write(data)
                        sock.send(b"WRITE OK")
                        print("writing file ....")

                    elif reel and camera_id == "bottom":
                        # myfile = open(bottom_image, 'ab')

                        if not data:
                            print('no data rip')
                            # myfile.close()
                            break

                        if txt3[0:3] == 'EOF':
                            # myfile.close()
                            print('got EOF')
                            sock.send(b"GOT IMAGE")
                            buffer_size = 4096
                            sock.shutdown()

                        cv.imwrite(bottom_image, data)
                        # myfile.write(data)
                        sock.send(b"WRITE OK")
                        print("writing file ....")

            except:
                print("Unexpected error:")
                sock.close()
                connected_clients_sockets.remove(sock)
                print('Client disconnected.')
                continue

server_socket.close()
