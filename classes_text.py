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

# My stuff
try:
    import globals
except:
    pass

from classes_arduino import ardUIno
from grabPorts import grabPorts

# Maths
import numpy as np
import pandas as pd
import curses


class textIO:
    def __init__(self):
        pass

    def intensity(self):

        while True:
            self.intense = input("\n From 0 to 10, how cold did that feel? (0 is no cold - 10 is painfully cold)  ")
            if self.intense in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'):
                break
            else:
                print('\n Only "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" and "10" are valid answers')
                continue

    def lowFam(self):
        while True:
            self.low_bound = input("\n What is the minimum temperature for COLTHER? ")
            try:
                self.low_bound = float(self.low_bound)
                break
            except:
                print("\n Only numbers are valid answers")
                continue

    def highFam(self):
        while True:
            self.high_bound = input("\n What is the maximum temperature for COLTHER? ")
            try:
                self.high_bound = float(self.high_bound)
                break
            except:
                print("\n Only numbers are valid answers")
                continue

    def amplitudeFam(self):
        while True:
            self.amplitude = input("\n What is the amplitude range for COLTHER?   ")
            try:
                self.amplitude = float(self.high_bound)/2
            except:
                print("\n Only numbers are valid answers")

    def CspotB(self):
        while True:
            self.Cwalle = input("\n Have we found a cold spot? (Y/n)   ")
            if self.Cwalle in ('Y', 'n'):
                break
            else:
                print("\n ")
                continue

    def printValues(self):
            while globals.status == None and globals.distance > globals.distance_limit and globals.elapsed < globals.time_limit:
                print('Temperature:  ' + str(globals.temp))
                print('Distance:  ' + str(globals.distance))

    def famOrder(self):
        while True:
            self.f_order = input("\n What spots are we finding first? (C / W)  ")
            if self.f_order in ('C', 'W'):
                break
            else:
                print("\n Only C and W are valid answers \n")
                continue

    def WspotB(self):
        while True:
            self.Wwalle = input("\n Have we found a warm spot? (Y/n)   ")
            if self.Wwalle in ('Y', 'n'):
                break
            else:
                print("\n ")
                continue

    def laserTfam(self):
        while True:
            self.laserT = input("\n At what temperature should the LASER be?    ")
            try:
                self.laserT = float(self.laserT)
                break
            except:
                print("\n Only numbers are valid answers")
                continue
    def TGIfam(self):
        while True:
            self.tgi_fam = input("\n Are we happy with the sensation? (Y/n)")
            if self.tgi_fam in ('Y', 'n'):
                break
            else:
                print("\n ")
                continue


    def famTGI(self):
        while True:
            self.famTGI= input("\n What familiarisation step are we doing now? (C / W / TGI)  ")
            if self.famTGI in ('C', 'W'):
                break
            else:
                print("\n Only C and W are valid answers \n")
                continue

    def spotTGIfam(self):
        while True:
            self.spot_TGIfam = input("What COLD spot would you like to choose? (C1/C2)")
            if self.spot_TGIfam in ('C1', 'C2'):
                break
            else:
                print("\n Only 'C1' and 'C2' are valid answers")
                continue
