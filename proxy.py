#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sample Script
    Version 0.1
"""

#import argparse
import logging
import threading
import socket
import sys

FORMAT = '%(asctime)-15s - %(message)s'
LOGGER = logging.getLogger('scriptlogger')
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(FORMAT))
LOGGER.addHandler(ch)

def server_loop(fwd_ip, fwd_port, recv_first, listen_ip="0.0.0.0", listen_port=8080):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((listen_ip, listen_port))
    except:
        LOGGER.error("[!!!] Couldn't bind to %s:%d" % (listen_ip, listen_port))
        sys.exit(1)

    LOGGER.info("[*] server listening to %s:%d" % (listen_ip, listen_port))

    server.listen(5)

    while True:
        client_sock, addr = server.accept()
        LOGGER.info("[=>] new connection accepted from %s:%d" % (addr[0], addr[1]))

        proxy_thread = threading.Thread(target=proxy_handler,
                args=(client_sock, fwd_ip, fwd_port, recv_first))
        proxy_thread.start()

def proxy_handler(client_sock, fwd_ip, fwd_port, recv_first):
    LOGGER.info("[<=] opening connection to remote host")
    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_sock.connect((fwd_ip, fwd_port))

    if recv_first:
        remote_buff = receive_from(remote_sock)
        remote_buff = response_handler(remote_buff)
        if len(remote_buff):
            LOGGER.info("[<=] forwarding %d bytes to local connection" % len(remote_buff))
            client_sock.send(remote_buff)

    while True:
        local_buff = receive_from(client_sock)
        if len(local_buff):
            LOGGER.info("[=>] forwarding %d bytes to remote connection" % len(local_buff))
            local_buff = request_handler(local_buff)
            remote_sock.send(local_buff)

        remote_buff = receive_from(remote_sock)
        if len(remote_buff):
            LOGGER.info("[<=] forwarding %d bytes to local connection" % len(remote_buff))
            remote_buff = response_handler(remote_buff)
            client_sock.send(remote_buff)

        #if not len(remote_buff) or not len(local_buff):
        #    client_sock.close()
        #    remote_sock.close()
        #    LOGGER.info("[*] No more data. Closing connections")

def receive_from(connection):
    buffer = ""
    connection.settimeout(0.1)

    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except:
        pass

    return buffer


def request_handler(buffer):
    return buffer

def response_handler(buffer):
    return buffer

def main():
    """ main program
    """
    listen_ip = "0.0.0.0"
    listen_port = 8080
    fwd_ip = "tmbt.de"
    fwd_port = 22
    recv_first = True

    server_loop(fwd_ip, fwd_port, recv_first)


if __name__ == '__main__':
    main()
