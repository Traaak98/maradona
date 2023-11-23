#!/usr/bin/env python3

import random
import socket, select
from time import gmtime, strftime, time
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

# Load model :
model = load_model()
t0 = time()

while True:

    read_sockets, write_sockets, error_sockets = select.select(connected_clients_sockets, [], [])
    # print("OK")

    for sock in read_sockets:
        if sock == server_socket:
            sockfd, client_address = server_socket.accept()
            connected_clients_sockets.append(sockfd)
        else:
            try:
                # print('Buffer size is %s' % buffer_size)

                # Find image :
                path = os.getcwd()[0:-12]
                # print(path)
                image = cv.imread(path + "imgs/out_11212.ppm")

                # MESSAGE :
                t1 = time() - t0
                # print("Avant requete client : ", t1)
                data = sock.recv(buffer_size)
                txt = str(data)     # b'blabla' to blabla
                txt = txt[2:-1]

                if txt == "REQUEST BALL":
                    #t2 = time() - t0
                    #print("Avant utilisation modele : ", t2)
                    new_image, detect_, x, y, w, h = detect_ball(image, model)
                    #t3 = time() - t0
                    #print("Entre modele et imwrite : ", t3)
                    cv.imwrite(path + "imgs/out_11212_detect.ppm", new_image)

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

                elif txt == 'BYE':
                    print('got BYE')
                    sock.shutdown()

            except:
                sock.close()
                connected_clients_sockets.remove(sock)
                print('Client disconnected.')
                continue

server_socket.close()
