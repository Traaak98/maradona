#!/usr/bin/env python3

import random
import socket, select
from time import gmtime, strftime
from random import randint
from detect import detect_goal, detect_ball, load_model
import cv2 as cv
import os

HOST = '127.0.0.1'
PORT = 6666

connected_clients_sockets = []

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10)

connected_clients_sockets.append(server_socket)
buffer_size = 4096

while True:

    read_sockets, write_sockets, error_sockets = select.select(connected_clients_sockets, [], [])
    print("OK")
    for sock in read_sockets:

        if sock == server_socket:

            sockfd, client_address = server_socket.accept()
            connected_clients_sockets.append(sockfd)

        else:
            try:
                print(' Buffer size is %s' % buffer_size)

                # Load model :
                model = load_model()

                # Find image :
                path = os.path.dirname(__file__)[:-4]
                print(path)
                image = cv.imread(path + "imgs/out_11212.ppm")

                # MESSAGE :
                data = sock.recv(buffer_size)
                txt = str(data)     # b'blabla' to blabla
                txt = txt[2:-1]

                if txt == "REQUEST BALL":
                    new_image, detect_, x, y, w, h = detect_ball(image, model)
                    cv.imwrite(path + "imgs/out_11212_detect.ppm", new_image)

                    sock.send(detect_)
                    sock.send(x)
                    sock.send(y)
                    sock.send(w)
                    sock.send(h)
                    print("detect = ", detect_)
                    print("x = ", x)
                    print("y = ", y)
                    print("w = ", w)
                    print("h = ", h)


                elif txt == 'BYE':
                    print('got BYE')
                    sock.shutdown()

            except:
                sock.close()
                connected_clients_sockets.remove(sock)
                print('Client disconnected.')
                continue

server_socket.close()
