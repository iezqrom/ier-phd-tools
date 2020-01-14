#!/usr/bin/env python3
import glob
import sys
import numpy as np

import re


class grabPorts(object):

    def __init__(self):
        try:
            self.ports = glob.glob('/dev/tty.*')
        except:
            pass

# [s for s in ports  if "usbmodem14{}{}01".format(1, 2) in s][0]

    def zaberPort(self, who, usb_port = None, n_modem = None, winPort = None):
        if sys.platform.startswith('win'):
            self.zaber_port = winPort
            # self.zaber_port = serial.Serial('COM{}'.format(winPort), baudrate = 115200, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE);

        elif sys.platform.startswith('darwin'):

            if who == 'serial':
                self.zaber_port = [s for s in self.ports if "serial" in s]

            elif who == 'modem':
                self.zaber_port = [s for s in self.ports if "usbmodem14{}{}01".format(usb_port, str(n_modem)) in s]

            try:
                print(self.zaber_port)
            except:
                print('There are not Zabers connected to the mac machine')

    def arduinoPort(self, winPort = None, num_ards = 1, usb_port = None, n_modem = None):
        if sys.platform.startswith('win'):
            if num_ards == 1:
                self.arduino_ports = winPort
            elif num_ards > 1:
                self.arduino_ports = []
                for i in winPort:
                    self.arduino_ports.append(winPort)

        elif sys.platform.startswith('darwin'):
            if num_ards == 1:
                self.arduino_ports = [s for s in self.ports  if "usbmodem14{}{}01".format(usb_port, n_modem) in s]

            elif num_ards > 1:
                self.arduino_ports = []
                for i in np.arange(len(n_ards)):
                    self.arduino_ports.append([s for s in self.ports  if "usbmodem142{}01".format(n_modem[i]) in s])
