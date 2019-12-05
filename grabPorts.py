#!/usr/bin/env python3
import glob
import sys
import numpy as np


class grabPorts(object):

    def __init__(self):
        try:
            self.ports = glob.glob('/dev/tty.*')
        except:
            pass

    def zaberPort(self, winPort = None):
        if sys.platform.startswith('win'):
            self.zaber_port = winPort
            # self.zaber_port = serial.Serial('COM{}'.format(winPort), baudrate = 115200, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE);

        elif sys.platform.startswith('darwin'):
            for i in np.arange(len(self.ports)):
                if 'usbserial' in self.ports[i]:
                    self.zaber_port = self.ports[i]
                else:
                    pass
            try:
                print(self.zaber_port)
            except:
                print('There are not Zabers connected to the mac machine')

    def arduinoPort(self, winPort = None, num_ards = 1):
        if sys.platform.startswith('win'):
            if num_ards == 1:
                self.arduino_port = winPort
            elif num_ards > 1:
                self.arduino_port = []
                for i in winPort:
                    self.arduino_ports.append(winPort)

        elif sys.platform.startswith('darwin'):
            if num_ards == 1:
                for i in np.arange(len(self.ports)):
                    if 'usbmodem' in self.ports[i]:
                        self.arduino_ports = self.ports[i]
                    else:
                        pass
            elif num_ards > 1:
                self.arduino_ports = []
                for i in np.arange(len(self.ports)):
                    if 'usbmodem' in self.ports[i]:
                        self.arduino_ports.append(self.ports[i])
                    else:
                        pass
