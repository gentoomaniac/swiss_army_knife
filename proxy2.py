#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sample Script
    Version 0.1
"""

import logging
import threading
import signal
import socket
import sys

FORMAT = '%(asctime)-15s - %(message)s'
LOGGER = logging.getLogger('scriptlogger')
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(FORMAT))
LOGGER.addHandler(ch)

THREADS = []

def signal_handler(signum):
    for thread in THREADS:
        thread.kill()

def server_loop(fwd_ip, fwd_port, listen_ip="0.0.0.0", listen_port=8080):
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
                args=(client_sock, fwd_ip, fwd_port))
        proxy_thread.start()

def proxy_handler(client_sock, fwd_ip, fwd_port):
    global THREADS
    LOGGER.info("[*] starting proxy handler")
    LOGGER.info("[<=] opening connection to remote host")
    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_sock.connect((fwd_ip, fwd_port))

    client_thread = threading.Thread(target=connection_handler,
            args=(client_sock, remote_sock))
    client_thread.start()

    remote_thread = threading.Thread(target=connection_handler,
            args=(remote_sock, client_sock))
    remote_thread.start()

    THREADS.append(client_thread)
    THREADS.append(remote_thread)

def connection_handler(input_socket, output_socket):
    LOGGER.info("[*] starting connection handler in:%s os:%s." % (input_socket.getpeername(), output_socket.getpeername()))
    while True:
        try:
            buff = receive_from(input_socket)
        except socket.timeout:
            LOGGER.info("[*] %s timed out. Closing connections." % input_socket.getpeername())
            output_socket.close()
            break

        if len(buff):
            LOGGER.info("[%s] received %d bytes" %
                        (input_socket.getpeername(), len(buff)))
            try:
                output_socket.send(buff)
                LOGGER.info("[<>] forwarding %d bytes to %s" %
                            (len(buff), output_socket.getpeername()))
            except socket.timeout:
                LOGGER.info("[*] %s timed out. Closing connections." % output_socket.getpeername())
                input_socket.close()
                break

def receive_from(connection):
    buffer = ""
    connection.settimeout(0)

    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except:
        pass

    return buffer

def main():
    """ main program
    """
    listen_ip = "0.0.0.0"
    listen_port = 8080
    fwd_ip = "tmbt.de"
    fwd_port = 22

    signal.signal(signal.SIGTERM, signal_handler)

    server_loop(fwd_ip, fwd_port)

if __name__ == '__main__':
    main()
