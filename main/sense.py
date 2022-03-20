#!/usr/bin/env python
from __future__ import division

import os
import time
import logging
import serial
from threading import Thread
#import Adafruit_PCA9685
#from mpu9250_i2c import *
#import RPi.GPIO as GPIO
import datetime
import subprocess
import configparser
import sys
import data
import udp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

class sense(Thread):

    # Definition of class variables. Whould be nice to shift them in __init__ as instance variables.
    TRACE = 0
    SERIAL = 0
    IMU = 0

    #### INIT #################################
    def __init__(self, udp):
        Thread.__init__(self) 
        self._running = True
        if(self.SERIAL == 1):
            self.ser = serial.Serial('/dev/ttyS0', 115200, timeout=0.1)
        self.line = ''
        self.lastFrameTimestamp = time.time()
        self.cycleTime = 0
        #self.RT_data = {} # Real time data
        self.udp = udp
        
    def readSerial(self):
        res = False

        try:
            if(self.SERIAL == 1):
                self.line = self.ser.readline()   #read a '\n' terminated line (timeout set in open statement)
                if "MOV" in self.line:
                    self.cycleTime = int(round((time.time() - self.lastFrameTimestamp)*1000))
                    self.lastFrameTimestamp = time.time()
                res = True
            #print(self.line)
        except:
            logger.error("Serial readline error: "+self.line)
        return res

    def outputData(self):
        print (str(self.cycleTime) + " - RT_Data: ", str(data.RT_data))

    def decodeSerialFrame(self):
        try:
            data = self.line.split(';')
            if(data[0] == "MOV"):
                print("mov")
            elif(data[0] == "DBG"):
                print("dbg")
        except:
            logger.error("Frame not complete: "+self.line) # serial data was not complete

    def readIMU(self):
        if(self.IMU == 1):
            ax, wz, hdg, m_x, m_y = mpu9250_read()
            data.RT_data["ax"] = ax
            data.RT_data["wz"] = wz
            data.RT_data["hdg"] = hdg
            data.RT_data["m_x"] = m_x
            data.RT_data["m_y"] = m_y
            #print('accel [g]: x = {0:.2f}, wz = {1:.2f} , hdg = {2:.2f} '.format(ax,wz,hdg))

    def close(self):
        logging.info("Closing serial")
        if(self.SERIAL == 1):
            self.ser.close()

    def terminate(self):
        self._running = False

    def idleTask(self):
        #print(os.system(vcgencmd measure_temp))
        pass

    def run(self):
        #time.sleep(0.5)
        data.RT_data["test"] = "test data"
        if(self.SERIAL == 1):
            self.readSerial()
        while self._running:
            if(self.SERIAL == 1):
                if self.readSerial():
                    self.decodeSerialFrame()
            self.readIMU() ## Too long. Shift in a thread !!
            self.idleTask()
            time.sleep(0.1)
        self.close()

# Run this if standalone (test purpose)
if __name__ == '__main__':
    try:
        logging.info("Started main")
        s = sense()
        s.start()
        while(1):
            s.outputData()
            time.sleep(1.0)
    except KeyboardInterrupt:
        # Signal termination
        logging.info("Keyboard interrupt. Terminate thread")
        s.terminate()
        logging.debug("Thread terminated")

        # Wait for actual termination (if needed)
        s.join()
        logging.debug("Thread finished")

