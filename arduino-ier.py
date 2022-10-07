#!/usr/bin/env python3
# MY CODE
try:
    import globals
except:
    pass
from grabPorts import grabPorts
from classes_text import *
from failing import *
from saving_data import *

# OTHER'S CODE
from datetime import datetime
import time
from time import sleep

try:
    import sys
except:
    pass
try:
    import tty
except:
    pass
try:
    import termios
except:
    pass

import glob
import keyboard
import serial

try:
    import winsound
except:
    pass
try:
    import os
except:
    pass
import numpy as np
import pandas as pd
import curses
import re
import struct
from scipy import signal


class ArdUIno(grabPorts):
    def __init__(
        self, winPort=None, num_ards=1, usb_port=None, n_modem=None, name="Arduino"
    ):

        self.ports = grabPorts()
        self.n_modem = n_modem
        self.usb_port = usb_port
        self.name = name
        self.ports.arduinoPort(winPort, num_ards, usb_port, self.n_modem)
        # printme(f'Arduino port: {print_var_name(self)}')
        print(str(self.ports.arduino_ports))

        if num_ards == 1:
            try:
                self.arduino = serial.Serial(
                    self.ports.arduino_ports[0], 9600, timeout=1
                )
            except IndexError:
                print("I cannot find any arduino boards!")
        elif num_ards > 1:
            self.arduino1 = serial.Serial(self.ports.arduino_ports[0], 9600, timeout=1)
            self.arduino2 = serial.Serial(self.ports.arduino_ports[1], 9600, timeout=1)

        self.arduino.flushInput()

    def readData(self, dataParser=float):
        self.read_parsed = None

        try:
            self.read = self.arduino.readline()
            self.read_parsed = dataParser(self.read)

        except Exception as e:
            print(f"Exception from arduino readData method {e}")