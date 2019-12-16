#!/usr/bin/env python3
import glob
import sys
import numpy as np

import re


class grabPorts(object):

    def __init__(self):
        try:
            self.ports = glob.glob('/dev/tty.*')
            print('All ports' + self.ports)
        except:
            pass

    def zaberPort(self, who, n_modem = None, winPort = None):
        if sys.platform.startswith('win'):
            self.zaber_port = winPort
            # self.zaber_port = serial.Serial('COM{}'.format(winPort), baudrate = 115200, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE);

        elif sys.platform.startswith('darwin'):

            if who == 'serial':
                self.zaber_port = [s for s in self.ports if "serial" in s]

            elif who == 'modem':
                self.zaber_port = [s for s in self.ports if "usbmodem142{}01".format(str(n_modem)) in s]
                # print(self.zaber_port)
            try:
                print(self.zaber_port)
            except:
                print('There are not Zabers connected to the mac machine')

    def arduinoPort(self, winPort = None, num_ards = 1, n_modem = None):
        if sys.platform.startswith('win'):
            if num_ards == 1:
                self.arduino_port = winPort
            elif num_ards > 1:
                self.arduino_port = []
                for i in winPort:
                    self.arduino_ports.append(winPort)

        elif sys.platform.startswith('darwin'):
            if num_ards == 1:

                self.zaber_port = [s for s in self.ports  if "usbmodem142{}01".format(n_modem) in s]

            elif num_ards > 1:
                self.arduino_ports = []
                for i in np.arange(len(n_ards)):
                    self.arduino_ports.append([s for s in self.ports  if "usbmodem142{}01".format(n_modem[i]) in s])
