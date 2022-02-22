#!/usr/bin/env python3
import glob
import sys
import numpy as np

import re


class grabPorts(object):
    def __init__(self):
        try:
            self.ports = glob.glob("/dev/tty.*")
        except:
            pass

    # [s for s in ports  if "usbmodem14{}{}01".format(1, 2) in s][0]

    def zaberPort(
        self,
        who,
        head,
        tail2,
        tail1,
        surname_serial="A104BTL5",
        usb_port=None,
        n_modem=None,
        winPort=None,
    ):

        if sys.platform.startswith("win"):
            self.zaber_port = winPort
            # self.zaber_port = serial.Serial('COM{}'.format(winPort), baudrate = 115200, bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE);

        elif sys.platform.startswith("darwin"):
            # print("HELLO")
            # pri
            if who == "serial":
                self.zaber_port = [
                    s for s in self.ports if "serial" and surname_serial in s
                ]

                # print(self.zaber_port)

            elif who == "modem":
                # print(who)
                # print('HELLO')
                # print(f"usbmodem{str(head)}{str(usb_port)}{str(n_modem)}{str(tail2)}{str(tail1)}")
                # print([s for s in self.ports if f"usbmodem{str(usb_port)}{str(n_modem)}{str(tail2)}{str(tail1)}"])
                self.zaber_port = [
                    s
                    for s in self.ports
                    if f"usbmodem{str(head)}{str(usb_port)}{str(n_modem)}{str(tail2)}{str(tail1)}"
                    in s
                ]
                print(self.zaber_port)

            try:
                pass
            except:
                print("There are not Zabers connected to the mac machine")

    def arduinoPort(self, winPort=None, num_ards=1, usb_port=None, n_modem=None):
        if sys.platform.startswith("win"):
            if num_ards == 1:
                self.arduino_ports = winPort
            elif num_ards > 1:
                self.arduino_ports = []
                for i in winPort:
                    self.arduino_ports.append(winPort)

        elif sys.platform.startswith("darwin"):
            if num_ards == 1:
                self.arduino_ports = [
                    s
                    for s in self.ports
                    if "usbmodem14{}{}01".format(usb_port, n_modem) in s
                ]
                print(self.arduino_ports)

            elif num_ards > 1:
                self.arduino_ports = []
                for i in np.arange(len(n_ards)):
                    self.arduino_ports.append(
                        [
                            s
                            for s in self.ports
                            if "usbmodem142{}01".format(n_modem[i]) in s
                        ]
                    )
