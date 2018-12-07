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

from optparse import OptionParser


FORMAT = '%(asctime)-15s - %(message)s'
LOGGER = logging.getLogger('scriptlogger')
LOGGER.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(FORMAT))
LOGGER.addHandler(ch)

THREADS = []

RUN = True


def thread_cleanup(signum=None, frame=None):
    global THREADS, RUN
    RUN = False
    LOGGER.debug("Thread cleanup: %d threads running" % len(THREADS))


def server_loop(fwd_ip, fwd_port, listen_ip="0.0.0.0", listen_port=8080):
    global THREADS, RUN
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((listen_ip, listen_port))
    except Exception:
        LOGGER.error("[!!!] Couldn't bind to %s:%d" % (listen_ip, listen_port))
        sys.exit(1)

    LOGGER.info("[*] server listening to %s:%d" % (listen_ip, listen_port))
    LOGGER.info("[*] forwarding to %s:%d" % (fwd_ip, fwd_port))

    server.listen(5)

    while RUN:
        LOGGER.debug("[*] waiting for new client connection")
        try:
            client_sock, addr = server.accept()
        except socket.error:
            LOGGER.info("[*] interrupted. Exiting ...")
            return

        LOGGER.info("[=>] new connection accepted from %s:%d" % (addr[0], addr[1]))
        proxy_thread = threading.Thread(target=proxy_handler, args=(client_sock, fwd_ip, fwd_port))
        proxy_thread.start()
        THREADS.append(proxy_thread)


def proxy_handler(client_sock, fwd_ip, fwd_port):
    global THREADS
    LOGGER.info("[*] starting proxy handler")
    LOGGER.info("[<=] opening connection to remote host")
    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_sock.connect((fwd_ip, fwd_port))

    client_thread = threading.Thread(target=connection_handler, args=(client_sock, remote_sock))
    client_thread.start()

    remote_thread = threading.Thread(target=connection_handler, args=(remote_sock, client_sock))
    remote_thread.start()

    THREADS.append(client_thread)
    THREADS.append(remote_thread)


def connection_handler(input_socket, output_socket):
    global RUN
    LOGGER.info("[*] starting connection handler in:%s os:%s." % (
        input_socket.getpeername(),
        output_socket.getpeername()))
    while RUN:
        try:
            buff = receive_from(input_socket)
        except socket.timeout:
            LOGGER.info("[*] %s timed out. Closing connections." % input_socket.getpeername())
            output_socket.close()
            break

        if len(buff):
            LOGGER.debug("[%s -> %s] received %d bytes" % (
                input_socket.getpeername()[0], output_socket.getpeername()[0], len(buff)))
            try:
                output_socket.send(buff)
                LOGGER.debug("[%s -> %s] forwarding %d bytes" % (
                    input_socket.getpeername()[0], output_socket.getpeername()[0], len(buff)))
            except socket.timeout:
                LOGGER.info("[*] %s timed out. Closing connections." % output_socket.getpeername())
                input_socket.close()
                break

    # try cleaning up the input socket
    try:
        LOGGER.debug("[*] closing connection to %s" % input_socket.getpeername())
        input_socket.close()
    except Exception:
        pass


def receive_from(connection):
    buffer = ""
    connection.settimeout(0)

    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except Exception:
        pass

    return buffer


def main():
    """ main program
    """
    parser = OptionParser()
    parser.add_option(
            "-d", "--debug", action="store_true", dest="debug", default=False, help="print debug information")
    (options, args) = parser.parse_args()

    if options.debug:
        LOGGER.setLevel(logging.DEBUG)

    if len(args) < 2:
        print "Usage: %s listenaddress:port remoteaddress:port" % sys.argv[0]
        print ""
        print "example: %s 0.0.0.0:9000 8.8.4.4:53" % sys.argv[0]
        sys.exit(0)

    listen = args[0].split(":")
    remote = args[1].split(":")

    signal.signal(signal.SIGTERM, thread_cleanup)

    try:
        server_loop(remote[0], int(remote[1]), listen_ip=listen[0], listen_port=int(listen[1]))
    except KeyboardInterrupt:
        thread_cleanup()
    except ValueError:
        print "invalid port"
        sys.exit(1)
    except IndexError:
        print "specify local and remote ip/port like '127.0.0.1:22'"


if __name__ == '__main__':
    main()
