#!/usr/bin/env python3
import glob
import sys
import numpy as np

import re


class grabPorts(object):
    def __init__(self):
        self.ports = glob.glob("/dev/tty.*")
        print(self.ports)

    def zaberPort(self, name, surname, winPort=None):

        if sys.platform.startswith("win"):
            self.zaber_port = winPort

        elif sys.platform.startswith("darwin"):
            name_zaber = str(name) + str(surname)

            zaber_connected = check_string_in_list(name_zaber, self.ports)

            if zaber_connected:
                self.zaber_port_list = [s for s in self.ports if name_zaber in s]
                self.zaber_port = self.zaber_port_list[0]
            else:
                raise Exception(f"Zaber {name_zaber} is not connected to the mac machine")


    def arduinoPort(self, winPort=None, num_ards=1, usbname = None):
        if sys.platform.startswith("win"):
            if num_ards == 1:
                self.arduino_ports = winPort
            elif num_ards > 1:
                self.arduino_ports = []
                for i in winPort:
                    self.arduino_ports.append(winPort)

        elif sys.platform.startswith("darwin"):
            if num_ards == 1:
                arduino_string = f"usbmodem{usbname}"
                print(arduino_string)
                self.arduino_ports = [
                    s
                    for s in self.ports
                    if arduino_string in s
                ]
                print(self.arduino_ports)

            elif num_ards > 1:
                self.arduino_ports = []
                for i in np.arange(len(num_ards)):
                    self.arduino_ports.append(
                        [
                            s
                            for s in self.ports
                            if arduino_string in s
                        ]
                    )

def check_string_in_list(string_to_search, list_of_strings):
    for elem in list_of_strings:
        if re.search(string_to_search, elem):
            return True
    return False