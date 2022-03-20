#!/usr/bin/env python

import time
import logging
import configparser
from threading import Thread
#import RPi.GPIO as GPIO
import sense
import data
import udp
import json
import math

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class navigation():

    def __init__(self, udp):
        self.udp = udp
        self.x = 0
        self.y = 0
        self.theta = 90
        self.mission = None
        self.obstacles = []
        self.setAcceleration(1200)

    def isMoving(self):
        res = self.udp.sendUDP("5 5")
        logger.debug("Mode: "+res)
        if(int(res) == 0):
            return False
        else:
            return True

    def scan(self):
        return self.udp.sendUDP("8")

    def setAcceleration(self, acceleration):
        self.udp.sendUDP("4 2 "+str(acceleration)+ " "+str(acceleration))
        
    def startMission(self, mission):
        self.mission = mission
        for target in self.mission:
            logger.debug("x: "+str(target['x'])+" y: "+str(target['y']))
            distance = math.sqrt((target['x']-self.x)**2 + (target['y']-self.y)**2)
            angle = round(math.atan2(target['y']-self.y, target['x']-self.x)*180/math.pi)
            logger.debug("Angle: "+str(angle))
            if((angle != self.theta) and (distance > 0)):
                # turn
                logger.debug("turn: "+str(angle-self.theta))
                logger.debug("1 "+str(round((self.theta-angle)*22.575))+" "+str(round(-(self.theta-angle)*22.575)))
                res = self.udp.sendUDP("1 "+str(round((self.theta-angle)*22.575))+" "+str(round(-(self.theta-angle)*22.575)))
                self.theta = angle
                while(self.isMoving()):
                    self.scan()
                    time.sleep(0.2)
            logger.debug("Distance: "+str(distance))
            # move
            logger.debug("1 "+str(round(distance*215.58))+" "+str(round(distance*215.58)))
            res = self.udp.sendUDP("1 "+str(round(distance*215.58))+" "+str(round(distance*215.58)))
            self.x = target['x']
            self.y = target['y']
            while(self.isMoving()):
                self.scan()
                time.sleep(0.2)

class control(Thread):

    TRACE = 0

    def __init__(self, udp):
        Thread.__init__(self)
        self.tracefile = None
        self.traceline = 0
        self.traceData = {}
        self.lastFrameTimestamp = time.time()
        self.cycleTime = 0
        self.nav = navigation(udp)
        self._running = True
        if(self.TRACE == 1):
            self.initTrace()
        self.udp = udp

    def initTrace(self):
        if(self.TRACE == 1):
            self.tracefile = open("trace.csv","w+")
            header = "timestamp;"
            for k, v in self.traceData.iteritems():
                header += k+";"
            header += "\r\n"
            self.tracefile.write(header)

    def writeTrace(self):
        if (self.TRACE == 1):
            if self.traceline == 0:
                self.initTrace()
                self.traceline = 1
            filestring = str(time.time())+";"
            displaystring = ""
            for k, v in self.traceData.iteritems():
                displaystring += k+": "+str(v)+", "
                filestring += str(v)+";"
            filestring += "\r\n"
            #logger.debug(displaystring)
            self.tracefile.write(filestring)

    def terminate(self): 
        self._running = False

    def close(self):
        logger.debug("Closing control thread")
        if self.TRACE == 1 and self.tracefile != None:
            self.tracefile.close()

    def idleTask(self):
        pass
        #print("."),

    def runMission(self, command):
        self.nav.startMission(command)

    def runCommand(self, cmd):
        res = ""
        try:
            #logger.debug(cmd)
            command = json.loads(cmd)
            #logger.debug(command)
        except:
            logger.debug("Control thread received command: " + cmd)
            data = cmd.split(';')
            res = self.udp.sendUDP(cmd)
            return res
        self.runMission(command)
        return "ok"
        """ if(data[0] == "SERVO"):
            self.servos.setServoAngle(data[1], "shoulder", int(data[2]))
            self.servos.setServoAngle(data[1], "knee", int(data[3]))
            self.servos.setServoAngle(data[1], "hip", int(data[4]))
        elif(data[0] == "RESET"):
            self.servos.close()
        elif(data[0] == "CONFIG"):
            self.servos.readServosConfig()
            self.initialPosition() """

    def run(self):
        logger.debug('Control thread running')
        while self._running:
            time.sleep(0.05)
            ### Wait for command (call of runCommand by rpibot.py)
            self.idleTask()
        self.close()
        logger.debug('Control thread terminating')

    def stop(self, reason):
        logger.info("Stopped by "+reason)

# Run this if standalone (test purpose)
if __name__ == '__main__':

    try:
        logger.info("Started main")
        #s = sense.sense()
        #s.start()
        c = control()
        c.start()
        time.sleep(2)
        c.stop("Test")
    except KeyboardInterrupt:
        # Signal termination
        logger.info("Keyboard interrupt. Terminate thread")
    finally:
        c.terminate()
        #s.terminate()
        logger.debug("Thread terminated")

        # Wait for actual termination (if needed)
        c.join()
        #s.join()
        logger.debug("Thread finished")
