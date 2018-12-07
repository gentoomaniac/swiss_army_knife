#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Sample Script
    Version 0.1
"""

import logging
import socket
import sys

from optparse import OptionParser

FORMAT = '%(asctime)-15s - %(message)s'
LOGGER = logging.getLogger('scriptlogger')
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(FORMAT))
LOGGER.addHandler(ch)


def main():
    """ main program
    """
    min_port = 1
    max_port = 1024
    sock_timeout = 0.1

    if len(sys.argv) < 2:
        print "usage: %s IP [minport:maxport]" % sys.argv[0]
        sys.exit(1)

    parser = OptionParser()
    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False, help="print debug information")
    (options, args) = parser.parse_args()

    if options.debug:
        LOGGER.setLevel(logging.DEBUG)

    if len(args) > 1:
        portrange = args[1].split(":")

        if len(portrange) != 2:
            print "Portrange must be specified as <minport>:<maxport>"
            sys.exit(1)

        try:
            min_port = int(portrange[0])
            max_port = int(portrange[1])
        except:
            print "Portrange must consist of two valid integer"
            sys.exit(1)

        if min_port < 1 or min_port > 65635 or max_port < 1 or max_port > 65635 or min_port > max_port:
            print "Invalid portrange specified!"
            sys.exit(1)

    socket.setdefaulttimeout(sock_timeout)
    for port in xrange(min_port, max_port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((args[0], port))
            sock.close()
        except socket.timeout:
            LOGGER.info("[BLOCKED] %d" % port)
            continue
        except:
            continue
        LOGGER.info("[OPEN] %d" % port)


if __name__ == '__main__':
    main()
