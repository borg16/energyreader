#!/usr/bin/python3

import datetime
import RPi.GPIO as GPIO
import time
import paho.mqtt.publish as publish

class EnergyReader:
    def __init__(self):
        self.previousStart = None
        self.previousEnd = None
        self.prevPreviousStart = None
        self.prevPreviousEnd = None
        self.count = 0
        self.skipped = 0
        self.previousCycle = 0
        
    def __enter__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.IN)
        GPIO.add_event_detect(4,GPIO.BOTH,self.transitCallback)

    def __exit__(self,a,b,c):
        GPIO.remove_event_detect(4)
        
    def transitCallback(self,channel):
        n = datetime.datetime.now()
        if GPIO.input(4)==0:
            if self.prevPreviousStart != None and self.prevPreviousEnd != None:
                cycle = self.previousEnd - self.prevPreviousEnd
                length = self.previousEnd - self.prevPreviousStart
                skipCycle = n - self.prevPreviousEnd
                nextLength = n - self.previousStart
                
                #print(str(nextLength/skipCycle)+' ' +str(length/cycle))
                
                #if not(0.035 < length / cycle < 0.45) and 0.035 < nextLength / skipCycle < 0.045:
                if (0.025 < nextLength / skipCycle < 0.065 and 0.8 < self.previousCycle / skipCycle < 1.3) \
                    or (length / cycle < 0.01 and nextLength / skipCycle > 0.04) \
                        or (length / cycle > 0.1 and nextLength / skipCycle < 0.1):
                    #print('Skip ' + str(length) + ' at ' + str(self.previousStart))
                    self.skipped = self.skipped + 1
                    self.previousEnd = n
                else:
                    time = self.prevPreviousEnd + cycle * 0.5
                    self.publishsingle(time,cycle,length)
                    self.previousCycle = cycle
                    self.count = self.count + 1
                    self.prevPreviousEnd = self.previousEnd
                    self.previousEnd = n
            else:
                self.prevPreviousEnd = self.previousEnd
                self.previousEnd = n
        else:
            self.prevPreviousStart = self.previousStart
            self.previousStart = n
        
    def publishsingle(self,time,cycle,length):
        p = 300000 / 8 / cycle.total_seconds()
        #print('{"ts":'
        #                    + str(int(time.timestamp()*1000))
        #                    +',"values":{"cycle":'+str(cycle.total_seconds())
        #                    +',"length":'+str(length.total_seconds())
        #                    +',"power":'+ str(p) + '}'
        #                    +'}')
        publish.single("v1/devices/me/attributes",
                       '{"count":' + str(self.count)
                       + ',skipped:' + str(self.skipped) + '}',
                       hostname = 'localhost',
                       port = 1884,
                       auth = { 'username' : '7eTEUqzEAzPdZXkeZYvV'})
        publish.single("v1/devices/me/telemetry",
                       '{"ts":'
                       + str(int(time.timestamp()*1000))
                       +',"values":{"cycle":'+str(cycle.total_seconds())
                       +',"length":'+str(length.total_seconds())
                       +',"power":'+ str(p) + '}'
                       +'}',
                       hostname = 'localhost',
                       port = 1884,
                       auth = { 'username' : '7eTEUqzEAzPdZXkeZYvV'})

if __name__ == "__main__":
    with EnergyReader():
        while True:
            time.sleep(600)

