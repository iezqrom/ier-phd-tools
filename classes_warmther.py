#!/usr/bin/env python3

#Time
from datetime import datetime
import time
from time import sleep
#System
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

import zaber.serial as zs

import keyboard
import serial
try:
    import winsound
except:
    pass

import matplotlib.pyplot as plt

# My stuff
try:
    import globals
except:
    pass

from classes_arduino import ArdUIno
from grabPorts import grabPorts
from pyd import PYD

# Maths
import numpy as np
import pandas as pd
import curses
import math
import struct

from pyd import PYD

def sineWave(set_point, amplitude, freq, phase = 0, repeats = 1):

    t = np.arange(0, repeats * 10, 0.01)
    w = 2 * math.pi * freq
    phi = phase # phase to change the phase of sine function

    A = ((set_point + amplitude/2) - (set_point - amplitude/2))/2
    wave = A * np.sin(w * t + phi) + ((set_point + amplitude/2) + (set_point - amplitude/2))/2

    # self.volt = np.tile(self.volt, repeats)
    # duration = int(1000 * repeats/globals.rate_NI) # duration of sound
    return wave

class Warm(ArdUIno):

    def __init__(self, winPort = None, num_ards = 1, usb_port = None, n_modem = None):
        self.Warm = ArdUIno(winPort, num_ards, usb_port, n_modem)

    def ROIPID(self, set_point, event1, radio, duration):

        previous_temp = globals.temp
        time.sleep(2)

        globals.stimulus = 1
        counter = 0

        try:
            timeout = time.time() + duration
            while True:

                if globals.stimulus == 1:
                    counter += 1

                    event1.wait()

                    if counter == 1:

                        ## PID parameters
                        Kp = -90
                        Ki = -40
                        Kd = -50
                        output_limits = (0, 128)

                        # we initialise PID object
                        PID = PYD(Kp, Ki, Kd, set_point, output_limits)

                    if keyboard.is_pressed('c'):
                        globals.pid_var = 128
                        globals.stimulus = 0

                    else:
                        globals.pid_var = PID(globals.temp)

                    print(globals.pid_var)

                    self.Warm.arduino.write(struct.pack('>B', int(globals.pid_var)))

                elif globals.stimulus == 0:
                    if keyboard.is_pressed('e'):
                        break

                previous_temp = globals.temp
                event1.clear()


        except KeyboardInterrupt:
            sys.exit(0)

#### developing

    def manual(self, cond):
        try:
            print('We start manual light manipulation')
            self.Warm.arduino.write(struct.pack('>B', int(globals.pid_var)))
            while True:
                # print('we are here')
                if keyboard.is_pressed('up'):
                    if globals.pid_var == 0:
                        print('Already at MAXIMUM intensity')
                    else:
                        globals.pid_var -= 1
                        self.Warm.arduino.write(struct.pack('>B', int(globals.pid_var)))
                    print('One up')
                    time.sleep(0.1)

                elif keyboard.is_pressed('down'):
                    if globals.pid_var == 128:
                        print('Already at MINIMUM intensity')
                    else:
                        globals.pid_var += 1
                        self.Warm.arduino.write(struct.pack('>B', int(globals.pid_var)))

                    print('One down')
                    time.sleep(0.1)

                elif keyboard.is_pressed('e'): ### TERMINATE
                    globals.pid_var = 128
                    self.Warm.arduino.write(struct.pack('>B', int(globals.pid_var)))
                    break

                elif keyboard.is_pressed('p'):
                    globals.centreROI[cond] = globals.indx0, globals.indy0
                    print(globals.centreROI[cond])
                    time.sleep(0.1)

                else:
                    continue

                print(globals.pid_var)

        finally:
            print('We are out')
            globals.pid_var = 128
            self.Warm.arduino.write(struct.pack('>B', int(globals.pid_var)))
