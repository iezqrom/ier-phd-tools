#!/usr/bin/env python3


import numpy as np
import pandas as pd
import curses
import math

import struct
from scipy import stats
from scipy.interpolate import interp1d
import re
from termios import TCIFLUSH, tcflush
from datetime import datetime
from glob import glob
from os import pread
from sys import platform
import time
from time import sleep
import logging
import random

# System
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
try:
    import os
except:
    pass

import threading

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

from arduino import ArdUIno
from arduino import *
from grabPorts import grabPorts
from pyd import PYD
from saving_data import *
from text import *
from index_funcs import *

# Maths

from failing import *

################################################################################################################
################################################################################################################
############################ SYRINGE LOOK-UP TABLE (LUT)
################################################################################################################
################################################################################################################

end_220000 = 25.98
end_210000 = 27.17
end_200000 = 28.09
end_190000 = 28.78
end_170000 = 29.18
end_140000 = 30.78

ends = [end_220000, end_210000, end_200000, end_190000, end_170000, end_140000]
zebers = [220000, 210000, 200000, 190000, 170000, 140000]

slope, intercept, r_value, p_value, std_err = stats.linregress(zebers, ends)

# %%
y_vals = intercept + slope * np.asarray(zebers) + (33 - ends[-1])
zebers_inter = np.arange(220000, 140000, -150)
y_vals_inter = intercept + slope * zebers_inter + (33 - ends[-1])

default_rules = {
    "colther": {"x": True, "y": True, "z": True},
    "camera": {"x": False, "y": True, "z": True},
    "tactile": {"x": False, "y": True, "z": True},
}

default_grid = {"colther": None, "camera": None, "tactile": None}

default_ROIs = {}

default_amount = 10000

default_haxes = {
    "colther": ["z", "x", "y"],
    "camera": ["x", "z", "y"],
    "tactile": ["y", "x", "z"],
}

default_touch_z_offset = 52494

default_PanTilts = {
    "1": (37, 84, 66),
    "2": (24, 101, 48),
    "3": (29, 83, 61),
    "4": (39, 95, 63),
    "5": (31, 97, 57),
}

default_step_sizes = {"colther": 0.49609375, "camera": 0.1905, "tactile": 0.1905}

default_positions = {
    "colther": {"x": 233126, "y": 106874, "z": 0},
    "camera": {"x": 49507, "y": 535098, "z": 287000},
    "tactile": {"x": 336000, "y": 380000, "z": 270000},
}

zaber_models_default = {
    "colther": {"x": "end_X-LSQ150B", "y": "end_A-LSQ150B", "z": "end_A-LSQ150B"},
    "camera": {"x": "end_LSM100B-T4", "y": "end_LSM200B-T4", "z": "end_LSM100B-T4"},
    "tactile": {"x": "end_LSM100B-T4", "y": "end_LSM200B-T4", "z": "end_LSM100B-T4"},
}

zaber_models_end_default = {
    "end_X-LSQ150B": 305381,
    "end_A-LSQ150B": 305381,
    "end_LSM100B-T4": 533333,
    "end_LSM200B-T4": 1066667,
}

################################################################################################################
################################################################################################################
############################ CLASS
################################################################################################################
################################################################################################################
# logging.basicConfig(filename='./zaber_positions.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


class Zaber(grabPorts):
    """
    Zaber class developed by Ivan Ezquerra-Romano at the Action & Body lab (2018-2023)
    """

    def __init__(
        self,
        n_device,
        who,
        surname_serial="A104BTL5",
        usb_port=None,
        n_modem=None,
        winPort=None,
        port=None,
        head=14,
        tail2=0,
        tail1=1,
    ):
        self.ports = grabPorts()
        self.ports.zaberPort(
            who, head, tail2, tail1, surname_serial, usb_port, n_modem, winPort
        )
        self.home = False

        if n_device == 1:  # number 1 device is chosen to lead the Daisy chain
            try:
                print(self.ports.zaber_port)
                self.port = zs.AsciiSerial(self.ports.zaber_port)
            except:
                self.port = zs.AsciiSerial(self.ports.zaber_port[0])

            # print(self.port)
            self.device = zs.AsciiDevice(self.port, n_device)
        else:
            self.port = port
            self.device = zs.AsciiDevice(port.port, n_device)

        # print('DEVICE')
        # print(self.device)

    def move(self, amount):
        reply = self.device.move_rel(amount)
        print(reply)

    def manual(self):
        amount = input("Distance per click: (300-5000)")
        amount = int(amount)
        while True:
            move = input("Direction: (r for right | l for left | e to end)")
            if move in ("r"):
                self.move(amount)
            elif move in ("l"):
                self.move(0 - amount)
            elif move in ("e"):
                break
            else:
                print("\n Only r, l and e are valid answers")
                continue

    def manualCon1(self, devices, rules = default_rules):
        """
        Method for Object Zaber to move 3 axes in ONE zaber with keyboard presses.
        Like a game!
        """
        try:

            device = devices[globals.current_device]

            while True:
                #### Y axis
                if keyboard.is_pressed("up"):
                    try:
                        device["y"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )
                    except:
                        device["y"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("down"):
                    try:
                        device["y"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )
                    except:
                        device["y"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )

                #### X axis

                elif keyboard.is_pressed("left"):
                    try:
                        device["x"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )
                    except:
                        device["x"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("right"):
                    try:
                        device["x"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )
                    except:
                        device["x"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )

                ### Z axis
                elif keyboard.is_pressed("d"):
                    try:
                        device["z"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        device["z"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("u"):
                    try:
                        device["z"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        device["z"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    homingZabers(devices)
                    break

                # Press letter h and Zaber will home, first z axis, then y and finally x
                # Control

                elif keyboard.is_pressed("h"):
                    homingZabers(devices)

                elif keyboard.is_pressed("z"):
                    try:
                        posX = device[2].send("/get pos")
                    except:
                        posX = device[2].device.send("/get pos")

                    try:
                        posY = device[1].send("/get pos")
                    except:
                        posY = device[1].device.send("/get pos")

                    try:
                        posZ = device[0].send("/get pos")
                    except:
                        posZ = device[0].device.send("/get pos")

                    default_positions[globals.current_device][0] = int(posX.data)
                    default_positions[globals.current_device][1] = int(posY.data)
                    default_positions[globals.current_device][2] = int(posZ.data)

                    # logging.info(default_positions)

                else:
                    continue

        except Exception as e:
            print(e)

    def manualCon1Measure(self, devices, device, rules=default_rules):
        """
        Method for Object Zaber to move 3 axes in ONE zaber with keyboard presses.
        Like a game!
        """
        self.vector_coors = {"1": False, "2": False}
        start_end = "1"
        was_pressed = False

        try:
            while True:
                #### Y axis
                if keyboard.is_pressed("up"):
                    if not was_pressed:
                        try:
                            devices[device]["y"].move_rel(
                                0 - revDirection(device, "y", rules, default_amount)
                            )
                        except:
                            devices[device]["y"].device.move_rel(
                                0 - revDirection(device, "y", rules, default_amount)
                            )

                elif keyboard.is_pressed("down"):
                    if not was_pressed:
                        try:
                            devices[device]["y"].move_rel(
                                0 + revDirection(device, "y", rules, default_amount)
                            )
                        except:
                            devices[device]["y"].device.move_rel(
                                0 + revDirection(device, "y", rules, default_amount)
                            )

                elif keyboard.is_pressed("1"):
                    if not was_pressed:
                        start_end = "1"
                        was_pressed = True

                elif keyboard.is_pressed("2"):
                    if not was_pressed:
                        start_end = "2"
                        was_pressed = True

                #### X axis

                elif keyboard.is_pressed("left"):
                    if not was_pressed:
                        try:
                            devices[device]["x"].move_rel(
                                0 - revDirection(device, "x", rules, default_amount)
                            )
                        except:
                            devices[device]["x"].device.move_rel(
                                0 - revDirection(device, "x", rules, default_amount)
                            )

                        was_pressed = True

                elif keyboard.is_pressed("right"):
                    if not was_pressed:
                        try:
                            devices[device]["x"].move_rel(
                                0 + revDirection(device, "x", rules, default_amount)
                            )
                        except:
                            devices[device]["x"].device.move_rel(
                                0 + revDirection(device, "x", rules, default_amount)
                            )

                        was_pressed = True

                ### Z axis
                elif keyboard.is_pressed("d"):
                    if not was_pressed:
                        try:
                            devices[device]["z"].move_rel(
                                0 + revDirection(device, "z", rules, default_amount)
                            )
                        except:
                            devices[device]["z"].device.move_rel(
                                0 + revDirection(device, "z", rules, default_amount)
                            )

                        was_pressed = True

                elif keyboard.is_pressed("u"):
                    if not was_pressed:
                        try:
                            devices[device]["z"].move_rel(
                                0 - revDirection(device, "z", rules, default_amount)
                            )
                        except:
                            devices[device]["z"].device.move_rel(
                                0 - revDirection(device, "z", rules, default_amount)
                            )

                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    print(all(list(self.vector_coors.values())))
                    if all(list(self.vector_coors.values())):
                        homingZabers(devices)
                        break

                # Press letter h and Zaber will home, first z axis, then y and finally x
                # Control

                elif keyboard.is_pressed("h"):
                    if not was_pressed:
                        homingZabers(devices)
                        was_pressed = True

                elif keyboard.is_pressed("z"):
                    if not was_pressed:
                        try:
                            posX = devices[device]["x"].send("/get pos")
                        except:
                            posX = devices[device]["x"].device.send("/get pos")

                        try:
                            posY = devices[device]["y"].send("/get pos")
                        except:
                            posY = devices[device]["y"].device.send("/get pos")

                        try:
                            posZ = devices[device]["z"].send("/get pos")
                        except:
                            posZ = devices[device]["z"].device.send("/get pos")

                        self.vector_coors[start_end] = [
                            int(posX.data),
                            int(posY.data),
                            int(posZ.data),
                        ]
                        printme(self.vector_coors)
                        was_pressed = True

                else:
                    was_pressed = False
                    continue

        except Exception as e:
            print(e)

    def manualCon2(self, devices, arduino=None, home="y", rules=default_rules):
        """
        Method for Object Zabers to move the three axes of TWO zabers with keyboard presses.
        Like a game!
        """
        was_pressed = False

        if home not in ("y", "n"):
            print("Invalid value for 'home', only 'y' and 'n' are valid values")
            print("'y' selected by default")
            home = "y"

        print("Zaber game activated")

        if arduino != None:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        try:
            device = devices[globals.current_device]

            while True:
                #### Y axis
                if keyboard.is_pressed("up"):
                    try:
                        device["y"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )
                    except:
                        device["y"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("down"):
                    try:
                        device["y"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )
                    except:
                        device["y"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )

                #### X axis

                elif keyboard.is_pressed("left"):
                    try:
                        device["x"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )
                    except:
                        device["x"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("right"):
                    try:
                        device["x"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )
                    except:
                        device["x"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )

                ### Z axis
                elif keyboard.is_pressed("d"):
                    try:
                        device["z"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        device["z"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("u"):
                    try:
                        device["z"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        device["z"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("p"):
                    if not was_pressed:
                        globals.centreROI = [globals.indx0, globals.indy0]
                        print(f"Centre of ROI is: {globals.centreROI}")
                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    vars = [globals.centreROI, default_positions]
                    if all(v is not None for v in vars) and home == "n":
                        print("Terminating Zaber game \n")
                        break

                    elif all(v is not None for v in vars) and home == "y":
                        homingZabers(devices)
                        break
                    else:
                        print("You are missing something...")
                        print(globals.centreROI, default_positions)

                #### GET POSITION

                elif keyboard.is_pressed("z"):
                    if not was_pressed:
                        try:
                            posX = device["x"].send("/get pos")

                        except:
                            posX = device["x"].device.send("/get pos")

                        try:
                            posY = device["y"].send("/get pos")
                        except:
                            posY = device["y"].device.send("/get pos")

                        try:
                            posZ = device["z"].send("/get pos")
                        except:
                            posZ = device["z"].device.send("/get pos")

                        default_positions[globals.current_device]["x"] = int(posX.data)
                        default_positions[globals.current_device]["y"] = int(posY.data)
                        default_positions[globals.current_device]["z"] = int(posZ.data)

                        print(default_positions)
                        # logging.info(default_positions)
                        was_pressed = True

                # Press letter h and Zaber will home, first z axis, then y and finally x
                # Control

                elif keyboard.is_pressed("h"):
                    homingZabers(devices)

                elif keyboard.is_pressed("o"):  # Open Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 1
                        arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                elif keyboard.is_pressed("c"):  # Close Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 0
                        arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                #### Double

                elif keyboard.is_pressed("k"):
                    if not was_pressed:
                        device = devices["camera"]
                        globals.current_device = "camera"
                        print(f"\nControlling CAMERA zaber")
                        was_pressed = True

                elif keyboard.is_pressed("f"):
                    if not was_pressed:
                        device = devices["colther"]
                        globals.current_device = "colther"
                        print(f"\nControlling COLTHER zaber")
                        was_pressed = True

                else:
                    was_pressed = False

        finally:
            if arduino != None:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def manualCon3(
        self, devices, arduino=None, home="y", rules=default_rules, end_button="e"
    ):
        """
        Method for Object Zaber to move the 3 axes of THREE zabers with keyboard presses. Like a game!
        The coordinates of two positions can be saved with 'z' and 'x'
        This method was created and it is specific to the experiment in which we measure cold
        thresholds with and without touch
        """
        was_pressed = False

        if home not in ("y", "n"):
            print("Invalid value for 'home', only 'y' and 'n' are valid values")
            print("'y' selected by default")
            home = "y"

        if arduino:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        print("Zaber game activated")

        try:
            device = devices[globals.current_device]

            while True:
                if keyboard.is_pressed("up"):
                    try:
                        response = device["y"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )
                    except:
                        response = device["y"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )

                    handleOutOfRange(
                        response,
                        device,
                        "y",
                        globals.current_device,
                        default_amount,
                        zaber_models_default,
                        zaber_models_end_default,
                    )

                elif keyboard.is_pressed("down"):
                    try:
                        response = device["y"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )
                    except:
                        response = device["y"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "y", rules, default_amount
                            )
                        )

                    handleOutOfRange(
                        response,
                        device,
                        "y",
                        globals.current_device,
                        default_amount,
                        zaber_models_default,
                        zaber_models_end_default,
                    )

                #### X axis

                elif keyboard.is_pressed("left"):
                    try:
                        response = device["x"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )
                    except:
                        response = device["x"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )

                    handleOutOfRange(
                        response,
                        device,
                        "x",
                        globals.current_device,
                        default_amount,
                        zaber_models_default,
                        zaber_models_end_default,
                    )

                elif keyboard.is_pressed("right"):
                    try:
                        response = device["x"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )
                    except:
                        response = device["x"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "x", rules, default_amount
                            )
                        )

                    handleOutOfRange(
                        response,
                        device,
                        "x",
                        globals.current_device,
                        default_amount,
                        zaber_models_default,
                        zaber_models_end_default,
                    )

                ### Z axis
                elif keyboard.is_pressed("d"):
                    try:
                        response = device["z"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        response = device["z"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                    handleOutOfRange(
                        response,
                        device,
                        "z",
                        globals.current_device,
                        default_amount,
                        zaber_models_default,
                        zaber_models_end_default,
                    )

                elif keyboard.is_pressed("u"):
                    try:
                        response = device["z"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        response = device["z"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                    handleOutOfRange(
                        response,
                        device,
                        "z",
                        globals.current_device,
                        default_amount,
                        zaber_models_default,
                        zaber_models_end_default,
                    )

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 500
                        was_pressed = True

                elif keyboard.is_pressed("o"):  # Open Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 1
                        if arduino:
                            arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                elif keyboard.is_pressed("c"):  # Close Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 0
                        if arduino:
                            arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed(f"{end_button}"):
                    vars = [globals.centreROI, default_positions]
                    if all(v is not None for v in vars) and home == "n":
                        print("Terminating Zaber game \n")
                        break

                    elif all(v is not None for v in vars) and home == "y":
                        homingZabers(devices)
                        break
                    else:
                        print("You are missing something...")
                        print(globals.centreROI, default_positions)

                #### GET POSITION

                elif keyboard.is_pressed("p"):
                    if not was_pressed:
                        try:
                            posX = device["x"].send("/get pos")

                        except:
                            posX = device["x"].device.send("/get pos")

                        try:
                            posY = device["y"].send("/get pos")
                        except:
                            posY = device["y"].device.send("/get pos")

                        try:
                            posZ = device["z"].send("/get pos")
                        except:
                            posZ = device["z"].device.send("/get pos")

                        default_positions[globals.current_device]["x"] = int(posX.data)
                        default_positions[globals.current_device]["y"] = int(posY.data)
                        default_positions[globals.current_device]["z"] = int(posZ.data)

                        printme(default_positions[globals.current_device])
                        # logging.info(default_positions)
                        was_pressed = True

                # Press letter h and Zaber will home, first z axis, then y and finally x
                # Control

                elif keyboard.is_pressed("h"):
                    homingZabers(devices)

                #### Triple

                elif keyboard.is_pressed("k"):
                    if not was_pressed:
                        device = devices["camera"]
                        globals.current_device = "camera"
                        print(f"Controlling CAMERA zabers")
                        was_pressed = True

                elif keyboard.is_pressed("f"):
                    if not was_pressed:
                        device = devices["colther"]
                        globals.current_device = "colther"
                        print(f"Controlling COLTHER zabers")
                        was_pressed = True

                elif keyboard.is_pressed("t"):
                    if not was_pressed:
                        device = devices["tactile"]
                        globals.current_device = "tactile"
                        print(f"Controlling TACTILE zabers")
                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        default_amount = changeAmount("a")

                        was_pressed = True

                else:
                    was_pressed = False
                    continue

        finally:
            if arduino:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def manualCon3PanTilt(
        self,
        devices,
        ardpantilt,
        arduino=None,
        home="y",
        rules=default_rules,
        end_button="e",
    ):
        """
        Method for Object Zaber to move the 3 axes of THREE zabers with keyboard presses. Like a game!
        The coordinates of two positions can be saved with 'z' and 'x'
        This method was created and it is specific to the experiment in which we measure cold
        thresholds with and without touch
        """
        was_pressed = False
        pantilt_on = True

        if home not in ("y", "n"):
            print("Invalid value for 'home', only 'y' and 'n' are valid values")
            print("'y' selected by default")
            home = "y"

        if arduino:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        keydelay = 0.15
        print("Zaber game activated")

        try:
            device = devices[globals.current_device]

            while True:
                if keyboard.is_pressed("up"):
                    if pantilt_on and globals.current_device == "camera":
                        ardpantilt.arduino.write(struct.pack(">B", 3))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("down"):
                    if pantilt_on and globals.current_device == "camera":
                        ardpantilt.arduino.write(struct.pack(">B", 4))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("right"):
                    if pantilt_on and globals.current_device == "camera":
                        ardpantilt.arduino.write(struct.pack(">B", 2))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("left"):
                    if pantilt_on and globals.current_device == "camera":
                        ardpantilt.arduino.write(struct.pack(">B", 1))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("u"):
                    if pantilt_on and globals.current_device == "camera":
                        ardpantilt.arduino.write(struct.pack(">B", 5))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("d"):
                    if pantilt_on and globals.current_device == "camera":
                        ardpantilt.arduino.write(struct.pack(">B", 6))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 500
                        was_pressed = True

                elif keyboard.is_pressed("o"):  # Open Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 1
                        if arduino:
                            arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                elif keyboard.is_pressed("c"):  # Close Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 0
                        if arduino:
                            arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed(f"{end_button}"):
                    vars = [globals.centreROI, default_positions]
                    if all(v is not None for v in vars) and home == "n":
                        print("Terminating Zaber game \n")
                        break

                    elif all(v is not None for v in vars) and home == "y":
                        homingZabers(devices)
                        break
                    else:
                        print("You are missing something...")
                        print(globals.centreROI, default_positions)

                #### GET POSITION
                elif keyboard.is_pressed("p"):
                    if not was_pressed:
                        try:
                            posX = device["x"].send("/get pos")

                        except:
                            posX = device["x"].device.send("/get pos")

                        try:
                            posY = device["y"].send("/get pos")
                        except:
                            posY = device["y"].device.send("/get pos")

                        try:
                            posZ = device["z"].send("/get pos")
                        except:
                            posZ = device["z"].device.send("/get pos")

                        default_positions[globals.current_device]["x"] = int(posX.data)
                        default_positions[globals.current_device]["y"] = int(posY.data)
                        default_positions[globals.current_device]["z"] = int(posZ.data)

                        printme(default_positions[globals.current_device])
                        # logging.info(default_positions)
                        was_pressed = True

                # Press letter h and Zaber will home, first z axis, then y and finally x
                # Control

                elif keyboard.is_pressed("h"):
                    homingZabers(devices)

                #### Triple

                elif keyboard.is_pressed("k"):
                    if not was_pressed:
                        pantilt_on = not pantilt_on
                        device = devices["camera"]
                        globals.current_device = "camera"
                        print(f"Controlling CAMERA zabers")
                        was_pressed = True

                elif keyboard.is_pressed("f"):
                    if not was_pressed:
                        device = devices["colther"]
                        globals.current_device = "colther"
                        print(f"Controlling COLTHER zabers")
                        was_pressed = True

                elif keyboard.is_pressed("t"):
                    if not was_pressed:
                        device = devices["tactile"]
                        globals.current_device = "tactile"
                        print(f"Controlling TACTILE zabers")
                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        default_amount = changeAmount("a")

                        was_pressed = True

                else:
                    was_pressed = False
                    continue

        finally:
            if arduino:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def gridCon2(
        self,
        devices,
        arduino=None,
        home="y",
        grid=default_grid,
        rois=default_ROIs,
        rules=default_rules,
        amount=default_amount,
        haxes=default_haxes,
    ):
        """
        Method for Object Zaber to move the 3 axes of THREE zabers with keyboard presses. Like a game!
        The coordinates of two positions can be saved with 'z' and 'x'
        This method was created and it is specific to the experiment in which we measure cold
        thresholds with and without touch
        """

        self.rois = rois
        was_pressed = False

        if arduino != None:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        # Build dictionary of rois
        r_zaber = random.choice(list(grid))
        self.rois = {}
        grid_i = list(np.arange(1, len(grid[r_zaber]) + 0.1, 1))
        for i in grid_i:
            self.rois[str(int(i))] = []

        if home not in ("y", "n"):
            print("Invalid value for 'home', only 'y' and 'n' are valid values")
            print("'y' selected by default")
            home = "y"

        print("\nZaber game activated\n")

        try:
            # device = devices[globals.current_device]
            current_roi = "1"

            while True:

                if keyboard.is_pressed("p"):
                    if not was_pressed:
                        self.rois[current_roi] = [globals.indx0, globals.indy0]
                        print(f"Centre of ROI is: {self.rois[current_roi]}")
                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    vars = [globals.centreROI, default_positions]
                    if all(v is not None for v in vars) and home == "n":
                        printme("Terminating Zaber game")
                        break

                    elif all(v is not None for v in vars) and home == "y":
                        homingZabers(devices)
                        break
                    else:
                        print("You are missing something...")
                        print(globals.centreROI, default_positions)

                elif keyboard.is_pressed("d"):  # Open Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 6
                        arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                elif keyboard.is_pressed("o"):  # Open Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 1
                        arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                elif keyboard.is_pressed("c"):  # Close Arduino shutter
                    if not was_pressed:
                        globals.stimulus = 0
                        arduino.arduino.write(struct.pack(">B", globals.stimulus))
                        time.sleep(0.1)
                        was_pressed = True

                elif keyboard.is_pressed("h"):
                    homingZabers(devices)

                elif keyboard.is_pressed("g"):
                    if not was_pressed:
                        print(self.rois)
                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) + 1)
                        if int(current_roi) > len(grid[globals.current_device]):
                            current_roi = "1"

                        moveZabersUp(devices, ["colther"])

                        for k, v in reversed(haxes.items()):
                            if k != "tactile":
                                movetostartZabersConcu(
                                    devices,
                                    k,
                                    list(reversed(v)),
                                    pos=grid[k][current_roi],
                                )

                        was_pressed = True

                elif keyboard.is_pressed("z"):
                    if not was_pressed:
                        try:
                            posXf = devices["colther"]["x"].send("/get pos")

                        except:
                            posXf = devices["colther"]["x"].device.send("/get pos")

                        try:
                            posYf = devices["colther"]["y"].send("/get pos")
                        except:
                            posYf = devices["colther"]["y"].device.send("/get pos")

                        try:
                            posZf = devices["colther"]["z"].send("/get pos")
                        except:
                            posZf = devices["colther"]["z"].device.send("/get pos")

                        try:
                            posXk = devices["camera"]["x"].send("/get pos")

                        except:
                            posXk = devices["camera"]["x"].device.send("/get pos")

                        try:
                            posYk = devices["camera"]["y"].send("/get pos")
                        except:
                            posYk = devices["camera"]["y"].device.send("/get pos")

                        try:
                            posZk = devices["camera"]["z"].send("/get pos")
                        except:
                            posZk = devices["camera"]["z"].device.send("/get pos")

                        print("CAMERA")
                        print(posXk, posYk, posZk)

                        print("COLTHER")
                        print(posXf, posYf, posZf)
                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) - 1)
                        if int(current_roi) == 0:
                            current_roi = "1"

                        moveZabersUp(devices, ["colther"])

                        for k, v in reversed(haxes.items()):
                            if k != "tactile":
                                movetostartZabersConcu(
                                    devices,
                                    k,
                                    list(reversed(v)),
                                    pos=grid[k][current_roi],
                                )

                        was_pressed = True

                else:
                    was_pressed = False
                    continue

        finally:
            if arduino != None:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def gridUpDown(
        self,
        devices,
        current_device,
        current_roi="1",
        home="y",
        grid=default_grid,
        haxes=default_haxes,
        rules=default_rules,
    ):
        was_pressed = False

        self.gridZs = grid
        printme(self.gridZs)

        roi_selector = 0

        try:
            while True:
                if keyboard.is_pressed("e"):

                    if (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "y"
                    ):
                        try:
                            globals.weDone = True
                        except Exception as e:
                            errorloc(e)
                        homingZabers(devices)
                        break
                    elif (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "n"
                    ):
                        printme("Terminating Zaber game")
                        break
                    else:
                        print("You are missing something...")
                        print(grid[current_device])
                        was_pressed = True

                elif keyboard.is_pressed("d"):
                    try:
                        devices[current_device]["z"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        devices[current_device]["z"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("u"):
                    try:
                        devices[current_device]["z"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        devices[current_device]["z"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("p"):
                    if not was_pressed:
                        try:
                            posXf = devices[current_device]["x"].send("/get pos")

                        except:
                            posXf = devices[current_device]["x"].device.send("/get pos")

                        try:
                            posYf = devices[current_device]["y"].send("/get pos")
                        except:
                            posYf = devices[current_device]["y"].device.send("/get pos")

                        try:
                            posZf = devices[current_device]["z"].send("/get pos")
                        except:
                            posZf = devices[current_device]["z"].device.send("/get pos")

                        self.gridZs[current_device][current_roi]["x"] = int(posXf.data)
                        self.gridZs[current_device][current_roi]["y"] = int(posYf.data)
                        self.gridZs[current_device][current_roi]["z"] = int(posZf.data)

                        printme(self.gridZs[current_device])

                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        roi_selector += 1

                        print(len(grid[globals.current_device]))
                        if (roi_selector + 1) > len(grid[globals.current_device]):
                            roi_selector = 0

                        print(roi_selector)
                        current_roi = str(
                            list(default_grid[globals.current_device].keys())[
                                roi_selector
                            ]
                        )

                        k = "tactile"
                        moveZabersUp(devices, [k])
                        movetostartZabersConcu(
                            devices,
                            k,
                            list(reversed(haxes[k])),
                            pos=self.gridZs[k][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("b"):
                    if not was_pressed:
                        roi_selector -= 1
                        if roi_selector == -1:
                            roi_selector = len(list(grid[current_device].keys())) - 1

                            current_roi = str(list(grid[current_device].keys())[-1])

                        print(roi_selector)
                        current_roi = str(
                            list(default_grid[globals.current_device].keys())[
                                roi_selector
                            ]
                        )

                        k = "tactile"
                        moveZabersUp(devices, [k])
                        movetostartZabersConcu(
                            devices,
                            k,
                            list(reversed(haxes[k])),
                            pos=self.gridZs[k][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True
                else:
                    was_pressed = False
        except Exception as e:
            errorloc(e)

    def gridUpDownArc(
        self,
        devices,
        current_device,
        arcs,
        dist_z,
        current_angle_arc,
        current_roi="1",
        home="y",
        grid=default_grid,
        haxes=default_haxes,
        rules=default_rules,
    ):
        was_pressed = False
        current_pos_arc = None

        self.gridZs = grid
        printme(self.gridZs)

        try:
            while True:
                if keyboard.is_pressed("e"):

                    if (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "y"
                    ):
                        try:
                            globals.weDone = True
                        except Exception as e:
                            errorloc(e)
                        homingZabers(devices)
                        break
                    elif (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "n"
                    ):
                        printme("Terminating Zaber game")
                        break
                    else:
                        print("You are missing something...")
                        print(grid[current_device])
                        was_pressed = True

                elif keyboard.is_pressed("d"):
                    try:
                        devices[current_device]["z"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        devices[current_device]["z"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("u"):
                    try:
                        devices[current_device]["z"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        devices[current_device]["z"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True

                elif keyboard.is_pressed("7"):
                    if not was_pressed:
                        default_amount = 100000
                        was_pressed = True

                elif keyboard.is_pressed("right"):
                    if any(i == current_roi for i in list(arcs.keys())):
                        current_angle_arc[current_roi] = (
                            current_angle_arc[current_roi] - 1
                        )

                        if current_angle_arc[current_roi] < min(
                            list(arcs[current_roi].keys())
                        ) or current_angle_arc[current_roi] > max(
                            list(arcs[current_roi].keys())
                        ):
                            current_angle_arc[current_roi] = (
                                current_angle_arc[current_roi] + 1
                            )

                        current_pos_arc = arcs[current_roi][
                            current_angle_arc[current_roi]
                        ]
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["x", "y"],
                            {"x": current_pos_arc[0], "y": current_pos_arc[1]},
                        )
                        # print(current_angle_arc)
                        # print(current_pos_arc)
                        was_pressed = True

                elif keyboard.is_pressed("left"):
                    if any(i == current_roi for i in list(arcs.keys())):
                        current_angle_arc[current_roi] = (
                            current_angle_arc[current_roi] + 1
                        )

                        if current_angle_arc[current_roi] < min(
                            list(arcs[current_roi].keys())
                        ) or current_angle_arc[current_roi] > max(
                            list(arcs[current_roi].keys())
                        ):
                            current_angle_arc[current_roi] = (
                                current_angle_arc[current_roi] - 1
                            )

                        current_pos_arc = arcs[current_roi][
                            current_angle_arc[current_roi]
                        ]
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["x", "y"],
                            {"x": current_pos_arc[0], "y": current_pos_arc[1]},
                        )
                        # print(current_angle_arc[current_roi])
                        # print(current_pos_arc)
                        was_pressed = True

                elif keyboard.is_pressed("p"):
                    if not was_pressed:
                        try:
                            posXf = devices[current_device]["x"].send("/get pos")

                        except:
                            posXf = devices[current_device]["x"].device.send("/get pos")

                        try:
                            posYf = devices[current_device]["y"].send("/get pos")
                        except:
                            posYf = devices[current_device]["y"].device.send("/get pos")

                        try:
                            posZf = devices[current_device]["z"].send("/get pos")
                        except:
                            posZf = devices[current_device]["z"].device.send("/get pos")

                        self.gridZs[current_device][current_roi]["x"] = int(posXf.data)
                        self.gridZs[current_device][current_roi]["y"] = int(posYf.data)
                        self.gridZs[current_device][current_roi]["z"] = int(posZf.data)

                        printme(self.gridZs[current_device])

                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) + 1)

                        if int(current_roi) > len(grid[globals.current_device]):
                            current_roi = "1"

                        k = "tactile"
                        if not any(self.gridZs[k][current_roi].values()):
                            previous_roi = str(int(current_roi) - 1)
                            if any(self.gridZs[k][previous_roi].values()):
                                range_angles = np.arange(
                                    (current_angle_arc[current_roi] - 30),
                                    (current_angle_arc[current_roi] + 30),
                                    1,
                                )

                                for angle in range_angles:
                                    temp_angle_pos = vectorEnd(
                                        [
                                            self.gridZs[k][previous_roi]["x"],
                                            self.gridZs[k][previous_roi]["y"],
                                        ],
                                        dist_z,
                                        angle,
                                    )
                                    if all(i > 0 for i in temp_angle_pos):
                                        arcs[current_roi][angle] = [
                                            temp_angle_pos[0],
                                            temp_angle_pos[1],
                                            0,
                                        ]

                                self.gridZs[k][current_roi] = {
                                    "x": arcs[current_roi][
                                        current_angle_arc[current_roi]
                                    ][0],
                                    "y": arcs[current_roi][
                                        current_angle_arc[current_roi]
                                    ][1],
                                    "z": arcs[current_roi][
                                        current_angle_arc[current_roi]
                                    ][2],
                                }
                            else:
                                current_roi = str(int(current_roi) + 2)
                                print(len(grid[globals.current_device]))
                                if int(current_roi) > len(grid[globals.current_device]):
                                    current_roi = "1"

                        printme(f"Current ROI: {current_roi}")
                        moveZabersUp(devices, [k])
                        print(self.gridZs[k][current_roi])
                        movetostartZabersConcu(
                            devices,
                            k,
                            list(reversed(haxes[k])),
                            pos=self.gridZs[k][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("b"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) - 1)
                        if int(current_roi) == 0:
                            current_roi = str(list(grid[current_device].keys())[-1])

                        k = "tactile"

                        if not any(self.gridZs[k][current_roi].values()):
                            previous_roi = str(int(current_roi) - 1)

                            if any(self.gridZs[k][previous_roi].values()):
                                range_angles = np.arange(
                                    (current_angle_arc[current_roi] - 30),
                                    (current_angle_arc[current_roi] + 30),
                                    1,
                                )

                                for angle in range_angles:
                                    temp_angle_pos = vectorEnd(
                                        [
                                            self.gridZs[k][previous_roi]["x"],
                                            self.gridZs[k][previous_roi]["y"],
                                        ],
                                        dist_z,
                                        angle,
                                    )
                                    if all(i > 0 for i in temp_angle_pos):
                                        arcs[current_roi][angle] = [
                                            temp_angle_pos[0],
                                            temp_angle_pos[1],
                                            0,
                                        ]
                            else:
                                current_roi = "2"

                        printme(f"Current ROI: {current_roi}")
                        moveZabersUp(devices, [k])
                        movetostartZabersConcu(
                            devices,
                            k,
                            list(reversed(haxes[k])),
                            pos=self.gridZs[k][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        default_amount = changeAmount("a")

                        was_pressed = True

                else:
                    was_pressed = False
        except Exception as e:
            errorloc(e)

    def gridUpDownArcf(
        self,
        devices,
        current_device,
        arcs,
        current_angle_arc,
        current_roi="1",
        home="y",
        grid=default_grid,
        haxes=default_haxes,
        rules=default_rules,
    ):
        """
        Move along arc from fixed master point
        """
        was_pressed = False
        current_pos_arc = None

        self.gridZs = grid
        printme(self.gridZs)

        try:
            while True:
                if keyboard.is_pressed("e"):

                    if (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "y"
                    ):
                        try:
                            globals.weDone = True
                        except Exception as e:
                            errorloc(e)
                        homingZabers(devices)
                        break
                    elif (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "n"
                    ):
                        printme("Terminating Zaber game")
                        break
                    else:
                        print("You are missing something...")
                        print(grid[current_device])
                        was_pressed = True

                elif keyboard.is_pressed("d"):
                    try:
                        devices[current_device]["z"].move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        devices[current_device]["z"].device.move_rel(
                            0
                            + revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("u"):
                    try:
                        devices[current_device]["z"].move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )
                    except:
                        devices[current_device]["z"].device.move_rel(
                            0
                            - revDirection(
                                globals.current_device, "z", rules, default_amount
                            )
                        )

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True

                elif keyboard.is_pressed("7"):
                    if not was_pressed:
                        default_amount = 100000
                        was_pressed = True

                elif keyboard.is_pressed("right"):
                    if any(i == current_roi for i in list(arcs.keys())):
                        current_angle_arc[current_roi] = (
                            current_angle_arc[current_roi] - 1
                        )

                        if current_angle_arc[current_roi] < min(
                            list(arcs[current_roi].keys())
                        ) or current_angle_arc[current_roi] > max(
                            list(arcs[current_roi].keys())
                        ):
                            current_angle_arc[current_roi] = (
                                current_angle_arc[current_roi] + 1
                            )

                        current_pos_arc = arcs[current_roi][
                            current_angle_arc[current_roi]
                        ]
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["x", "y"],
                            {"x": current_pos_arc[0], "y": current_pos_arc[1]},
                        )
                        # print(current_angle_arc)
                        # print(current_pos_arc)
                        was_pressed = True

                elif keyboard.is_pressed("left"):
                    if any(i == current_roi for i in list(arcs.keys())):
                        current_angle_arc[current_roi] = (
                            current_angle_arc[current_roi] + 1
                        )

                        if current_angle_arc[current_roi] < min(
                            list(arcs[current_roi].keys())
                        ) or current_angle_arc[current_roi] > max(
                            list(arcs[current_roi].keys())
                        ):
                            current_angle_arc[current_roi] = (
                                current_angle_arc[current_roi] - 1
                            )

                        current_pos_arc = arcs[current_roi][
                            current_angle_arc[current_roi]
                        ]
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["x", "y"],
                            {"x": current_pos_arc[0], "y": current_pos_arc[1]},
                        )
                        # print(current_angle_arc[current_roi])
                        # print(current_pos_arc)
                        was_pressed = True

                elif keyboard.is_pressed("p"):
                    if not was_pressed:
                        try:
                            posXf = devices[current_device]["x"].send("/get pos")

                        except:
                            posXf = devices[current_device]["x"].device.send("/get pos")

                        try:
                            posYf = devices[current_device]["y"].send("/get pos")
                        except:
                            posYf = devices[current_device]["y"].device.send("/get pos")

                        try:
                            posZf = devices[current_device]["z"].send("/get pos")
                        except:
                            posZf = devices[current_device]["z"].device.send("/get pos")

                        self.gridZs[current_device][current_roi]["x"] = int(posXf.data)
                        self.gridZs[current_device][current_roi]["y"] = int(posYf.data)
                        self.gridZs[current_device][current_roi]["z"] = int(posZf.data)

                        printme(self.gridZs[current_device])

                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) + 1)

                        if int(current_roi) > len(grid[globals.current_device]):
                            current_roi = "2"

                        k = "tactile"
                        self.gridZs[k][current_roi] = {
                            "x": arcs[current_roi][current_angle_arc[current_roi]][0],
                            "y": arcs[current_roi][current_angle_arc[current_roi]][1],
                            "z": arcs[current_roi][current_angle_arc[current_roi]][2],
                        }

                        printme(f"Current ROI: {current_roi}")
                        moveZabersUp(devices, [k])
                        print(self.gridZs[k][current_roi])
                        movetostartZabersConcu(
                            devices,
                            k,
                            list(reversed(haxes[k])),
                            pos=self.gridZs[k][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("b"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) - 1)
                        if int(current_roi) == 0 or int(current_roi) == 1:
                            current_roi = str(list(grid[current_device].keys())[-1])

                        k = "tactile"
                        self.gridZs[k][current_roi] = {
                            "x": arcs[current_roi][current_angle_arc[current_roi]][0],
                            "y": arcs[current_roi][current_angle_arc[current_roi]][1],
                            "z": arcs[current_roi][current_angle_arc[current_roi]][2],
                        }

                        printme(f"Current ROI: {current_roi}")
                        moveZabersUp(devices, [k])
                        movetostartZabersConcu(
                            devices,
                            k,
                            list(reversed(haxes[k])),
                            pos=self.gridZs[k][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        default_amount = changeAmount("a")

                        was_pressed = True

                else:
                    was_pressed = False
        except Exception as e:
            errorloc(e)

    def gridAround(
        self,
        devices,
        current_device,
        current_roi="1",
        home="y",
        grid=default_grid,
        haxes=default_haxes,
    ):
        was_pressed = False

        try:
            while True:
                if keyboard.is_pressed("e"):

                    if (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "y"
                    ):
                        try:
                            globals.weDone = True
                        except Exception as e:
                            errorloc(e)
                        homingZabers(devices)
                        break
                    elif (
                        not any(
                            [
                                default_grid[current_device][x]["z"] == 0
                                for x in default_grid[current_device]
                            ]
                        )
                        and home == "n"
                    ):
                        printme("Terminating Zaber game")
                        break
                    else:
                        print("You are missing something...")
                        print(grid[current_device])
                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) + 1)
                        print(len(grid[globals.current_device]))
                        if int(current_roi) > len(grid[globals.current_device]):
                            current_roi = "1"

                        moveZabersUp(devices, [current_device])
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["x", "y"],
                            pos=grid[current_device][current_roi],
                        )
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["z"],
                            pos=grid[current_device][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("b"):
                    if not was_pressed:
                        current_roi = str(int(current_roi) - 1)
                        if int(current_roi) == 0:
                            current_roi = str(list(grid[current_device].keys())[-1])
                            print(current_roi)

                        moveZabersUp(devices, [current_device])
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["x", "y"],
                            pos=grid[current_device][current_roi],
                        )
                        movetostartZabersConcu(
                            devices,
                            current_device,
                            ["z"],
                            pos=grid[current_device][current_roi],
                        )

                        was_pressed = True

                else:
                    was_pressed = False
        except Exception as e:
            errorloc(e)

    def gridCon3pantilt(
        self,
        devices,
        ardpantilt,
        platformcamera=None,
        arduino=None,
        default_pan_tilt_values=default_PanTilts,
        grid=default_grid,
        haxes=default_haxes,
        rules=default_rules,
    ):
        """
        (for dermatome distance experiment) Method for Object Zaber to move the 3 axes of THREE zabers with keyboard presses. Like a game!
        The coordinates of two positions can be saved with 'z' and 'x'
        This method was created and it is specific to the experiment in which we measure cold
        thresholds with and without touch
        """

        was_pressed = False
        pantilt_on = True
        default_camera = False
        touched = False
        three_reversed = False
        # print(default_pan_tilt_values)
        camera_pan_tilt2 = {0: default_pan_tilt_values["2"], 1: (83, 41, 36)}
        camera_position_zaber = {
            0: grid["camera"]["2"].copy(),
            1: {"x": 356247, "y": 1018906, "z": 23039},
        }
        pre_touch = grid["tactile"]["4"]["z"] - default_touch_z_offset

        if arduino:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        # Build dictionary of rois
        r_zaber = random.choice(list(grid))

        self.rois = {}
        self.PanTilts = {}
        self.gridcamera = grid["camera"]

        grid_i = list(np.arange(1, len(grid[r_zaber]) + 0.1, 1))
        for i in grid_i:
            self.rois[str(int(i))] = []

        keydelay = 0.15
        pan, tilt, head = 0, 0, 0
        device = devices["camera"]
        # print(default_pan_tilt_values)
        move_platform_camera = globals.move_platform_camera
        move_platform_camera_4 = globals.move_platform_camera_4
        backwards_colther = 10079
        positions_touch = {"1": "2", "2": "1", "3": "2", "4": "3"}
        checked = {"1": True, "2": True, "3": True, "4": True}
        reversed_checking = ["2", "4"]

        movetostartZabersConcu(devices, "tactile", ["z"], pos=globals.base_touch)
        moveAxisTo(devices, "tactile", "x", 533332)

        print("\nZaber game activated\n")

        globals.current_device = "camera"
        try:
            # device = devices[globals.current_device]
            current_roi = "1"

            while True:
                try:
                    red = ardpantilt.arduino.readline()
                except Exception as e:
                    errorloc(e)

                if keyboard.is_pressed("p"):
                    if not was_pressed:
                        if len(str(red)) > 10:
                            try:
                                pan, tilt, head = str(red)[2:-5].split("-")
                            except Exception as e:
                                errorloc(e)
                        self.rois[current_roi] = [globals.indx0, globals.indy0]
                        print(pan, tilt, head)
                        default_pan_tilt_values[current_roi] = [
                            int(pan),
                            int(tilt),
                            int(head),
                        ]

                        try:
                            posXk = devices["camera"]["x"].send("/get pos")

                        except:
                            posXk = devices["camera"]["x"].device.send("/get pos")

                        try:
                            posYk = devices["camera"]["y"].send("/get pos")
                        except:
                            posYk = devices["camera"]["y"].device.send("/get pos")

                        try:
                            posZk = devices["camera"]["z"].send("/get pos")
                        except:
                            posZk = devices["camera"]["z"].device.send("/get pos")

                        print(f"Centre of ROI is: {self.rois[current_roi]}")
                        print(f"Pan/tilt head position is: {pan} {tilt} {head}")
                        print(
                            f"Position camera: {int(posXk.data)} {int(posYk.data)} {int(posZk.data)}"
                        )

                        self.gridcamera[current_roi]["x"] = int(posXk.data)
                        self.gridcamera[current_roi]["y"] = int(posYk.data)
                        self.gridcamera[current_roi]["z"] = int(posZk.data)

                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    # print([len(n) < 2 for n in list(self.rois.values())])
                    if not any(
                        [len(n) < 2 for n in list(self.rois.values())]
                    ) and not any(list(checked.values())):
                        self.PanTilts = default_pan_tilt_values
                        try:
                            globals.weDone = True
                        except Exception as e:
                            errorloc(e)
                        break
                    else:
                        print("You are missing something...")
                        print(self.rois, self.PanTilts, checked)
                        was_pressed = True

                elif keyboard.is_pressed("k"):
                    if not was_pressed:
                        pantilt_on = not pantilt_on
                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        globals.stimulus = 6
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True

                elif keyboard.is_pressed("7"):
                    if not was_pressed:
                        default_amount = 50000
                        was_pressed = True

                elif keyboard.is_pressed("o"):
                    if not was_pressed:
                        globals.stimulus = 1
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("c"):
                    if not was_pressed:
                        globals.stimulus = 0
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("up"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 3))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("down"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 4))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("right"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 2))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("left"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 1))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("u"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 5))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("d"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 6))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("h"):
                    triggered_exception(
                        zabers=devices,
                        platform=platformcamera,
                        arduino_syringe=arduino,
                        arduino_pantilt=ardpantilt,
                    )

                elif keyboard.is_pressed("g"):
                    if not was_pressed:
                        print("ROIS")
                        print(self.rois)
                        print("Pan tilt")
                        print(default_pan_tilt_values)
                        print("Camera positions")
                        print(self.gridcamera)
                        print("Checked Touch")
                        print(checked)
                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        if (
                            touched
                            and current_roi == "1"
                            or current_roi == "3"
                            or three_reversed
                        ):
                            devices["colther"]["z"].device.move_abs(0)
                            movetostartZabersConcu(
                                devices, "tactile", ["z"], pos=pre_touch
                            )
                            moveAxisTo(devices, "tactile", "x", 533332)
                            moveAxisTo(devices, "tactile", "y", 1)
                        else:
                            devices["colther"]["z"].device.move_abs(0)
                            movetostartZabersConcu(devices, "tactile", ["z"], pre_touch)
                            moveAxisTo(devices, "tactile", "y", 1)
                            moveAxisTo(devices, "tactile", "x", 533332)

                        touched = False
                        three_reversed = False

                        current_roi = str(int(current_roi) + 1)
                        if int(current_roi) > len(grid[globals.current_device]):
                            current_roi = "1"

                        moveZabersUp(devices, ["colther"])

                        try:
                            devices["colther"]["x"].device.move_abs(backwards_colther)
                        except:
                            devices["colther"]["x"].move_abs(backwards_colther)

                        moveZabersUp(devices, ["camera"], uppos=0)
                        print(default_pan_tilt_values)
                        movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

                        movetostartZabersConcu(
                            devices,
                            "camera",
                            ["x", "y"],
                            pos=grid["camera"][current_roi],
                        )
                        movetostartZabersConcu(
                            devices, "camera", ["z"], pos=grid["camera"][current_roi]
                        )
                        movetostartZabersConcu(
                            devices,
                            "colther",
                            list(reversed(haxes["colther"])),
                            pos=grid["colther"][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("b"):
                    if not was_pressed:
                        if (
                            touched
                            and current_roi == "1"
                            or current_roi == "3"
                            or three_reversed
                        ):
                            devices["colther"]["z"].device.move_abs(0)
                            movetostartZabersConcu(
                                devices, "tactile", ["z"], pos=pre_touch
                            )
                            moveAxisTo(devices, "tactile", "x", 533332)
                            moveAxisTo(devices, "tactile", "y", 1)
                        else:
                            devices["colther"]["z"].device.move_abs(0)
                            movetostartZabersConcu(
                                devices, "tactile", ["z"], pos=pre_touch
                            )
                            moveAxisTo(devices, "tactile", "y", 1)
                            moveAxisTo(devices, "tactile", "x", 533332)

                        touched = False
                        three_reversed = False

                        current_roi = str(int(current_roi) - 1)
                        if int(current_roi) == 0:
                            current_roi = list(grid["colther"].keys())[-1]

                        moveZabersUp(devices, ["colther"])
                        try:
                            devices["colther"]["x"].device.move_abs(backwards_colther)
                        except:
                            devices["colther"]["x"].move_abs(backwards_colther)

                        moveZabersUp(devices, ["camera"], uppos=0)
                        movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

                        movetostartZabersConcu(
                            devices,
                            "camera",
                            ["x", "y"],
                            pos=grid["camera"][current_roi],
                        )
                        movetostartZabersConcu(
                            devices, "camera", ["z"], pos=grid["camera"][current_roi]
                        )
                        movetostartZabersConcu(
                            devices,
                            "colther",
                            list(reversed(haxes["colther"])),
                            pos=grid["colther"][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("z"):
                    if not was_pressed:
                        try:
                            posXf = devices["colther"]["x"].send("/get pos")

                        except:
                            posXf = devices["colther"]["x"].device.send("/get pos")

                        try:
                            posYf = devices["colther"]["y"].send("/get pos")
                        except:
                            posYf = devices["colther"]["y"].device.send("/get pos")

                        try:
                            posZf = devices["colther"]["z"].send("/get pos")
                        except:
                            posZf = devices["colther"]["z"].device.send("/get pos")

                        try:
                            posXk = devices["camera"]["x"].send("/get pos")

                        except:
                            posXk = devices["camera"]["x"].device.send("/get pos")

                        try:
                            posYk = devices["camera"]["y"].send("/get pos")
                        except:
                            posYk = devices["camera"]["y"].device.send("/get pos")

                        try:
                            posZk = devices["camera"]["z"].send("/get pos")
                        except:
                            posZk = devices["camera"]["z"].device.send("/get pos")

                        try:
                            posXt = devices["tactile"]["x"].send("/get pos")

                        except:
                            posXt = devices["tactile"]["x"].device.send("/get pos")

                        try:
                            posYt = devices["tactile"]["y"].send("/get pos")
                        except:
                            posYt = devices["tactile"]["y"].device.send("/get pos")

                        try:
                            posZt = devices["tactile"]["z"].send("/get pos")
                        except:
                            posZt = devices["tactile"]["z"].device.send("/get pos")

                        print("CAMERA")
                        print(posXk, posYk, posZk)

                        print("COLTHER")
                        print(posXf, posYf, posZf)

                        print("TACTILE")
                        print(posXt, posYt, posZt)

                        print("Pan/tilt position")
                        print(red)
                        was_pressed = True

                elif keyboard.is_pressed("t"):
                    if not was_pressed:
                        if not touched:
                            if current_roi == "1" or current_roi == "3":
                                devices["colther"]["z"].device.move_abs(0)
                                movetostartZabersConcu(
                                    devices, "tactile", ["z"], pos=pre_touch
                                )
                                moveAxisTo(
                                    devices,
                                    "tactile",
                                    "y",
                                    grid["tactile"][positions_touch[current_roi]]["y"],
                                )
                                moveAxisTo(
                                    devices,
                                    "tactile",
                                    "x",
                                    grid["tactile"][positions_touch[current_roi]]["x"],
                                )
                                moveAxisTo(
                                    devices,
                                    "tactile",
                                    "z",
                                    grid["tactile"][positions_touch[current_roi]]["z"],
                                )
                                moveAxisTo(
                                    devices,
                                    "colther",
                                    "z",
                                    grid["colther"][current_roi]["z"],
                                )

                            else:
                                movetostartZabersConcu(
                                    devices, "tactile", ["z"], pos=pre_touch
                                )
                                moveAxisTo(
                                    devices,
                                    "tactile",
                                    "x",
                                    grid["tactile"][positions_touch[current_roi]]["x"],
                                )
                                moveAxisTo(
                                    devices,
                                    "tactile",
                                    "y",
                                    grid["tactile"][positions_touch[current_roi]]["y"],
                                )
                                moveAxisTo(
                                    devices,
                                    "tactile",
                                    "z",
                                    grid["tactile"][positions_touch[current_roi]]["z"],
                                )
                                moveAxisTo(
                                    devices,
                                    "colther",
                                    "z",
                                    grid["colther"][current_roi]["z"],
                                )

                        elif touched:
                            if current_roi == "1" or current_roi == "3":
                                devices["colther"]["z"].device.move_abs(0)
                                movetostartZabersConcu(
                                    devices, "tactile", ["z"], pos=pre_touch
                                )
                                moveAxisTo(devices, "tactile", "x", 533332)
                                moveAxisTo(devices, "tactile", "y", 1)
                                moveAxisTo(
                                    devices,
                                    "colther",
                                    "z",
                                    grid["colther"][current_roi]["z"],
                                )
                            else:
                                movetostartZabersConcu(
                                    devices, "tactile", ["z"], pos=pre_touch
                                )
                                moveAxisTo(devices, "tactile", "y", 1)
                                moveAxisTo(devices, "tactile", "x", 533332)
                                moveAxisTo(
                                    devices,
                                    "colther",
                                    "z",
                                    grid["colther"][current_roi]["z"],
                                )

                        touched = not touched
                        checked[current_roi] = False
                        was_pressed = True

                else:
                    was_pressed = False
                    continue

        finally:
            if arduino:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def gridCon3pantiltD(
        self,
        devices,
        ardpantilt,
        platformcamera=None,
        arduino=None,
        default_pan_tilt_values=default_PanTilts,
        grid=default_grid,
        haxes=default_haxes,
        rules=default_rules,
    ):
        """
        (for skin distance experiment) Method for Object Zaber to move the 3 axes of THREE zabers with keyboard presses. Like a game!
        The coordinates of two positions can be saved with 'z' and 'x'
        This method was created and it is specific to the experiment in which we measure cold
        thresholds with and without touch
        """

        was_pressed = False
        pantilt_on = True
        touched = {"1": False, "2": False, "3": False, "4": False}
        checked = {"1": True, "2": True, "3": True, "4": True}

        if arduino:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        # Build dictionary of rois
        r_zaber = random.choice(list(grid))

        self.rois = {}
        self.PanTilts = {}
        self.gridcamera = grid["camera"]

        grid_i = list(np.arange(1, len(grid[r_zaber]) + 0.1, 1))
        for i in grid_i:
            self.rois[str(int(i))] = []

        keydelay = 0.15
        pan, tilt, head = 0, 0, 0
        device = devices["camera"]

        backwards_colther = 10079

        funcs = [
            [movetostartZabersConcu, [devices, "tactile", ["z"], globals.base_touch]],
            [moveAxisTo, [devices, "tactile", "x", globals.tactile_x_save]],
        ]
        threadFunctions(funcs)

        print("\nZaber game activated\n")

        globals.current_device = "camera"
        try:
            current_roi = "1"
            while True:
                try:
                    red = ardpantilt.arduino.readline()
                except Exception as e:
                    errorloc(e)

                if keyboard.is_pressed("p"):
                    if not was_pressed:
                        if len(str(red)) > 10:
                            try:
                                pan, tilt, head = str(red)[2:-5].split("-")
                            except Exception as e:
                                errorloc(e)
                        self.rois[current_roi] = [globals.indx0, globals.indy0]
                        print(pan, tilt, head)
                        default_pan_tilt_values[current_roi] = [
                            int(pan),
                            int(tilt),
                            int(head),
                        ]

                        try:
                            posXk = devices["camera"]["x"].send("/get pos")

                        except:
                            posXk = devices["camera"]["x"].device.send("/get pos")

                        try:
                            posYk = devices["camera"]["y"].send("/get pos")
                        except:
                            posYk = devices["camera"]["y"].device.send("/get pos")

                        try:
                            posZk = devices["camera"]["z"].send("/get pos")
                        except:
                            posZk = devices["camera"]["z"].device.send("/get pos")

                        print(f"Centre of ROI is: {self.rois[current_roi]}")
                        print(f"Pan/tilt head position is: {pan} {tilt} {head}")
                        print(
                            f"Position camera: {int(posXk.data)} {int(posYk.data)} {int(posZk.data)}"
                        )

                        self.gridcamera[current_roi]["x"] = int(posXk.data)
                        self.gridcamera[current_roi]["y"] = int(posYk.data)
                        self.gridcamera[current_roi]["z"] = int(posZk.data)

                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed("e"):

                    if not any(
                        [len(n) < 2 for n in list(self.rois.values())]
                    ) and not any(list(checked.values())):
                        self.PanTilts = default_pan_tilt_values
                        try:
                            globals.weDone = True
                        except Exception as e:
                            errorloc(e)
                        break
                    else:
                        print("You are missing something...")
                        print(self.rois, self.PanTilts, checked)
                        was_pressed = True

                elif keyboard.is_pressed("k"):
                    if not was_pressed:
                        pantilt_on = not pantilt_on
                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        globals.stimulus = 6
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True

                elif keyboard.is_pressed("7"):
                    if not was_pressed:
                        default_amount = 50000
                        was_pressed = True

                elif keyboard.is_pressed("o"):
                    if not was_pressed:
                        globals.stimulus = 1
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("c"):
                    if not was_pressed:
                        globals.stimulus = 0
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("up"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 3))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("down"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 4))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("right"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 2))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("left"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 1))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("u"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 5))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("d"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 6))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("h"):
                    triggered_exception(
                        zabers=devices,
                        arduino_syringe=arduino,
                        arduino_pantilt=ardpantilt,
                    )

                elif keyboard.is_pressed("g"):
                    if not was_pressed:
                        print(f"Current spot: {current_roi}")
                        print("ROIS")
                        print(self.rois)
                        print("Pan tilt")
                        print(default_pan_tilt_values)
                        print("Camera positions")
                        print(self.gridcamera)
                        print("Checked Touch")
                        print(checked)
                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        if len([k for k, v in touched.items() if v]) == 1:
                            movetostartZabersConcu(
                                devices,
                                "tactile",
                                ["z"],
                                (
                                    grid["tactile"][
                                        [k for k, v in touched.items() if v][0]
                                    ]["z"]
                                    - default_touch_z_offset * 1.3
                                ),
                            )

                        funcs = [
                            [moveZabersUp, [devices, ["colther"]]],
                            [
                                moveAxisTo,
                                [devices, "tactile", "x", globals.tactile_x_save],
                            ],
                            [moveAxisTo, [devices, "camera", "x", globals.camera_back]],
                        ]

                        threadFunctions(funcs)
                        for i in touched:
                            touched[i] = False

                        current_roi = str(int(current_roi) + 1)
                        if int(current_roi) > len(grid[globals.current_device]):
                            current_roi = "1"

                        movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

                        movetostartZabersConcu(
                            devices, "camera", ["y", "z"], grid["camera"][current_roi]
                        )
                        movetostartZabersConcu(
                            devices, "camera", ["x"], grid["camera"][current_roi]
                        )
                        movetostartZabersConcu(
                            devices,
                            "colther",
                            list(reversed(haxes["colther"])),
                            grid["colther"][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("b"):
                    if not was_pressed:
                        if len([k for k, v in touched.items() if v]) == 1:
                            movetostartZabersConcu(
                                devices,
                                "tactile",
                                ["z"],
                                (
                                    grid["tactile"][
                                        [k for k, v in touched.items() if v][0]
                                    ]["z"]
                                    - default_touch_z_offset * 1.3
                                ),
                            )

                        funcs = [
                            [moveZabersUp, [devices, ["colther"]]],
                            [
                                moveAxisTo,
                                [devices, "tactile", "x", globals.tactile_x_save],
                            ],
                            [moveAxisTo, [devices, "camera", "x", globals.camera_back]],
                        ]

                        threadFunctions(funcs)
                        for i in touched:
                            touched[i] = False

                        current_roi = str(int(current_roi) - 1)
                        if int(current_roi) == 0:
                            current_roi = list(grid["colther"].keys())[-1]

                        movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

                        movetostartZabersConcu(
                            devices,
                            "camera",
                            ["y", "z"],
                            pos=grid["camera"][current_roi],
                        )
                        movetostartZabersConcu(
                            devices, "camera", ["x"], pos=grid["camera"][current_roi]
                        )
                        movetostartZabersConcu(
                            devices,
                            "colther",
                            list(reversed(haxes["colther"])),
                            pos=grid["colther"][current_roi],
                        )

                        was_pressed = True

                elif keyboard.is_pressed("z"):
                    if not was_pressed:
                        try:
                            posXf = devices["colther"]["x"].send("/get pos")

                        except:
                            posXf = devices["colther"]["x"].device.send("/get pos")

                        try:
                            posYf = devices["colther"]["y"].send("/get pos")
                        except:
                            posYf = devices["colther"]["y"].device.send("/get pos")

                        try:
                            posZf = devices["colther"]["z"].send("/get pos")
                        except:
                            posZf = devices["colther"]["z"].device.send("/get pos")

                        try:
                            posXk = devices["camera"]["x"].send("/get pos")

                        except:
                            posXk = devices["camera"]["x"].device.send("/get pos")

                        try:
                            posYk = devices["camera"]["y"].send("/get pos")
                        except:
                            posYk = devices["camera"]["y"].device.send("/get pos")

                        try:
                            posZk = devices["camera"]["z"].send("/get pos")
                        except:
                            posZk = devices["camera"]["z"].device.send("/get pos")

                        try:
                            posXt = devices["tactile"]["x"].send("/get pos")

                        except:
                            posXt = devices["tactile"]["x"].device.send("/get pos")

                        try:
                            posYt = devices["tactile"]["y"].send("/get pos")
                        except:
                            posYt = devices["tactile"]["y"].device.send("/get pos")

                        try:
                            posZt = devices["tactile"]["z"].send("/get pos")
                        except:
                            posZt = devices["tactile"]["z"].device.send("/get pos")

                        print("CAMERA")
                        print(posXk, posYk, posZk)

                        print("COLTHER")
                        print(posXf, posYf, posZf)

                        print("TACTILE")
                        print(posXt, posYt, posZt)

                        print("Pan/tilt position")
                        print(red)
                        was_pressed = True

                elif keyboard.is_pressed("1"):
                    if not was_pressed and not touched["1"] and current_roi == "2":
                        funcs = [
                            [moveZabersUp, [devices, ["colther"]]],
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "tactile",
                                    ["z"],
                                    (
                                        grid["tactile"]["4"]["z"]
                                        - default_touch_z_offset
                                        * globals.up_modifier_touch_height
                                    ),
                                ],
                            ],
                        ]

                        threadFunctions(funcs)

                        movetostartZabersConcu(
                            devices, "tactile", ["y"], grid["tactile"]["1"]
                        )
                        movetostartZabersConcu(
                            devices, "tactile", ["x"], grid["tactile"]["1"]
                        )
                        touch = default_grid["tactile"]["1"]["z"] + round(
                            default_touch_z_offset * globals.down_modifier_touch_height
                        )
                        moveAxisTo(devices, "tactile", "z", touch)

                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                        for i in touched:
                            touched[i] = False

                    elif not was_pressed and touched["1"] and current_roi == "2":
                        devices["colther"]["z"].device.move_abs(0)
                        movetostartZabersConcu(
                            devices,
                            "tactile",
                            ["z"],
                            (
                                grid["tactile"]["1"]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            ),
                        )
                        moveAxisTo(devices, "tactile", "x", globals.tactile_x_save)
                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                    touched["1"] = not touched["1"]
                    checked["1"] = False
                    was_pressed = True

                elif keyboard.is_pressed("2"):
                    if not was_pressed and not touched["2"] and current_roi == "1":
                        funcs = [
                            [moveZabersUp, [devices, ["colther"]]],
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "tactile",
                                    ["z"],
                                    (
                                        grid["tactile"]["2"]["z"]
                                        - default_touch_z_offset
                                        * globals.up_modifier_touch_height
                                    ),
                                ],
                            ],
                        ]

                        threadFunctions(funcs)

                        movetostartZabersConcu(
                            devices, "tactile", ["x", "y"], grid["tactile"]["2"]
                        )
                        touch = default_grid["tactile"]["2"]["z"] + round(
                            default_touch_z_offset * globals.down_modifier_touch_height
                        )
                        moveAxisTo(devices, "tactile", "z", touch)

                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                        for i in touched:
                            touched[i] = False

                    elif not was_pressed and touched["2"] and current_roi == "1":
                        devices["colther"]["z"].device.move_abs(0)
                        movetostartZabersConcu(
                            devices,
                            "tactile",
                            ["z"],
                            (
                                grid["tactile"]["2"]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            ),
                        )
                        moveAxisTo(devices, "tactile", "x", globals.tactile_x_save)
                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                    touched["2"] = not touched["2"]
                    checked["2"] = False
                    was_pressed = True

                elif keyboard.is_pressed("3"):
                    if not was_pressed and not touched["3"] and current_roi == "1":
                        funcs = [
                            [moveZabersUp, [devices, ["colther"]]],
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "tactile",
                                    ["z"],
                                    (
                                        grid["tactile"]["3"]["z"]
                                        - default_touch_z_offset
                                        * globals.up_modifier_touch_height
                                    ),
                                ],
                            ],
                        ]

                        threadFunctions(funcs)

                        movetostartZabersConcu(
                            devices, "tactile", ["x", "y"], grid["tactile"]["3"]
                        )
                        touch = default_grid["tactile"]["3"]["z"] + round(
                            default_touch_z_offset * globals.down_modifier_touch_height
                        )
                        moveAxisTo(devices, "tactile", "z", touch)

                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                        for i in touched:
                            touched[i] = False

                    elif not was_pressed and touched["3"] and current_roi == "1":
                        devices["colther"]["z"].device.move_abs(0)
                        movetostartZabersConcu(
                            devices,
                            "tactile",
                            ["z"],
                            (
                                grid["tactile"]["3"]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            ),
                        )
                        moveAxisTo(devices, "tactile", "x", globals.tactile_x_save)
                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                    touched["3"] = not touched["3"]
                    checked["3"] = False
                    was_pressed = True

                elif keyboard.is_pressed("4"):
                    if not was_pressed and not touched["4"] and current_roi == "1":
                        funcs = [
                            [moveZabersUp, [devices, ["colther"]]],
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "tactile",
                                    ["z"],
                                    (
                                        grid["tactile"]["4"]["z"]
                                        - default_touch_z_offset
                                        * globals.up_modifier_touch_height
                                    ),
                                ],
                            ],
                        ]

                        threadFunctions(funcs)

                        movetostartZabersConcu(
                            devices, "tactile", ["x", "y"], grid["tactile"]["4"]
                        )
                        touch = default_grid["tactile"]["4"]["z"] + round(
                            default_touch_z_offset * globals.down_modifier_touch_height
                        )
                        moveAxisTo(devices, "tactile", "z", touch)

                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                        for i in touched:
                            touched[i] = False

                    elif not was_pressed and touched["4"] and current_roi == "1":
                        devices["colther"]["z"].device.move_abs(0)
                        movetostartZabersConcu(
                            devices,
                            "tactile",
                            ["z"],
                            (
                                grid["tactile"]["4"]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            ),
                        )
                        moveAxisTo(devices, "tactile", "x", globals.tactile_x_save)
                        moveAxisTo(
                            devices, "colther", "z", grid["colther"][current_roi]["z"]
                        )

                    touched["4"] = not touched["4"]
                    checked["4"] = False
                    was_pressed = True

                else:
                    was_pressed = False
                    continue

        finally:
            if arduino:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def gridCon3pantiltScaling(
        self,
        devices,
        ardpantilt,
        platformcamera=None,
        arduino=None,
        default_pan_tilt_values=default_PanTilts,
        grid=default_grid,
        haxes=default_haxes,
        rules=default_rules,
    ):
        """
        (for dermatome distance experiment) Method for Object Zaber to move the 3 axes of THREE zabers with keyboard presses. Like a game!
        The coordinates of two positions can be saved with 'z' and 'x'
        This method was created and it is specific to the experiment in which we measure cold
        thresholds with and without touch
        """

        was_pressed = False
        pantilt_on = True

        touched = False

        if arduino:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        # Build dictionary of rois
        r_zaber = "camera"

        self.rois = {}
        self.PanTilts = {}
        self.gridcamera = grid["camera"]

        grid_i = list(np.arange(1, len(grid[r_zaber]) + 0.1, 1))
        for i in grid_i:
            self.rois[str(int(i))] = []

        keydelay = 0.15
        pan, tilt, head = 0, 0, 0
        device = devices["camera"]

        print("\nZaber game activated\n")

        globals.current_device = "camera"
        try:
            # device = devices[globals.current_device]
            current_roi = "1"

            while True:
                try:
                    red = ardpantilt.arduino.readline()
                except Exception as e:
                    errorloc(e)

                if keyboard.is_pressed("p"):
                    if not was_pressed:
                        if len(str(red)) > 10:
                            try:
                                pan, tilt, head = str(red)[2:-5].split("-")
                            except Exception as e:
                                errorloc(e)
                        self.rois[current_roi] = [globals.indx0, globals.indy0]
                        default_pan_tilt_values[current_roi] = [
                            int(pan),
                            int(tilt),
                            int(head),
                        ]

                        try:
                            posXk = devices["camera"]["x"].send("/get pos")

                        except:
                            posXk = devices["camera"]["x"].device.send("/get pos")

                        try:
                            posYk = devices["camera"]["y"].send("/get pos")
                        except:
                            posYk = devices["camera"]["y"].device.send("/get pos")

                        try:
                            posZk = devices["camera"]["z"].send("/get pos")
                        except:
                            posZk = devices["camera"]["z"].device.send("/get pos")

                        print(f"Centre of ROI is: {self.rois[current_roi]}")
                        print(f"Pan/tilt head position is: {pan} {tilt} {head}")
                        print(
                            f"Position camera: {int(posXk.data)} {int(posYk.data)} {int(posZk.data)}"
                        )

                        self.gridcamera[current_roi]["x"] = int(posXk.data)
                        self.gridcamera[current_roi]["y"] = int(posYk.data)
                        self.gridcamera[current_roi]["z"] = int(posZk.data)

                        was_pressed = True

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    # print([len(n) < 2 for n in list(self.rois.values())])
                    if not any(
                        [len(n) < 2 for n in list(self.rois.values())]
                    ):  # and not any(list(checked.values())):
                        self.PanTilts = default_pan_tilt_values
                        try:
                            globals.weDone = True
                        except Exception as e:
                            errorloc(e)
                        break
                    else:
                        print("You are missing something...")
                        # print(self.rois, self.PanTilts, checked)
                        was_pressed = True

                elif keyboard.is_pressed("k"):
                    if not was_pressed:
                        pantilt_on = not pantilt_on
                        was_pressed = True

                elif keyboard.is_pressed("a"):
                    if not was_pressed:
                        globals.stimulus = 6
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("5"):
                    if not was_pressed:
                        default_amount = 10000
                        was_pressed = True

                elif keyboard.is_pressed("6"):
                    if not was_pressed:
                        default_amount = 1000
                        was_pressed = True

                elif keyboard.is_pressed("7"):
                    if not was_pressed:
                        default_amount = 50000
                        was_pressed = True

                elif keyboard.is_pressed("o"):
                    if not was_pressed:
                        globals.stimulus = 1
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif keyboard.is_pressed("c"):
                    if not was_pressed:
                        globals.stimulus = 0
                        tryexceptArduino(arduino, globals.stimulus)
                        was_pressed = True

                elif (
                    keyboard.is_pressed("up")
                    and not keyboard.is_pressed("i")
                    and not keyboard.is_pressed("l")
                ):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 3))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif (
                    keyboard.is_pressed("down")
                    and not keyboard.is_pressed("i")
                    and not keyboard.is_pressed("l")
                ):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 4))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["y"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )
                        except:
                            response = device["y"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "y", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "y",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("right"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 2))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("left"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 1))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["x"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )
                        except:
                            response = device["x"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "x", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "x",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("u"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 5))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                - revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("d"):
                    if pantilt_on:
                        ardpantilt.arduino.write(struct.pack(">B", 6))
                        time.sleep(keydelay)
                    else:
                        try:
                            response = device["z"].move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )
                        except:
                            response = device["z"].device.move_rel(
                                0
                                + revDirection(
                                    globals.current_device, "z", rules, default_amount
                                )
                            )

                        handleOutOfRange(
                            response,
                            device,
                            "z",
                            globals.current_device,
                            default_amount,
                            zaber_models_default,
                            zaber_models_end_default,
                        )

                elif keyboard.is_pressed("h"):
                    triggered_exception(
                        zabers=devices,
                        platform=platformcamera,
                        arduino_syringe=arduino,
                        arduino_pantilt=ardpantilt,
                    )

                elif keyboard.is_pressed("g"):
                    if not was_pressed:
                        print(f"Current spot: {current_roi}")
                        print("ROIS")
                        print(self.rois)
                        print("Pan tilt")
                        print(default_pan_tilt_values)
                        print("Camera positions")
                        print(self.gridcamera)
                        print("Checked Touch")
                        # print(checked)
                        was_pressed = True

                elif keyboard.is_pressed("n"):
                    if not was_pressed:
                        devices["colther"]["z"].device.move_abs(0)
                        try:
                            pre_touch = (
                                grid["tactile"][current_roi]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            )
                            movetostartZabersConcu(
                                devices, "tactile", ["z"], pos=pre_touch
                            )
                            moveAxisTo(devices, "tactile", "x", 533332)
                            moveAxisTo(devices, "tactile", "y", 1)
                        except:
                            print("HELLO")
                            pass

                        touched = False

                        current_roi = str(int(current_roi) + 1)
                        if int(current_roi) > len(grid[globals.current_device]):
                            current_roi = "1"

                        movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

                        funcs = [
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "camera",
                                    ["x", "y", "z"],
                                    grid["camera"][current_roi],
                                ],
                            ],
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "colther",
                                    list(reversed(haxes["colther"])),
                                    grid["colther"][current_roi],
                                ],
                            ],
                        ]
                        threadFunctions(funcs)

                        was_pressed = True

                elif keyboard.is_pressed("b"):
                    if not was_pressed:
                        devices["colther"]["z"].device.move_abs(0)
                        try:
                            pre_touch = (
                                grid["tactile"][current_roi]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            )
                            movetostartZabersConcu(
                                devices, "tactile", ["z"], pos=pre_touch
                            )
                            moveAxisTo(devices, "tactile", "x", 533332)
                            moveAxisTo(devices, "tactile", "y", 1)
                        except:
                            pass

                        touched = False

                        current_roi = str(int(current_roi) - 1)
                        if int(current_roi) == 0:
                            current_roi = list(grid["colther"].keys())[-1]

                        movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

                        funcs = [
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "camera",
                                    ["x", "y", "z"],
                                    grid["camera"][current_roi],
                                ],
                            ],
                            [
                                movetostartZabersConcu,
                                [
                                    devices,
                                    "colther",
                                    list(reversed(haxes["colther"])),
                                    grid["colther"][current_roi],
                                ],
                            ],
                        ]
                        threadFunctions(funcs)

                        was_pressed = True

                elif keyboard.is_pressed("z"):
                    if not was_pressed:
                        try:
                            posXf = devices["colther"]["x"].send("/get pos")

                        except:
                            posXf = devices["colther"]["x"].device.send("/get pos")

                        try:
                            posYf = devices["colther"]["y"].send("/get pos")
                        except:
                            posYf = devices["colther"]["y"].device.send("/get pos")

                        try:
                            posZf = devices["colther"]["z"].send("/get pos")
                        except:
                            posZf = devices["colther"]["z"].device.send("/get pos")

                        try:
                            posXk = devices["camera"]["x"].send("/get pos")

                        except:
                            posXk = devices["camera"]["x"].device.send("/get pos")

                        try:
                            posYk = devices["camera"]["y"].send("/get pos")
                        except:
                            posYk = devices["camera"]["y"].device.send("/get pos")

                        try:
                            posZk = devices["camera"]["z"].send("/get pos")
                        except:
                            posZk = devices["camera"]["z"].device.send("/get pos")

                        try:
                            posXt = devices["tactile"]["x"].send("/get pos")

                        except:
                            posXt = devices["tactile"]["x"].device.send("/get pos")

                        try:
                            posYt = devices["tactile"]["y"].send("/get pos")
                        except:
                            posYt = devices["tactile"]["y"].device.send("/get pos")

                        try:
                            posZt = devices["tactile"]["z"].send("/get pos")
                        except:
                            posZt = devices["tactile"]["z"].device.send("/get pos")

                        print("CAMERA")
                        print(posXk, posYk, posZk)

                        print("COLTHER")
                        print(posXf, posYf, posZf)

                        print("TACTILE")
                        print(posXt, posYt, posZt)

                        print("Pan/tilt position")
                        print(red)
                        was_pressed = True

                elif keyboard.is_pressed("t"):
                    if not was_pressed:
                        if not touched:
                            devices["colther"]["z"].device.move_abs(0)
                            pre_touch = (
                                grid["tactile"][current_roi]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            )
                            movetostartZabersConcu(
                                devices, "tactile", ["z"], pos=pre_touch
                            )
                            moveAxisTo(
                                devices,
                                "tactile",
                                "y",
                                grid["tactile"][current_roi]["y"],
                            )
                            moveAxisTo(
                                devices,
                                "tactile",
                                "x",
                                grid["tactile"][current_roi]["x"],
                            )
                            touching = grid["tactile"][current_roi]["z"] + round(
                                default_touch_z_offset
                                * globals.down_modifier_touch_height
                            )
                            moveAxisTo(devices, "tactile", "z", touching)
                            moveAxisTo(
                                devices,
                                "colther",
                                "z",
                                grid["colther"][current_roi]["z"],
                            )

                        elif touched:
                            devices["colther"]["z"].device.move_abs(0)
                            pre_touch = (
                                grid["tactile"][current_roi]["z"]
                                - default_touch_z_offset
                                * globals.up_modifier_touch_height
                            )
                            movetostartZabersConcu(
                                devices, "tactile", ["z"], pos=pre_touch
                            )
                            moveAxisTo(devices, "tactile", "x", 533332)
                            moveAxisTo(devices, "tactile", "y", 1)
                            moveAxisTo(
                                devices,
                                "colther",
                                "z",
                                grid["colther"][current_roi]["z"],
                            )

                        touched = not touched
                        was_pressed = True

                else:
                    was_pressed = False
                    continue

        finally:
            if arduino:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def manualCon3OneCon(self, devices, amount, arduino=None):

        try:
            device = devices[globals.current_device]

            while True:
                #### Y axis
                if keyboard.is_pressed("up"):
                    try:
                        device[2].move_rel(default_amount)
                    except:
                        device[2].device.move_rel(default_amount)

                elif keyboard.is_pressed("down"):
                    try:
                        device[2].move_rel(0 - default_amount)
                    except:
                        device[2].device.move_rel(0 - default_amount)

                #### X axis

                elif keyboard.is_pressed("left"):
                    try:
                        device[1].move_rel(0 - default_amount)
                    except:
                        device[1].device.move_rel(0 - default_amount)

                elif keyboard.is_pressed("right"):
                    try:
                        device[1].move_rel(default_amount)
                    except:
                        device[1].device.move_rel(default_amount)

                ### Z axis
                elif keyboard.is_pressed("d"):
                    try:
                        device[0].move_rel(default_amount)
                    except:
                        device[0].device.move_rel(default_amount)

                elif keyboard.is_pressed("o"):  # Open Arduino shutter
                    globals.stimulus = 1
                    arduino.arduino.write(struct.pack(">B", globals.stimulus))

                elif keyboard.is_pressed("c"):  # Close Arduino shutter
                    globals.stimulus = 0
                    arduino.arduino.write(struct.pack(">B", globals.stimulus))

                elif keyboard.is_pressed("u"):
                    try:
                        device[0].move_rel(0 - default_amount)
                    except:
                        device[0].device.move_rel(0 - default_amount)

                elif keyboard.is_pressed("p"):
                    globals.centreROI = [globals.indx0, globals.indy0]

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    # homingZabers(devices)
                    break

                #### GET POSITION

                elif keyboard.is_pressed("z"):
                    try:
                        posX = device[2].send("/get pos")

                    except:
                        posX = device[2].device.send("/get pos")

                    try:
                        posY = device[1].send("/get pos")
                    except:
                        posY = device[1].device.send("/get pos")

                    try:
                        posZ = device[0].send("/get pos")
                    except:
                        posZ = device[0].device.send("/get pos")

                    default_positions1[globals.current_device][0] = int(posX.data)
                    default_positions1[globals.current_device][1] = int(posY.data)
                    default_positions1[globals.current_device][2] = int(posZ.data)

                # Press letter h and Zaber will home, first z axis, then y and finally x
                # Control

                elif keyboard.is_pressed("h"):
                    homingZabers(devices)

                #### Double

                elif keyboard.is_pressed("k"):
                    device = devices["camera"]
                    globals.current_device = "camera"

                elif keyboard.is_pressed("f"):
                    device = devices["colther"]
                    globals.current_device = "colther"

                elif keyboard.is_pressed("t"):
                    device = devices["tactile"]
                    globals.current_device = "tactile"

                elif keyboard.is_pressed("n"):
                    device = devices["tactile"]
                    globals.current_device = "non_tactile"

                else:
                    continue

        finally:
            if arduino != None:
                stimulus = 0
                arduino.arduino.write(struct.pack(">B", stimulus))

    def manualConGUIthree(self, devices, arduino=None):

        """
        Controls:               # letter 'f' for colther
                                # letter 'h' for camera
                                # letter 't' for tactile
                                # letter 'n' for non-tactile

                                # letter 'c' to close shutter
                                # letter 'o' to open shutter

                                # letter 'p' to get centre ROI tactile
                                # letter 'i' to get centre ROI non-tactile

                                # letter 'h' to home all zabers
                                # press 'enter' to terminate
                                # press arrow 'up' to move x axis forward
                                # press arrow 'down' to move x axis backwards
                                # press arrow 'left' to move y axis forward
                                # press arrow 'right' to move y axis backwards
                                # letter 'd' to move Z axis down
                                # letter 'u' to move Z axis up
                                # letter 'z' to save CONTROL spot position
                                # letter 'x' to save EXPERIMENTAL spot position
        """

        if arduino != None:
            globals.stimulus = 0
            arduino.arduino.write(struct.pack(">B", globals.stimulus))
            # print('make sure shutter is closed')

        try:
            # Default zaber is camera
            device = devices[globals.current_device]

            while True:

                #### Y axis
                if keyboard.is_pressed("up"):
                    try:
                        device[1].move_rel(default_amount)
                    except:
                        device[1].device.move_rel(default_amount)
                    # print(curses.KEY_UP)

                elif keyboard.is_pressed("down"):
                    try:
                        device[1].move_rel(0 - default_amount)
                    except:
                        device[1].device.move_rel(0 - default_amount)

                #### X axis

                elif keyboard.is_pressed("left"):
                    try:
                        device[2].move_rel(0 - default_amount)
                    except:
                        device[2].device.move_rel(0 - default_amount)

                elif keyboard.is_pressed("right"):
                    try:
                        device[2].move_rel(default_amount)
                    except:
                        device[2].device.move_rel(default_amount)

                ### Z axis
                elif keyboard.is_pressed("d"):
                    try:
                        device[0].move_rel(default_amount)
                    except:
                        device[0].device.move_rel(default_amount)

                elif keyboard.is_pressed("u"):
                    try:
                        device[0].move_rel(0 - default_amount)
                    except:
                        device[0].device.move_rel(0 - default_amount)

                ### TERMINATE
                elif keyboard.is_pressed("e"):
                    homingZabers(devices)

                    break

                #### GET POSITION ZABER
                # Experimental
                elif keyboard.is_pressed("x"):
                    try:
                        posX = device[0].send("/get pos")

                    except:
                        posX = device[0].device.send("/get pos")

                    try:
                        posY = device[1].send("/get pos")
                    except:
                        posY = device[1].device.send("/get pos")

                    try:
                        posZ = device[2].send("/get pos")
                    except:
                        posZ = device[2].device.send("/get pos")

                    default_positions[globals.current_device]["experimental"][2] = int(
                        posX.data
                    )
                    default_positions[globals.current_device]["experimental"][1] = int(
                        posY.data
                    )
                    default_positions[globals.current_device]["experimental"][0] = int(
                        posZ.data
                    )

                    # print(default_positions)

                elif keyboard.is_pressed("z"):
                    try:
                        posX = device[0].send("/get pos")

                    except:
                        posX = device[0].device.send("/get pos")

                    try:
                        posY = device[1].send("/get pos")
                    except:
                        posY = device[1].device.send("/get pos")

                    try:
                        posZ = device[2].send("/get pos")
                    except:
                        posZ = device[2].device.send("/get pos")

                    default_positions[globals.current_device]["control"][2] = int(
                        posX.data
                    )
                    default_positions[globals.current_device]["control"][1] = int(
                        posY.data
                    )
                    default_positions[globals.current_device]["control"][0] = int(
                        posZ.data
                    )

                    print(posX.data)

                # Press letter h and Zaber will home, first z axis, then y and finally x
                # Control

                elif keyboard.is_pressed("h"):
                    homingZabers(devices)

                elif keyboard.is_pressed("o"):  # Open Arduino shutter
                    globals.stimulus = 1
                    arduino.arduino.write(struct.pack(">B", globals.stimulus))
                    # time.sleep(2)

                elif keyboard.is_pressed("c"):  # Close Arduino shutter
                    globals.stimulus = 0
                    arduino.arduino.write(struct.pack(">B", globals.stimulus))
                    # time.sleep(2)

                elif keyboard.is_pressed("p"):
                    # print([globals.indx0, globals.indy0])
                    globals.centreROI["control"] = [globals.indx0, globals.indy0]

                elif keyboard.is_pressed("i"):
                    globals.centreROI["experimental"] = [globals.indx0, globals.indy0]

                elif keyboard.is_pressed("t"):
                    device = devices["tactile"]
                    globals.current_device = "tactile"

                elif keyboard.is_pressed("n"):
                    device = devices["tactile"]
                    globals.current_device = "non_tactile"

                elif keyboard.is_pressed("k"):
                    device = devices["camera"]
                    globals.current_device = "camera"

                elif keyboard.is_pressed("f"):
                    device = devices["colther"]
                    globals.current_device = "colther"

                else:
                    continue

        finally:
            if arduino != None:
                globals.shutter_state = "close"
                arduino.arduino.write(globals.shutter_state.encode())

    def ROIPID(
        self,
        device,
        set_point,
        event1,
        arduino=None,
        radio=20.0,
        Kp=-1500,
        Ki=-100,
        Kd=-800,
        output_limits=(-3000, 3000),
    ):

        """
        Method function to perform PID on a pre-selected ROI.
        It synchronises with the camera, so it needs an event.
        Globals: pid_out, stimulus, temp, pos_zaber
        """

        # we initialise PID object
        PID = PYD(Kp=Kp, Ki=Ki, Kd=Kd, setpoint=set_point, output_limits=output_limits)
        print("PID initialised")

        pos = device["z"].device.send("/get pos")
        globals.pos_zaber = int(pos.data)

        if arduino != None:
            globals.stimulus = 1
            arduino.arduino.write(struct.pack(">B", globals.stimulus))
            # print('Shutter '+ str(globals.stimulus))

        try:
            while True:
                if globals.stimulus == 1:
                    event1.wait()
                    # print(globals.stimulus)
                    # print('In while loop, stimulus')
                    print(globals.temp)

                    while globals.temp > (set_point + 0.4):
                        # print('waiting to start close-loop')
                        # print(type(set_point))
                        time.sleep(0.0001)

                    PID.run(globals.temp)
                    globals.pid_out = PID.output

                    device["z"].device.move_rel(int(globals.pid_out))
                    pos = device["z"].device.send("/get pos")
                    globals.pos_zaber = int(pos.data)
                    previous_temp = globals.temp

                elif globals.stimulus == 0:
                    print("Close shutter")
                    arduino.arduino.write(struct.pack(">B", globals.stimulus))
                    break

                event1.clear()
                # print('event cleared')

        except Exception as e:
            errorloc(e)

        except KeyboardInterrupt:
            sys.exit(0)

        finally:
            print("Stop PID")
            pass

    def ROIPIDSyringe(self, device, set_point, event1, radio, arduino=None):

        ## PID parameters

        thermal_range = np.round(np.arange(24.00, 33.01, 0.01), 2)

        Kp_down = -800
        Kp_up = -1500
        Kp_range = np.round(
            np.arange(Kp_down, Kp_up, -abs(Kp_down - Kp_up) / len(thermal_range)), 2
        )

        Ki_down = -100
        Ki_up = -500
        Ki_range = np.round(
            np.arange(Ki_down, Ki_up, -abs(Ki_down - Ki_up) / len(thermal_range)), 2
        )

        Kd_down = -100
        Kd_up = -500
        Kd_range = np.round(
            np.arange(Kd_down, Kd_up, -abs(Kp_down - Ki_up) / len(thermal_range)), 2
        )

        output_limits = (-3000, 3000)

        # we initialise PID object
        PID = PYD(
            Kp_range,
            Ki_range,
            Kd_range,
            set_point,
            gain_scheduling_range=thermal_range,
            output_limits=output_limits,
        )
        counter = 0
        try:
            while True:
                if globals.stimulus == 1:
                    counter += 1

                    event1.wait()

                    if counter == 1:

                        while globals.temp > (set_point + 0.4):
                            # print('waiting to start close-loop')
                            # print(type(set_point))
                            time.sleep(0.0001)

                    # Calculate controller variable
                    PID.runGainSchedule(globals.temp)

                    print(globals.temp)
                    print(PID.output)

                    # Move zaber
                    device[0].device.move_rel(int(PID.output))
                    pos = device[0].device.send("/get pos")
                    pos = int(pos.data)
                    previous_temp = globals.temp

                    # Send global variables to save
                    globals.pos_zaber = pos
                    globals.Kp = PID.current_Kp
                    globals.Ki = PID.current_Ki
                    globals.Kd = PID.current_Kd

                    globals.proportional = PID.proportional
                    globals.integral = PID.integral
                    globals.derivative = PID.derivative

                elif globals.stimulus == 0:

                    continue

                previous_temp = globals.temp
                event1.clear()

        except KeyboardInterrupt:
            sys.exit(0)

    def DistROI(self, device, set_point, event, file, folder, name_dev="colther"):

        dataTS = {
            "Koutput": [],
            "data": [],
            "Kp": [],
            "Ki": [],
            "error": [],
            "positionX": [],
            "positionY": [],
            "positionZ": [],
            "set_point": [],
            "time": [],
        }
        ## PID parameters
        Kp = -400
        Ki = -100
        output_limits = (-500, 500)

        # we initialise PID object
        PID = PYD(Kp, set_point, Ki=Ki, output_limits=output_limits)

        while True:

            event.wait()

            PID.run(globals.data)
            # print(globals.data)
            # print(PID.error)
            # print('PID data: ' + str(int(PID.output)))

            now = time.time()
            loop_data = [
                PID.output,
                globals.data,
                PID.proportional,
                PID.integral,
                PID.error,
                default_positions["colther"][0],
                default_positions["colther"][1],
                default_positions["colther"][2],
                globals.dist,
                now,
            ]
            # print(default_positions['colther'])

            device[name_dev][0].device.move_rel(int(PID.output))
            pos = device[name_dev][0].device.send("/get pos")
            pos = int(pos.data)

            globals.pos_zaber = pos

            event.clear()

            for k, l in zip(dataTS, loop_data):
                dataTS[k].append(l)

            if keyboard.is_pressed("e"):
                saveIndv(file, folder, dataTS)
                break

    def manualCon(self, devices, amount, arduino=None):
        """
        Very early method to control three axes of one zaber while displying instructions and
        other info on screen. It uses the curses library
        """

        if arduino != None:
            stimulus = 0
            arduino.arduino.write(struct.pack(">B", stimulus))

        # self.spotsPosX = {'C1': [], 'C2': [], 'NonC': []}
        # self.spotsPosY = {'C1': [], 'C2': [], 'NonC': []}

        def my_raw_input(stdscr, r, c, prompt_string):
            curses.echo()
            stdscr.addstr(r, c, prompt_string)
            stdscr.refresh()
            input = stdscr.getstr(r + 1, c, 20)
            return input

        try:

            stdscr = curses.initscr()
            stdscr.keypad(1)

            stdscr.addstr(
                0,
                0,
                '\n Move COLTHER. \n Device 1 (x): left and right arrows \n Device 2 (y): up and down arrows \n Device 3 (z): "u" (up) and "d" (down) \n Press "o" to open the shutter \n Press "c" to close the shutter \n Press "a" to choose how many steps to move \n Press "e" to terminate \n Press "s" to get Zaber coordiantes \n Press "p" tp get ROI centre"s coordinates',
            )
            stdscr.refresh()

            key = ""
            while True:

                try:
                    stdscr.move(23, 0)
                    stdscr.clrtoeol()

                except Exception as e:
                    stdscr.refresh()
                    curses.endwin()
                    # print(e)

                stdscr.addstr(19, 0, "Minimum temperature: {}".format(globals.temp))

                stdscr.move(19, 59)
                stdscr.clrtoeol()

                key = stdscr.getch()
                stdscr.refresh()

                if key == curses.KEY_UP:
                    devices[1].device.move_rel(amount)
                    # print(curses.KEY_UP)
                elif key == curses.KEY_DOWN:
                    devices[1].device.move_rel(0 - amount)

                elif key == ord("e"):  ### TERMINATE
                    for i in reversed(devices):
                        i.device.home()
                    break

                elif key == ord("a"):  ### ZABER STEPS
                    while True:
                        amount = my_raw_input(
                            stdscr, 10, 50, "\n How much would you like to move?"
                        ).decode("utf-8")
                        try:
                            amount = int(amount)
                            stdscr.move(10 + 1, 0)
                            # stdscr.refresh()
                            stdscr.clrtoeol()
                            break
                        except:
                            stdscr.addstr(14, 0, "Only integers are valid numbers")

                elif key == curses.KEY_LEFT:
                    devices[0].device.move_rel(0 - amount)
                elif key == curses.KEY_RIGHT:
                    devices[0].device.move_rel(amount)

                elif key == curses.KEY_LEFT:
                    devices[0].device.move_rel(0 - amount)
                elif key == curses.KEY_RIGHT:
                    devices[0].device.move_rel(amount)

                elif key == ord("d"):
                    devices[2].device.move_rel(amount)
                    # print('d')
                elif key == ord("u"):
                    devices[2].device.move_rel(0 - amount)

                elif key == ord("s"):  #### GET POSITION ZABER

                    posX = devices[0].device.send("/get pos")
                    globals.posX = int(posX.data)

                    posY = devices[1].device.send("/get pos")
                    globals.posY = int(posY.data)

                    posZ = devices[2].device.send("/get pos")
                    globals.posZ = int(posZ.data)

                    stdscr.addstr(
                        15,
                        0,
                        "X: {} // Y: {} // Z: {}".format(
                            globals.posX, globals.posY, globals.posZ
                        ),
                    )

                elif key == ord(
                    "h"
                ):  # Press letter h and Zaber will home, first z axis, then y and finally x
                    for i in reversed(devices):
                        i.device.home()

                elif key == ord("o"):  # Open Arduino shutter
                    globals.stimulus = 1
                    arduino.arduino.write(struct.pack(">B", globals.stimulus))

                elif key == ord("c"):  # Close Arduino shutter
                    globals.stimulus = 0
                    arduino.arduino.write(struct.pack(">B", globals.stimulus))

                elif key == ord("p"):
                    globals.indx_saved = globals.indx0
                    globals.indy_saved = globals.indy0

                else:
                    continue

        finally:

            if arduino != None:
                globals.stimulus = 0
                arduino.arduino.write(struct.pack(">B", globals.stimulus))

            stdscr.refresh()
            curses.endwin()

    def controlZaxis(self, amount=default_amount, rules=default_rules):
        """
        Function to....
        """

        was_pressed = False
        while True:

            if keyboard.is_pressed("q"):
                print(f"\nDone moving the Zaber\n")
                break

            elif keyboard.is_pressed("a"):
                while True:
                    print(f"\nEach movement is currently {amount} steps")
                    amount = input(
                        "How long should each movement be? (units: Zaber steps)   "
                    )
                    match = re.match(r"([a-z]+)([0-9]+)", amount, re.I)

                    if match:
                        amount = match.groups()[-1]

                    try:
                        amount = int(amount)
                        print(
                            f"\nEach movement is now {amount} steps, ready to continue...\n"
                        )
                        break
                    except:
                        print("Wrong input, try again")

            if keyboard.is_pressed("u"):
                try:
                    self.move_rel(
                        0 - revDirection(globals.current_device, "z", rules, amount)
                    )
                except:
                    self.device.move_rel(
                        0 - revDirection(globals.current_device, "z", rules, amount)
                    )

            elif keyboard.is_pressed("d"):
                try:
                    self.move_rel(
                        0 + revDirection(globals.current_device, "z", rules, amount)
                    )
                except:
                    self.device.move_rel(
                        0 + revDirection(globals.current_device, "z", rules, amount)
                    )

            elif keyboard.is_pressed("z"):
                if not was_pressed:
                    try:
                        posZ = self.send("/get pos")
                    except:
                        posZ = self.device.send("/get pos")

                    default_positions[globals.current_device]["z"] = int(posZ.data)

                    print(default_positions)
                    was_pressed = True

            else:
                was_pressed = False

    ######################## Developing phase
    def maintainColdMinPeak(
        self, amount, devices, set_point, range, event1, arduino=None
    ):

        devices[0].device.move_abs(globals.posX)
        devices[1].device.move_abs(globals.posY)
        devices[2].device.move_abs(globals.posZ)

        previous_temp = globals.temp

        # We define the low and upper bounds
        lowR = set_point - range / 2
        highR = set_point + range / 2

        # time.sleep(2)

        if arduino != None:
            shutter = "open"
            arduino.arduino.write(shutter.encode())
            time.sleep(1.2)
            globals.shutter_state = "open"
            print(globals.shutter_state)

        counter = 0

        try:

            while True:

                if globals.shutter_state == "open":
                    counter += 1

                    # print('we are here')
                    event1.wait()
                    # print('Minimum temperature: ' + str(globals.temp))

                    if counter == 1:
                        while globals.temp > (set_point + 0.4):
                            # print('waiting to start close-loop')
                            # print(type(set_point))
                            time.sleep(0.0001)

                    if keyboard.is_pressed("c"):
                        shutter = "close"
                        arduino.arduino.write(shutter.encode())

                        globals.shutter_state = "close"
                        devices[2].device.move_abs(0)
                        devices[1].device.move_abs(0)
                        devices[0].device.move_abs(0)

                    if globals.temp < lowR:  # BELOW lower bound
                        diff = abs(set_point - globals.temp)
                        a = amount * 10 * diff
                        b = amount * 4 * diff

                    if globals.temp > highR:  # ABOVE upper bound
                        diff = abs(set_point - globals.temp)
                        a = amount * 10 * diff
                        b = amount * 4 * diff

                    if globals.temp > (set_point - 1.5) and globals.temp < (
                        set_point + 1.5
                    ):
                        # print('here')
                        diff = abs(set_point - globals.temp)
                        a = amount * 4 * diff
                        b = amount * 10 * diff

                    print(diff)
                    zaber_pos = a * (set_point - globals.temp) + b * (
                        previous_temp - globals.temp
                    )

                    # print(zaber_pos)

                    devices[2].device.move_rel(-int(zaber_pos))
                    pos = devices[2].device.send("/get pos")
                    pos = int(pos.data)
                    previous_temp = globals.temp
                    globals.posZ = pos

                elif globals.shutter_state == "close":
                    # print('we are here actually')
                    # time.sleep(0.01)
                    continue

                previous_temp = globals.temp
                event1.clear()

        except KeyboardInterrupt:
            sys.exit(0)

    def maintainColdMeanROIPID(self, devices, set_point, event1, radio, arduino=None):

        devices[0].device.move_abs(globals.posX)
        devices[1].device.move_abs(globals.posY)
        devices[2].device.move_abs(globals.posZ)

        previous_temp = globals.temp

        # We define the low and upper bounds
        # lowR = set_point - range/2
        # highR = set_point + range/2
        # print(lowR, highR)

        if arduino != None:
            shutter = "open"
            arduino.arduino.write(shutter.encode())
            time.sleep(1.2)
            globals.shutter_state = "open"
            print(globals.shutter_state)

        counter = 0

        try:

            while True:

                if globals.shutter_state == "open":
                    counter += 1

                    # print('we are here')
                    event1.wait()
                    # print('Minimum temperature: ' + str(globals.temp))

                    if counter == 1:

                        while globals.temp > (set_point + 0.4):
                            # print('waiting to start close-loop')
                            # print(type(set_point))
                            time.sleep(0.0001)

                            ## PID parameters
                        Kp = -1500
                        Ki = -100
                        Kd = -800
                        output_limits = (-3000, 3000)
                        range = 0.3

                        # we initialise PID object
                        PID = PYD(Kp, Ki, Kd, set_point)

                    if keyboard.is_pressed("c"):
                        shutter = "close"
                        arduino.arduino.write(shutter.encode())

                        globals.shutter_state = "close"
                        devices[2].device.move_abs(0)
                        devices[1].device.move_abs(0)
                        devices[0].device.move_abs(0)

                    zaber_pos = PID(globals.temp)

                    # print(zaber_pos)

                    devices[2].device.move_rel(int(zaber_pos))
                    pos = devices[2].device.send("/get pos")
                    pos = int(pos.data)
                    previous_temp = globals.temp
                    globals.posZ = pos

                elif globals.shutter_state == "close":
                    # print('we are here actually')
                    # time.sleep(0.01)
                    continue

                previous_temp = globals.temp
                event1.clear()

        except KeyboardInterrupt:
            sys.exit(0)

    def OscColdMeanROIPID(
        self, devices, set_point, event1, radio, amplitude, frequency, arduino=None
    ):

        devices[0].device.move_abs(globals.posX)
        devices[1].device.move_abs(globals.posY)
        devices[2].device.move_abs(globals.posZ)

        previous_temp = globals.temp

        if arduino != None:
            shutter = "open"
            arduino.arduino.write(shutter.encode())
            time.sleep(1.2)
            globals.shutter_state = "open"
            print(globals.shutter_state)

        counter = 0

        wave = sineWave(set_point, amplitude, frequency)

        try:
            while True:
                if globals.shutter_state == "open":

                    # print('we are here')
                    event1.wait()
                    # print('Minimum temperature: ' + str(globals.temp))

                    if counter == 0:

                        while globals.temp > (set_point + 0.4):
                            # print('waiting to start close-loop')
                            # print(type(set_point))
                            time.sleep(0.0001)

                            ## PID parameters
                        Kp = -1500
                        Ki = -100
                        Kd = -800
                        output_limits = (-3000, 3000)
                        range = 0.3

                        # we initialise PID object
                        PID = PYD(Kp, Ki, Kd, set_point)

                    if keyboard.is_pressed("c"):
                        shutter = "close"
                        arduino.arduino.write(shutter.encode())

                        globals.shutter_state = "close"
                        devices[2].device.move_abs(0)
                        devices[1].device.move_abs(0)
                        devices[0].device.move_abs(0)

                    zaber_pos = PID(globals.temp, osc=wave[counter])
                    print(wave[counter])
                    counter += 1

                    # print(zaber_pos)

                    devices[2].device.move_rel(int(zaber_pos))
                    pos = devices[2].device.send("/get pos")
                    pos = int(pos.data)
                    previous_temp = globals.temp
                    globals.posZ = pos

                elif globals.shutter_state == "close":

                    continue

                previous_temp = globals.temp
                event1.clear()

        except KeyboardInterrupt:
            sys.exit(0)

    def testHeight(self, devices, steps):
        globals.pos = 0

        while globals.pos < 230000:

            time.sleep(0.01)
            devices[0].move(steps)
            pos = devices[0].device.send("/get pos")
            pos = int(pos.data)
            # print(pos)
            globals.pos = pos
            # print(globals.pos)

    def goStartingPosition(self, x_Spos, y_Spos, devices):
        devices[0].device.move_abs(x_Spos)
        devices[1].device.move_abs(y_Spos)

    def __repr__(self):

        return "Device {} at port {}".format(self.device, self.port)


################################################################################################################
################################################################################################################
############################ FUNCTIONS
################################################################################################################
################################################################################################################


def gridCalculation(
    zaber,
    grid_separation,
    step_size=default_step_sizes,
    pos=default_positions,
    rule=default_rules,
    dim=[3, 3],
):
    """
    Function to estimate a grid from a point. The initial point becomes the centre cell.
    grid_separation in millimetres
    """
    if len(dim) < 2:
        raise Exception("dim should be of the form [x, y]")

    # print(pos)

    # step_size = step_size[zaber]

    one_cm_zaber_steps = grid_separation / (step_size[zaber] / 1000)

    grid = {}

    # Calculate origin
    x_origin = pos[zaber]["x"] - revDirection(zaber, "x", rule, one_cm_zaber_steps)
    y_origin = pos[zaber]["y"] - revDirection(zaber, "y", rule, one_cm_zaber_steps)

    if x_origin < 0 or y_origin < 0:
        x_origin = int(max(0, x_origin))
        y_origin = int(max(0, y_origin))
        print(
            f"Either X or Y were found to be negative values.\n They were set to 0, but the grid won't apply properly"
        )

    # print(x_origin)
    # print(y_origin)
    cell = 1
    for i in np.arange(dim[1]):
        for j in np.arange(dim[0]):
            # print(pos[zaber]['z'])
            grid[str(cell)] = {
                "x": math.ceil(
                    x_origin + revDirection(zaber, "x", rule, one_cm_zaber_steps * j)
                ),
                "y": math.ceil(
                    y_origin + revDirection(zaber, "y", rule, one_cm_zaber_steps * i)
                ),
                "z": pos[zaber]["z"],
            }
            # print(j, i)
            cell += 1

    print(f"\nGrid calculated for {zaber}\n")

    return grid


def threeDD(point1, point2):
    sq_dist = (
        (point2[0] - point1[0]) ** 2
        + (point2[1] - point1[1]) ** 2
        + (point2[2] - point2[2]) ** 2
    )
    distance = np.sqrt(sq_dist)

    return distance


def angle2lines(point1, point2, point3):
    # print(point1)
    # print(point2)
    # print(point3)
    ba = point2 - point1
    bc = point3 - point1

    print(ba)
    print(bc)

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)


def angle2lines2D(point1, point2, point3):
    # print(point1)
    # print(point2)
    # print(point3)
    ba = point2[0:2] - point1[0:2]
    bc = point3[0:2] - point1[0:2]

    print(ba)
    print(bc)

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine_angle)
    return np.degrees(angle)


def vectorEnd(start, magnitude, angle):
    """
    Function to calculate the end point of a vector for a given starting point (start), length (magnitude) and angle (angle)
    """
    angle = angle * math.pi / 180
    length = magnitude
    return [
        math.ceil(length * math.cos(angle) + start[0]),
        math.ceil(length * math.sin(angle) + start[1]),
    ]


def addVectorPointGrid(zaber, pos, magnitude, angle, grid=default_grid):
    """
    Function to inject an end point of a vector starting from one grid point into the grid dictionary of a given Zaber
    """
    v_end = vectorEnd([grid[zaber][pos]["x"], grid[zaber][pos]["y"]], magnitude, angle)
    new_pos = max([int(x) for x in list(default_grid[zaber].keys())])

    grid[zaber][f"{new_pos + 1}"] = {"x": v_end[0], "y": v_end[1], "z": 0}

    return grid


def manualorder(haxes):
    """
    Function to manually choose the order for homing and moving multiple Zabers
    """
    os.system("clear")
    print(f"\nThere are {len(haxes.keys())} set of zabers, their names are: ")
    list_keys = list(haxes.keys())

    pos_zabs = tuple(str(i) for i in range(0, len(list_keys)))
    # print(pos_zabs)

    nhaxes = {}
    temp_zabers = []

    for i in np.arange((len(list_keys))):
        temp_axes = []

        set_diff_za = set(list_keys) - set(temp_zabers)
        diff_za = list(set_diff_za)

        if i == 0:
            while True:
                for k in diff_za:
                    print(k + f" ({[i for i, s in enumerate(list_keys) if k in s][0]})")
                chosen = input(f"\nWhich Zaber set should we move first?\n")
                if len(chosen) >= 2:
                    chosen = chosen[-1]
                    print(f"\nCache removed\n")

                try:
                    if chosen in temp_zabers:
                        print(f"\n{chosen.upper()} has been selected already\n")

                    elif chosen in pos_zabs:
                        print(f"\n{list_keys[int(chosen)].upper()} was selected\n")
                        break
                    else:
                        print(f"\nOnly {pos_zabs} are valid answers \n")
                        continue
                except:
                    printme("Wrong input")
        else:
            if len(list(set_diff_za)) > 1:
                while True:
                    for k in diff_za:
                        print(
                            k
                            + f" ({[i for i, s in enumerate(list_keys) if k in s][0]})"
                        )
                    chosen = input(f"\nWhich Zaber set should we move next?   ")

                    try:
                        if list_keys[int(chosen)] in temp_zabers:
                            print(
                                f"\n{list_keys[int(chosen)].upper()} has been selected already \n"
                            )

                        elif chosen in pos_zabs:
                            print(f"\n{list_keys[int(chosen)].upper()} was selected\n")
                            break
                        else:
                            print(f"\nOnly {pos_zabs} are valid answers\n")
                            continue

                    except:
                        print("Wrong input")
            else:

                chosen = list_keys.index(diff_za[0])
                print(f"\n{list_keys[int(chosen)].upper()} was selected\n")
                temp_zabers.append(chosen)

        temp_zabers.append(list_keys[int(chosen)])

        # Select 1st the axes
        while True:
            firstaxis = input(
                "Which axis should move first? \n You probably want to choose then one that is above the rest, so they don't crash each other\n"
            )
            if firstaxis in ("x", "y", "z"):
                if firstaxis == "x" and list_keys[int(chosen)] == "colther":
                    print(
                        "It is probably not a good idea to move the x axis of colther first\n "
                    )
                    continue
                else:
                    break
            else:
                print(f"Only 'x', 'y' & 'z' are valid answers\n ")
                continue

        temp_axes.append(firstaxis)
        # Select 2nd the axes
        while True:
            secondaxis = input("Which axis should move next?    ")

            if firstaxis == secondaxis:
                print(f"{secondaxis} has already been selected \n")
                continue

            elif secondaxis in ("x", "y", "z"):
                break

            else:
                print(f"Only 'x', 'y' & 'z' are valid answers \n")
                continue

        temp_axes.append(secondaxis)

        set_diff = set(haxes[list_keys[int(chosen)]]) - set(temp_axes)
        diff = list(set_diff)
        temp_axes.append(diff[0])

        # put into haxes dictionary
        nhaxes[list_keys[int(chosen)]] = temp_axes

    return nhaxes


def revDirection(zaber, axis, rule, number):
    """
    Function to get the negative value of a number depending on zaber rules
    """
    if not rule[zaber][axis]:
        number = -number

    return number


def homingZabers(zabers, axes=None, speed=153600 * 4):
    """
    This function is to home all zabers in a Zaber object
    """
    if axes == None:
        axes = {}
        for kzabers, vzabers in zabers.items():
            axes[kzabers] = ["z", "y", "x"]
        print("\n Homing to default axes order [z, y, x] \n")

    speed = str(speed)
    # print(axes)
    for kaxes, vaxes in axes.items():
        for d in vaxes:
            print(f"\n Homing {d} axis of {kaxes}\n")
            try:
                zabers[kaxes][d].device.send("/set maxspeed {}".format(speed))
                if zabers[kaxes][d].home:
                    zabers[kaxes][d].device.move_abs(0)
                else:
                    zabers[kaxes][d].device.home()
                    zabers[kaxes][d].home = True
            except:
                zabers[kaxes][d].send("/set maxspeed {}".format(speed))
                if zabers[kaxes][d].home:
                    zabers[kaxes][d].move_abs(0)
                else:
                    zabers[kaxes][d].home()
                    zabers[kaxes][d].home = True


def movetostartZabers(
    zabers, zaber, axes, pos=default_positions, event=None, speed=153600 * 4
):
    """
    This function is to move one set of Zabers to a defined positions (pos)
    """
    if event:
        print(event._flag)
        event.wait()

    for d in axes:
        if isinstance(pos, dict):
            posc = pos[d]
        else:
            posc = pos

        if posc < 0:
            posc = 0
        print(f"\n Moving axis {d} of {zaber} to {posc}")

        try:
            zabers[zaber][d].device.send("/set maxspeed {}".format(speed))
            zabers[zaber][d].device.move_abs(math.ceil(posc))
        except:
            zabers[zaber][d].send("/set maxspeed {}".format(speed))
            zabers[zaber][d].move_abs(math.ceil(posc))
        time.sleep(0.1)


def moveAxisTo(zabers, zaber, axis, amount, speed=153600 * 4):
    try:
        zabers[zaber][axis].device.send("/set maxspeed {}".format(speed))
        zabers[zaber][axis].device.move_abs(amount)
    except:
        zabers[zaber][axis].send("/set maxspeed {}".format(speed))
        zabers[zaber][axis].move_abs(amount)


def movetostartZabersConcu(
    zabers, zaber, axes, pos=default_positions, speed=153600 * 4
):
    """
    This function is to move one set of Zabers to a defined positions (pos)
    """

    def startOneAxis(zaber, d):
        if isinstance(pos, dict):
            posc = pos[d]
        else:
            posc = pos
        if posc < 0:
            posc = 0

        print(f"\n Moving axis {d} of {zaber} to {posc}\n")

        try:
            zabers[zaber][d].device.send("/set maxspeed {}".format(speed))
            zabers[zaber][d].device.move_abs(math.ceil(posc))
        except:
            zabers[zaber][d].send("/set maxspeed {}".format(speed))
            zabers[zaber][d].move_abs(math.ceil(posc))

    threads_zabers = []

    for d in axes:
        sz = threading.Thread(target=startOneAxis, args=[zaber, d])
        threads_zabers.append(sz)

    for x in threads_zabers:
        x.start()

    for x in threads_zabers:
        x.join()


def moveZabersUp(devices, zabers_to_move, uppos=0):
    """
    Move Zabers up (z axis) concurrently
    """

    def moveUp(devices, zaber_to_move):
        try:
            devices[zaber_to_move]["z"].device.move_abs(uppos)
        except:
            devices[zaber_to_move]["z"].move_abs(uppos)

    threads_zabers = []

    for d in zabers_to_move:
        uz = threading.Thread(target=moveUp, args=[devices, d])
        threads_zabers.append(uz)

    for x in threads_zabers:
        x.start()

    for x in threads_zabers:
        x.join()


def homingZabersConcu(zabers, axes=None, speed=153600 * 4):
    """
    This function is to home all zabers in a Zaber object concurrently
    """

    def homeOneAxis(kaxes, d):
        print(f"\n Homing {d} axis of {kaxes}\n")
        try:
            zabers[kaxes][d].device.send("/set maxspeed {}".format(speed))
            if zabers[kaxes][d].home:
                zabers[kaxes][d].device.move_abs(0)
            else:
                zabers[kaxes][d].device.home()
                zabers[kaxes][d].home = True
        except:
            zabers[kaxes][d].send("/set maxspeed {}".format(speed))
            if zabers[kaxes][d].home:
                zabers[kaxes][d].move_abs(0)
            else:
                zabers[kaxes][d].home()
                zabers[kaxes][d].home = True

    if axes == None:
        axes = {}
        for kzabers, vzabers in zabers.items():
            axes[kzabers] = ["z", "y", "x"]
        print("\n Homing to default axes order [z, y, x] \n")

    speed = str(speed)
    # print(axes)
    for kaxes, vaxes in axes.items():
        threads_zabers = []
        for d in vaxes:
            hz = threading.Thread(target=homeOneAxis, args=[kaxes, d])
            threads_zabers.append(hz)

        for x in threads_zabers:
            x.start()

        for x in threads_zabers:
            x.join()


def cm_to_steps(z_d, step_size):
    """
    Function to translate centimetres into Zaber steps
    """
    z_d_microm = z_d * 10000
    z_steps = z_d_microm / step_size
    return int(round(z_steps))


def z_axis_pos(z_d, step_size):
    """
    Function to translate centimetres into Zaber steps
    """
    return cm_to_steps(z_d, step_size)


def steps_to_cm(steps, step_size):
    """
    Function to translate Zaber steps into centimetres
    """
    microms = steps * step_size
    d_cm = microms / 10000
    return round(d_cm, 2)


def sineWave(set_point, amplitude, freq, phase=0, repeats=1):

    t = np.arange(0, repeats * 10, 0.01)
    w = 2 * math.pi * freq
    phi = phase  # phase to change the phase of sine function

    A = ((set_point + amplitude / 2) - (set_point - amplitude / 2)) / 2
    wave = (
        A * np.sin(w * t + phi)
        + ((set_point + amplitude / 2) + (set_point - amplitude / 2)) / 2
    )

    # self.volt = np.tile(self.volt, repeats)
    # duration = int(1000 * repeats/globals.rate_NI) # duration of sound
    return wave


def zrabber(n_trail, port, low_temp):

    while True:
        device = zaberClass(n_trail, port)

        if globals.temp < low_temp:

            device.move(5000)  # negative is up

        # elif globals.temp > high_temp:
        #
        #     device.move(-5000) #positive is down
        else:
            device.move(-5000)
            continue


def read_reply(command):
    return [
        "Message type:  " + command.message_type,
        "Device address:  " + str(command.device_address),
        "Axis number:  " + str(command.axis_number),
        "Message ID:  " + str(command.message_id),
        "Reply flag:  " + str(command.reply_flag),
        "Device status:  " + str(command.device_status),
        "Warning flag:  " + str(command.warning_flag),
        "Data: " + str(command.data),
        "Checksum:  " + str(command.checksum),
    ]


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def lutsyringe(temp):
    near_zaber = find_nearest(y_vals_inter, temp)
    where_near_zaber = np.where(y_vals_inter == near_zaber)
    return zebers_inter[where_near_zaber[0][0]]


def setUpBigThree(axes):

    ### Zabers
    colther1 = Zaber(1, who="serial")
    colther2 = Zaber(2, port=colther1, who="serial")
    colther3 = Zaber(3, port=colther1, who="serial")

    camera12 = Zaber(
        1,
        who="modem",
        usb_port=globals.usb_port_camera,
        n_modem=globals.modem_port_camera,
    )
    camera1 = camera12.device.axis(1)
    camera2 = camera12.device.axis(2)
    camera3 = Zaber(
        2,
        port=camera12,
        who="modem",
        usb_port=globals.usb_port_camera,
        n_modem=globals.modem_port_camera,
    )

    tactile12 = Zaber(
        1,
        who="modem",
        usb_port=globals.usb_port_tactile,
        n_modem=globals.modem_port_tactile,
        head=75,
        tail2=3,
        tail1=1,
    )
    tactile1 = tactile12.device.axis(1)
    tactile2 = tactile12.device.axis(2)
    tactile3 = Zaber(
        2,
        port=tactile12,
        who="modem",
        usb_port=globals.usb_port_tactile,
        n_modem=globals.modem_port_tactile,
        head=75,
        tail2=3,
        tail1=1,
    )

    colther = {
        axes["colther"][0]: colther1,
        axes["colther"][1]: colther2,
        axes["colther"][2]: colther3,
    }
    camera = {
        axes["camera"][0]: camera1,
        axes["camera"][1]: camera2,
        axes["colther"][2]: camera3,
    }
    tactile = {
        axes["tactile"][0]: tactile1,
        axes["tactile"][1]: tactile2,
        axes["tactile"][2]: tactile3,
    }

    zabers = {"colther": colther, "camera": camera, "tactile": tactile}

    return zabers


def set_up_one_zaber(
    name_dev, axes, who="serial", usb_port=None, n_modem=None, winPort=None
):
    """
    name_dev: string name for your zaber, without spaces
    axes: name and order of axes
    This function is for setting up ONE zaber set-up with 3 linear stage actuators
    """
    ### Zabers
    try:
        if who == "serial":
            zaber1 = Zaber(1, who, usb_port, n_modem, winPort=winPort)
            zaber2 = Zaber(2, port=zaber1, who=who, winPort=winPort)
            zaber3 = Zaber(3, port=zaber1, who=who, winPort=winPort)

        elif who == "modem":
            zaber12 = Zaber(1, who, usb_port, n_modem)

            zaber1 = zaber12.device.axis(1)
            zaber2 = zaber12.device.axis(2)
            zaber3 = Zaber(2, port=zaber12, who=who, usb_port=usb_port, n_modem=n_modem)

        zabers = {
            "{}".format(name_dev): {
                f"{axes[0]}": zaber1,
                f"{axes[1]}": zaber2,
                f"{axes[2]}": zaber3,
            }
        }
    except Exception as e:
        errorloc(e)
    return zabers


def changeSpeed(zabers, device=None, speed=153600 * 4):

    if device:
        for k in zabers[device]:
            try:
                zabers[device][k].send(f"set maxspeed {speed}")
            except:
                zabers[device][k].device.send(f"set maxspeed {speed}")
    else:
        try:
            zabers.send(f"set maxspeed {speed}")
        except:
            zabers.device.send(f"set maxspeed {speed}")


def changeAmount(key):
    while True:
        if not keyboard.is_pressed(key):
            tcflush(sys.stdin, TCIFLUSH)
            new_amount = input("\n\nAmount to move: ")
            try:
                new_amount = int(new_amount)
                break
            except Exception as e:
                errorloc(e)

    return new_amount


def handleOutOfRange(
    response,
    zaber,
    axis,
    current_device,
    amount=default_amount,
    models=zaber_models_default,
    ends=zaber_models_end_default,
):

    try:
        pos = zaber[axis].send("/get pos")
    except:
        pos = zaber[axis].device.send("/get pos")

    if response.data == "BADDATA":
        if int(pos.data) < amount:
            try:
                zaber[axis].move_abs(0)
            except:
                zaber[axis].device.move_abs(0)
            print("OUT OF START")
        else:
            model = models[current_device][axis]
            try:
                zaber[axis].move_abs(ends[model])
            except:
                zaber[axis].device.move_abs(ends[model])
            print("OUT OF END")


def triggered_exception(
    zabers=None,
    platform=None,
    path_day=None,
    path_anal=None,
    path_data=None,
    path_videos=None,
    path_figs=None,
    arduino_syringe=None,
    arduino_dimmer=None,
    arduino_pantilt=None,
    e=None,
    outcome="failed",
):

    if e:
        errorloc(e)
    else:
        print("Keyboard Interrupt")

    if path_data:
        rootToUser(path_day, path_anal, path_data, path_figs, path_videos)
        changeNameTempFile(path_data, outcome=outcome)

    if zabers:
        # check colther position
        colther_x_pos = zabers["colther"]["x"].device.send("/get pos")
        colther_y_pos = zabers["colther"]["y"].device.send("/get pos")
        pos_colther = [
            not colther_x_pos.warning_flag == "--",
            not colther_y_pos.warning_flag == "--",
        ]

        # check touch position
        tactile_x_pos = zabers["tactile"]["x"].send("/get pos")
        tactile_y_pos = zabers["tactile"]["y"].send("/get pos")
        pos_tactile = [
            not tactile_x_pos.warning_flag == "--",
            not tactile_y_pos.warning_flag == "--",
        ]

        homingZabersConcu(zabers, {"colther": ["z", "x", "y"]})
        # print(tactile_x_pos.data)
        # print(tactile_y_pos.data)
        # print(not any(pos_tactile))
        # print(not any(pos_colther))
        # if not any(pos_tactile) and not any(pos_colther) and int(tactile_x_pos.data) > 1000 and int(tactile_y_pos.data) > 1000:
        #     moveAxisTo(zabers, 'tactile', 'z', globals.base_touch)
        # homingZabersConcu(zabers, {'colther': ['x']})

        if (
            not any(pos_tactile)
            and not any(pos_colther)
            and int(colther_x_pos.data) > 1000
            and int(colther_y_pos.data) > 1000
        ):
            moveAxisTo(zabers, "colther", "y", globals.dry_ice_pos["y"])
        homingZabersConcu(zabers, {"camera": ["z"]})
        if platform:
            platform.device.move_abs(0)

        if (
            not any(pos_tactile)
            and not any(pos_colther)
            and int(tactile_x_pos.data) > 1000
            and int(tactile_y_pos.data) > 1000
        ):
            moveAxisTo(zabers, "tactile", "x", 533332)
        homingZabersConcu(zabers, {"tactile": ["y", "z"]})

    if arduino_syringe:
        globals.stimulus = 0
        arduino_syringe.arduino.write(struct.pack(">B", globals.stimulus))
        time.sleep(0.1)

    if arduino_pantilt:
        arduino_pantilt.arduino.write(struct.pack(">B", 8))
        time.sleep(globals.keydelay)
        arduino_pantilt.arduino.write(
            struct.pack(
                ">BBB",
                globals.default_pantilt[0],
                globals.default_pantilt[1],
                globals.default_pantilt[2],
            )
        )
        time.sleep(0.1)

    if arduino_dimmer:
        globals.lamp = 0
        arduino_dimmer.arduino.write(struct.pack(">B", globals.lamp))

    if zabers:
        homingZabersConcu(zabers, default_haxes, speed=globals.speed)


def reducegrid(dictionary, list_to_remove):
    """
    Function to remove a given keys froma dictionary and redefine the keys from '1' upwards
    """

    for i in list_to_remove:
        del dictionary[i]

    reduced_grid = {}

    for i, v in enumerate(dictionary.values()):
        reduced_grid[f"{i+1}"] = v

    return reduced_grid


def findHeight(delta):
    time_adjust = 0.8
    slope = -2.2589600000000023
    intercept = 15.199626666666676
    height = (intercept - delta) / slope - time_adjust
    if height < 0:
        height = abs(height)
    elif height > 0:
        height = 4
    height = round(height, 2)
    # clamp within range
    low_bound = 4
    high_bound = 6.5
    if height < low_bound:
        height = low_bound
    if height > high_bound:
        height = high_bound

    return height