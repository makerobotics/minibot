#!/usr/bin/env python
import socket    #for sockets
import sys    #for exit
import os
import time
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class udp():

    def __init__(self):
        #self.host = '192.168.2.164';
        self.host = 'minibot';
        self.port = 4210;
        self.busy = False

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except socket.error:
            logger.error('Failed to create socket')
        #self.readConfig()
        logger.debug("Started udp class")

    def readConfig(self):
        # Opening JSON file
        f = open('config.json',)
        # returns JSON object as a dictionary
        data = json.load(f)
        # Closing file
        f.close()

    def sendUDP(self, msg):
        res = "error"
        if(not self.busy):
            self.busy = True
            try:
                frame = msg.split()
                # turn angle in deg
                if("turn" in frame[0]):
                    msg = "1 "+str(round(float(frame[1])*22.575))+" "+str(round(float(frame[1])*(-22.575)))
                # move distance in cm
                if("move" in frame[0]):
                    msg = "1 "+str(round(float(frame[1])*21.558*10))+" "+str(round(float(frame[1])*(21.558*10)))
                logger.debug("UDP class received: "+msg)
                try :
                    #Set the whole string
                    self.s.sendto(msg.encode(), (self.host, self.port))
                    self.s.settimeout(1)
                    
                    # receive data from client (data, addr)
                    d = self.s.recvfrom(1024)
                    reply = d[0]
                    addr = d[1]
                    
                    logger.info('Server reply : ' + reply.decode())
                    res = reply.decode()
                except socket.timeout:
                    logger.error("UDP Timeout")
                except socket.error:
                    logger.error('Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            except:
                logger.debug("closing socket")
                self.s.close()
            self.busy = False
        else:
            res = "busy"
        return res

    def close(self):
        self.s.close()
        logger.info("Closed udp")

# Run this if standalone (test purpose)
if __name__ == '__main__':
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(ch)

    try:
        logger.info("Started main")
        myudp = udp()
        myudp.sendUDP("Welcome")
        time.sleep(0.5)
    except KeyboardInterrupt:
        # Signal termination
        logger.info("Keyboard interrupt. Terminate thread")
    finally:
        myudp.close()
        logger.debug("Thread terminated")
