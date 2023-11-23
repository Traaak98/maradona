#!/usr/bin/env python3

import random
import socket, select
from time import gmtime, strftime
from random import randint

imgcounter = 1
basename = "image%s.png"

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
                data = sock.recv(buffer_size)
                txt = str(data)     # b'blabla' to blabla
                txt = txt[2:-1]

                if txt[0:4] == "SIZE":
                    tmp = txt.split()
                    size = int(tmp[1])

                    print('got size')
                    print('size is %s' % size)

                    sock.send(b"GOT SIZE")
                    # Now set the buffer size for the image
                    buffer_size = 40960000

                elif txt[0:4] == 'BYE ':
                    print('got BYE')
                    sock.shutdown()

                elif data:
                    print('got image en theorie')
                    myfile = open(basename % imgcounter, 'ab')

                    if not data:
                        print('no data rip')
                        myfile.close()
                        break

                    if txt[0:3] == 'EOF':
                        myfile.close()
                        print('got EOF')
                        sock.send(b"GOT IMAGE")
                        buffer_size = 4096
                        sock.shutdown()

                    myfile.write(data)
                    sock.send(b"WRITE OK")
                    print("writing file ....")

                else:
                    print('Send nothing back.')

            except:
                sock.close()
                connected_clients_sockets.remove(sock)
                print('Client disconnected.')
                continue
        # imgcounter += 1

server_socket.close()
