#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sample Script
    Version 0.1
"""

import binascii
import logging
import socket
import struct
import signal

FORMAT = '%(asctime)-15s - %(message)s'
LOGGER = logging.getLogger('scriptlogger')
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter(FORMAT))
LOGGER.addHandler(ch)

RUN = True

found_hosts = {}


def sigterm_handler():
    global RUN
    RUN = False
#    print ""
#    for ip in found_hosts:
#        print "Found %s with mac %s" % (ip, found_hosts[ip])


def main():
    """ main program
    """
    signal.signal(signal.SIGTERM, sigterm_handler)
    try:
        sniff_arp_requests()
    except KeyboardInterrupt:
        sigterm_handler()


def sniff_arp_requests():
    global found_hosts
    rawSocket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))

    while RUN:

        packet = rawSocket.recvfrom(2048)

        ethernet_header = packet[0][0:14]
        ethernet_detailed = struct.unpack("!6s6s2s", ethernet_header)

        arp_header = packet[0][14:42]
        arp_detailed = struct.unpack("2s2s1s1s2s6s4s6s4s", arp_header)

        # skip non-ARP packets
        ethertype = ethernet_detailed[2]
        if ethertype != '\x08\x06':
            continue

        if arp_detailed[4] == '\x00\x02':
            opcode = "RESP"
        elif arp_detailed[4] == '\x00\x01':
            opcode = "REQ"
        else:
            opcode = "UNKNOWN"

        eth_src_mac = binascii.hexlify(ethernet_detailed[1])
        src_mac = binascii.hexlify(arp_detailed[5])
        src_ip = socket.inet_ntoa(arp_detailed[6])
        dest_mac = binascii.hexlify(arp_detailed[7])
        dest_ip = socket.inet_ntoa(arp_detailed[8])

        if src_ip not in found_hosts:
            found_hosts[src_ip] = src_mac
        # elif not dest_ip in found_hosts:
        #     found_hosts[dest_ip] = dest_mac
        else:
            continue

        LOGGER.info(
                "[new][%s]\t eth_src_mac: %s\tsrc_ip: %s\tsrc_mac: %s\tdest_ip: %s\tdest_mac: %s",
                opcode,
                eth_src_mac,
                src_ip,
                src_mac,
                dest_ip,
                dest_mac)

        # print "****************_ETHERNET_FRAME_****************"
        # print "Dest MAC:        ", binascii.hexlify(ethernet_detailed[0])
        # print "Source MAC:      ", binascii.hexlify(ethernet_detailed[1])
        # print "Type:            ", binascii.hexlify(ethertype)
        # print "************************************************"
        # print "******************_ARP_HEADER_******************"
        # print "Hardware type:   ", binascii.hexlify(arp_detailed[0])
        # print "Protocol type:   ", binascii.hexlify(arp_detailed[1])
        # print "Hardware size:   ", binascii.hexlify(arp_detailed[2])
        # print "Protocol size:   ", binascii.hexlify(arp_detailed[3])
        # print "Opcode:          ", binascii.hexlify(arp_detailed[4])
        # print "Source MAC:      ", binascii.hexlify(arp_detailed[5])
        # print "Source IP:       ", socket.inet_ntoa(arp_detailed[6])
        # print "Dest MAC:        ", binascii.hexlify(arp_detailed[7])
        # print "Dest IP:         ", socket.inet_ntoa(arp_detailed[8])
        # print "*************************************************\n"


if __name__ == '__main__':
    main()
