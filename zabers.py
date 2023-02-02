#!/usr/bin/env python3
import numpy as np
import math
import struct
from scipy import stats
from termios import TCIFLUSH, tcflush
import sys
import os
import threading
import zaber.serial as zs
import keyboard
import time

from failing import errorloc
from grabPorts import grabPorts
from text import printme
from saving_data import changeNameTempFile, rootToUser


default_amount = 10000

default_haxes = {
    "colther": ["z", "x", "y"],
    "camera": ["x", "z", "y"],
    "tactile": ["y", "x", "z"],
}

default_touch_z_offset = 52494

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

class Zaber(grabPorts):
    """
        Zaber class developed by Ivan Ezquerra-Romano at the Action & Body lab (2018-2023)
    """

    def __init__(self, n_device, name, surname, chained_to = None, winPort=None):
        self.ports = grabPorts()
        self.ports.zaberPort(name, surname, winPort)
        self.home = False

        if not chained_to:  # number 1 device is chosen to lead the Daisy chain
            self.port = zs.AsciiSerial(self.ports.zaber_port)
            self.device = zs.AsciiDevice(self.port, n_device)
        else:
            self.port = chained_to.port
            self.device = zs.AsciiDevice(self.port, n_device)

    def move(self, amount):
        try:
            response = self.device.move_rel(amount)
        except:
            response = self.move_rel(amount)

        handleOutOfRange(
            response,
            self.device,
            default_amount,
            zaber_models_default,
            zaber_models_end_default,
        )

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

    def __repr__(self):

        return "Device {} at port {}".format(self.device, self.port)


################################################################################################################
################################################################################################################
############################ FUNCTIONS
################################################################################################################
################################################################################################################

def manualControlPanTilt(
    devices,
    home=True,
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

    print("Zaber game activated")

    positions = {}
    current_device = "colther"
    amount = 10000

    device = devices[current_device]
    while True:
        if keyboard.is_pressed("up"):
            device["y"].move(-amount)

        elif keyboard.is_pressed("down"):
            device["y"].move(amount)

        elif keyboard.is_pressed("right"):
            device["x"].move(amount)

        elif keyboard.is_pressed("left"):
            device["x"].move(-amount)

        elif keyboard.is_pressed("u"):
            device["x"].move(-amount)

        elif keyboard.is_pressed("d"):
            device["x"].move(amount)

        elif keyboard.is_pressed("5"):
            if not was_pressed:
                amount = 10000
                was_pressed = True

        elif keyboard.is_pressed("6"):
            if not was_pressed:
                amount = 1000
                was_pressed = True

        elif keyboard.is_pressed("6"):
            if not was_pressed:
                amount = 500
                was_pressed = True

        ### TERMINATE
        elif keyboard.is_pressed(f"{end_button}"):
            if home:
                homingZabers(devices)
            print("Terminating Zaber game \n")
            break

        #### GET POSITION
        elif keyboard.is_pressed("p"):
            if not was_pressed:
                positions[current_device] = grabPositions(device)

                printme(positions[current_device])
                was_pressed = True

        # Press letter h and Zaber will home, first z axis, then y and finally x
        # Control
        elif keyboard.is_pressed("h"):
            homingZabers(devices)

        #### Change Zaber
        elif keyboard.is_pressed("k"):
            if not was_pressed:
                pantilt_on = not pantilt_on
                device = devices["camera"]
                current_device = "camera"
                print(f"Controlling CAMERA zabers")
                was_pressed = True

        elif keyboard.is_pressed("f"):
            if not was_pressed:
                device = devices["colther"]
                current_device = "colther"
                print(f"Controlling COLTHER zabers")
                print(device)
                was_pressed = True

        elif keyboard.is_pressed("t"):
            if not was_pressed:
                device = devices["tactile"]
                current_device = "tactile"
                print(f"Controlling TACTILE zabers")
                was_pressed = True

        elif keyboard.is_pressed("a"):
            if not was_pressed:
                amount = changeAmount("a")
                was_pressed = True

        else:
            was_pressed = False
            continue



    # def gridManualControlPantilt(
    #     self,
    #     devices,
    #     ardpantilt,
    #     rules,
    #     platformcamera=None,
    #     arduino=None,
    #     haxes=default_haxes,
    # ):
    #     """
    #     (for dermatome distance experiment) Method for Object Zaber to move the 3 axes of THREE zabers with keyboard presses. Like a game!
    #     The coordinates of two positions can be saved with 'z' and 'x'
    #     This method was created and it is specific to the experiment in which we measure cold
    #     thresholds with and without touch
    #     """

    #     was_pressed = False
    #     pantilt_on = True

    #     touched = False

    #     if arduino:
    #         stimulus = 0
    #         arduino.arduino.write(struct.pack(">B", stimulus))

    #     # Build dictionary of rois
    #     r_zaber = "camera"

    #     self.rois = {}
    #     self.pantilts = {}
    #     self.gridcamera = grid["camera"]

    #     grid_i = list(np.arange(1, len(grid[r_zaber]) + 0.1, 1))
    #     for i in grid_i:
    #         self.rois[str(int(i))] = []

    #     keydelay = 0.15
    #     pan, tilt, head = 0, 0, 0
    #     device = devices["camera"]

    #     print("\nZaber game activated\n")

    #     current_device = "camera"
    #     try:
    #         current_roi = "1"

    #         while True:
    #             try:
    #                 red = ardpantilt.arduino.readline()
    #             except Exception as e:
    #                 errorloc(e)

    #             if keyboard.is_pressed("p"):
    #                 if not was_pressed:
    #                     if len(str(red)) > 10:
    #                         try:
    #                             pan, tilt, head = str(red)[2:-5].split("-")
    #                         except Exception as e:
    #                             errorloc(e)
    #                     self.rois[current_roi] = [globals.indx0, globals.indy0]
    #                     default_pan_tilt_values[current_roi] = [
    #                         int(pan),
    #                         int(tilt),
    #                         int(head),
    #                     ]

    #                     try:
    #                         posXk = devices["camera"]["x"].send("/get pos")

    #                     except:
    #                         posXk = devices["camera"]["x"].device.send("/get pos")

    #                     try:
    #                         posYk = devices["camera"]["y"].send("/get pos")
    #                     except:
    #                         posYk = devices["camera"]["y"].device.send("/get pos")

    #                     try:
    #                         posZk = devices["camera"]["z"].send("/get pos")
    #                     except:
    #                         posZk = devices["camera"]["z"].device.send("/get pos")

    #                     print(f"Centre of ROI is: {self.rois[current_roi]}")
    #                     print(f"Pan/tilt head position is: {pan} {tilt} {head}")
    #                     print(
    #                         f"Position camera: {int(posXk.data)} {int(posYk.data)} {int(posZk.data)}"
    #                     )

    #                     self.gridcamera[current_roi]["x"] = int(posXk.data)
    #                     self.gridcamera[current_roi]["y"] = int(posYk.data)
    #                     self.gridcamera[current_roi]["z"] = int(posZk.data)

    #                     was_pressed = True

    #             ### TERMINATE
    #             elif keyboard.is_pressed("e"):
    #                 # print([len(n) < 2 for n in list(self.rois.values())])
    #                 if not any(
    #                     [len(n) < 2 for n in list(self.rois.values())]
    #                 ):  # and not any(list(checked.values())):
    #                     self.pantilts = default_pan_tilt_values
    #                     break
    #                 else:
    #                     print("You are missing something...")
    #                     # print(self.rois, self.pantilts, checked)
    #                     was_pressed = True

    #             elif keyboard.is_pressed("k"):
    #                 if not was_pressed:
    #                     pantilt_on = not pantilt_on
    #                     was_pressed = True

    #             elif keyboard.is_pressed("a"):
    #                 if not was_pressed:
    #                     tryexceptArduino(arduino, 6)
    #                     was_pressed = True

    #             elif keyboard.is_pressed("5"):
    #                 if not was_pressed:
    #                     default_amount = 10000
    #                     was_pressed = True

    #             elif keyboard.is_pressed("6"):
    #                 if not was_pressed:
    #                     default_amount = 1000
    #                     was_pressed = True

    #             elif keyboard.is_pressed("7"):
    #                 if not was_pressed:
    #                     default_amount = 50000
    #                     was_pressed = True

    #             elif keyboard.is_pressed("o"):
    #                 if not was_pressed:
    #                     tryexceptArduino(arduino, 1)
    #                     was_pressed = True

    #             elif keyboard.is_pressed("c"):
    #                 if not was_pressed:
    #                     tryexceptArduino(arduino, 0)
    #                     was_pressed = True

    #             elif (
    #                 keyboard.is_pressed("up")
    #                 and not keyboard.is_pressed("i")
    #                 and not keyboard.is_pressed("l")
    #             ):
    #                 if pantilt_on:
    #                     ardpantilt.arduino.write(struct.pack(">B", 3))
    #                     time.sleep(keydelay)
    #                 else:
    #                     try:
    #                         response = device["y"].move_rel(
    #                             0
    #                             - revDirection(
    #                                 current_device, "y", rules, default_amount
    #                             )
    #                         )
    #                     except:
    #                         response = device["y"].device.move_rel(
    #                             0
    #                             - revDirection(
    #                                 current_device, "y", rules, default_amount
    #                             )
    #                         )

    #                     handleOutOfRange(
    #                         response,
    #                         device,
    #                         "y",
    #                         current_device,
    #                         default_amount,
    #                         zaber_models_default,
    #                         zaber_models_end_default,
    #                     )

    #             elif (
    #                 keyboard.is_pressed("down")
    #                 and not keyboard.is_pressed("i")
    #                 and not keyboard.is_pressed("l")
    #             ):
    #                 if pantilt_on:
    #                     ardpantilt.arduino.write(struct.pack(">B", 4))
    #                     time.sleep(keydelay)
    #                 else:
    #                     try:
    #                         response = device["y"].move_rel(
    #                             0
    #                             + revDirection(
    #                                 current_device, "y", rules, default_amount
    #                             )
    #                         )
    #                     except:
    #                         response = device["y"].device.move_rel(
    #                             0
    #                             + revDirection(
    #                                 current_device, "y", rules, default_amount
    #                             )
    #                         )

    #                     handleOutOfRange(
    #                         response,
    #                         device,
    #                         "y",
    #                         current_device,
    #                         default_amount,
    #                         zaber_models_default,
    #                         zaber_models_end_default,
    #                     )

    #             elif keyboard.is_pressed("right"):
    #                 if pantilt_on:
    #                     ardpantilt.arduino.write(struct.pack(">B", 2))
    #                     time.sleep(keydelay)
    #                 else:
    #                     try:
    #                         response = device["x"].move_rel(
    #                             0
    #                             + revDirection(
    #                                 current_device, "x", rules, default_amount
    #                             )
    #                         )
    #                     except:
    #                         response = device["x"].device.move_rel(
    #                             0
    #                             + revDirection(
    #                                 current_device, "x", rules, default_amount
    #                             )
    #                         )

    #                     handleOutOfRange(
    #                         response,
    #                         device,
    #                         "x",
    #                         current_device,
    #                         default_amount,
    #                         zaber_models_default,
    #                         zaber_models_end_default,
    #                     )

    #             elif keyboard.is_pressed("left"):
    #                 if pantilt_on:
    #                     ardpantilt.arduino.write(struct.pack(">B", 1))
    #                     time.sleep(keydelay)
    #                 else:
    #                     try:
    #                         response = device["x"].move_rel(
    #                             0
    #                             - revDirection(
    #                                 current_device, "x", rules, default_amount
    #                             )
    #                         )
    #                     except:
    #                         response = device["x"].device.move_rel(
    #                             0
    #                             - revDirection(
    #                                 current_device, "x", rules, default_amount
    #                             )
    #                         )

    #                     handleOutOfRange(
    #                         response,
    #                         device,
    #                         "x",
    #                         current_device,
    #                         default_amount,
    #                         zaber_models_default,
    #                         zaber_models_end_default,
    #                     )

    #             elif keyboard.is_pressed("u"):
    #                 if pantilt_on:
    #                     ardpantilt.arduino.write(struct.pack(">B", 5))
    #                     time.sleep(keydelay)
    #                 else:
    #                     try:
    #                         response = device["z"].move_rel(
    #                             0
    #                             - revDirection(
    #                                 current_device, "z", rules, default_amount
    #                             )
    #                         )
    #                     except:
    #                         response = device["z"].device.move_rel(
    #                             0
    #                             - revDirection(
    #                                 current_device, "z", rules, default_amount
    #                             )
    #                         )

    #                     handleOutOfRange(
    #                         response,
    #                         device,
    #                         "z",
    #                         current_device,
    #                         default_amount,
    #                         zaber_models_default,
    #                         zaber_models_end_default,
    #                     )

    #             elif keyboard.is_pressed("d"):
    #                 if pantilt_on:
    #                     ardpantilt.arduino.write(struct.pack(">B", 6))
    #                     time.sleep(keydelay)
    #                 else:
    #                     try:
    #                         response = device["z"].move_rel(
    #                             0
    #                             + revDirection(
    #                                 current_device, "z", rules, default_amount
    #                             )
    #                         )
    #                     except:
    #                         response = device["z"].device.move_rel(
    #                             0
    #                             + revDirection(
    #                                 current_device, "z", rules, default_amount
    #                             )
    #                         )

    #                     handleOutOfRange(
    #                         response,
    #                         device,
    #                         "z",
    #                         current_device,
    #                         default_amount,
    #                         zaber_models_default,
    #                         zaber_models_end_default,
    #                     )

    #             elif keyboard.is_pressed("h"):
    #                 triggeredException(
    #                     zabers=devices,
    #                     platform=platformcamera,
    #                     arduino_syringe=arduino,
    #                     arduino_pantilt=ardpantilt,
    #                 )

    #             elif keyboard.is_pressed("g"):
    #                 if not was_pressed:
    #                     print(f"Current spot: {current_roi}")
    #                     print("ROIS")
    #                     print(self.rois)
    #                     print("Pan tilt")
    #                     print(default_pan_tilt_values)
    #                     print("Camera positions")
    #                     print(self.gridcamera)
    #                     print("Checked Touch")
    #                     # print(checked)
    #                     was_pressed = True

    #             elif keyboard.is_pressed("n"):
    #                 if not was_pressed:
    #                     devices["colther"]["z"].device.move_abs(0)
    #                     try:
    #                         pre_touch = (
    #                             grid["tactile"][current_roi]["z"]
    #                             - default_touch_z_offset
    #                             # * globals.up_modifier_touch_height
    #                         )
    #                         movetostartZabersConcu(
    #                             devices, "tactile", ["z"], pos=pre_touch
    #                         )
    #                         moveAxisTo(devices, "tactile", "x", 533332)
    #                         moveAxisTo(devices, "tactile", "y", 1)
    #                     except:
    #                         print("HELLO")
    #                         pass

    #                     touched = False

    #                     current_roi = str(int(current_roi) + 1)
    #                     if int(current_roi) > len(grid[current_device]):
    #                         current_roi = "1"

    #                     movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

    #                     funcs = [
    #                         [
    #                             movetostartZabersConcu,
    #                             [
    #                                 devices,
    #                                 "camera",
    #                                 ["x", "y", "z"],
    #                                 grid["camera"][current_roi],
    #                             ],
    #                         ],
    #                         [
    #                             movetostartZabersConcu,
    #                             [
    #                                 devices,
    #                                 "colther",
    #                                 list(reversed(haxes["colther"])),
    #                                 grid["colther"][current_roi],
    #                             ],
    #                         ],
    #                     ]
    #                     threadFunctions(funcs)

    #                     was_pressed = True

    #             elif keyboard.is_pressed("b"):
    #                 if not was_pressed:
    #                     devices["colther"]["z"].device.move_abs(0)
    #                     try:
    #                         pre_touch = (
    #                             grid["tactile"][current_roi]["z"]
    #                             - default_touch_z_offset
    #                             # * globals.up_modifier_touch_height
    #                         )
    #                         movetostartZabersConcu(
    #                             devices, "tactile", ["z"], pos=pre_touch
    #                         )
    #                         moveAxisTo(devices, "tactile", "x", 533332)
    #                         moveAxisTo(devices, "tactile", "y", 1)
    #                     except:
    #                         pass

    #                     touched = False

    #                     current_roi = str(int(current_roi) - 1)
    #                     if int(current_roi) == 0:
    #                         current_roi = list(grid["colther"].keys())[-1]

    #                     movePanTilt(ardpantilt, default_pan_tilt_values[current_roi])

    #                     funcs = [
    #                         [
    #                             movetostartZabersConcu,
    #                             [
    #                                 devices,
    #                                 "camera",
    #                                 ["x", "y", "z"],
    #                                 grid["camera"][current_roi],
    #                             ],
    #                         ],
    #                         [
    #                             movetostartZabersConcu,
    #                             [
    #                                 devices,
    #                                 "colther",
    #                                 list(reversed(haxes["colther"])),
    #                                 grid["colther"][current_roi],
    #                             ],
    #                         ],
    #                     ]
    #                     threadFunctions(funcs)

    #                     was_pressed = True

    #             elif keyboard.is_pressed("z"):
    #                 if not was_pressed:
    #                     try:
    #                         posXf = devices["colther"]["x"].send("/get pos")

    #                     except:
    #                         posXf = devices["colther"]["x"].device.send("/get pos")

    #                     try:
    #                         posYf = devices["colther"]["y"].send("/get pos")
    #                     except:
    #                         posYf = devices["colther"]["y"].device.send("/get pos")

    #                     try:
    #                         posZf = devices["colther"]["z"].send("/get pos")
    #                     except:
    #                         posZf = devices["colther"]["z"].device.send("/get pos")

    #                     try:
    #                         posXk = devices["camera"]["x"].send("/get pos")

    #                     except:
    #                         posXk = devices["camera"]["x"].device.send("/get pos")

    #                     try:
    #                         posYk = devices["camera"]["y"].send("/get pos")
    #                     except:
    #                         posYk = devices["camera"]["y"].device.send("/get pos")

    #                     try:
    #                         posZk = devices["camera"]["z"].send("/get pos")
    #                     except:
    #                         posZk = devices["camera"]["z"].device.send("/get pos")

    #                     try:
    #                         posXt = devices["tactile"]["x"].send("/get pos")

    #                     except:
    #                         posXt = devices["tactile"]["x"].device.send("/get pos")

    #                     try:
    #                         posYt = devices["tactile"]["y"].send("/get pos")
    #                     except:
    #                         posYt = devices["tactile"]["y"].device.send("/get pos")

    #                     try:
    #                         posZt = devices["tactile"]["z"].send("/get pos")
    #                     except:
    #                         posZt = devices["tactile"]["z"].device.send("/get pos")

    #                     print("CAMERA")
    #                     print(posXk, posYk, posZk)

    #                     print("COLTHER")
    #                     print(posXf, posYf, posZf)

    #                     print("TACTILE")
    #                     print(posXt, posYt, posZt)

    #                     print("Pan/tilt position")
    #                     print(red)
    #                     was_pressed = True

    #             elif keyboard.is_pressed("t"):
    #                 if not was_pressed:
    #                     if not touched:
    #                         devices["colther"]["z"].device.move_abs(0)
    #                         pre_touch = (
    #                             grid["tactile"][current_roi]["z"]
    #                             - default_touch_z_offset
    #                             # * globals.up_modifier_touch_height
    #                         )
    #                         movetostartZabersConcu(
    #                             devices, "tactile", ["z"], pos=pre_touch
    #                         )
    #                         moveAxisTo(
    #                             devices,
    #                             "tactile",
    #                             "y",
    #                             grid["tactile"][current_roi]["y"],
    #                         )
    #                         moveAxisTo(
    #                             devices,
    #                             "tactile",
    #                             "x",
    #                             grid["tactile"][current_roi]["x"],
    #                         )
    #                         touching = grid["tactile"][current_roi]["z"] + round(
    #                             default_touch_z_offset
    #                             # * globals.down_modifier_touch_height
    #                         )
    #                         moveAxisTo(devices, "tactile", "z", touching)
    #                         moveAxisTo(
    #                             devices,
    #                             "colther",
    #                             "z",
    #                             grid["colther"][current_roi]["z"],
    #                         )

    #                     elif touched:
    #                         devices["colther"]["z"].device.move_abs(0)
    #                         pre_touch = (
    #                             grid["tactile"][current_roi]["z"]
    #                             - default_touch_z_offset
    #                             # * globals.up_modifier_touch_height
    #                         )
    #                         movetostartZabersConcu(
    #                             devices, "tactile", ["z"], pos=pre_touch
    #                         )
    #                         moveAxisTo(devices, "tactile", "x", 533332)
    #                         moveAxisTo(devices, "tactile", "y", 1)
    #                         moveAxisTo(
    #                             devices,
    #                             "colther",
    #                             "z",
    #                             grid["colther"][current_roi]["z"],
    #                         )

    #                     touched = not touched
    #                     was_pressed = True

    #             else:
    #                 was_pressed = False
    #                 continue

    #     finally:
    #         if arduino:
    #             stimulus = 0
    #             arduino.arduino.write(struct.pack(">B", stimulus))

def grabPositions(device):
    positions = {}
    for axis in ["x", "y", "z"]:
        try:
            pos = device[axis].send("/get pos")
        except:
            pos = device[axis].device.send("/get pos")

        positions[axis] = int(pos.data)

    return positions

def setUpBigThree(axes):

    ### Zabers
    colther1 = Zaber(1, name = "serial", surname = "-A104BTL5")
    colther2 = Zaber(2, name = "serial", surname = "-A104BTL5", chained_to = colther1)
    colther3 = Zaber(3, name = "serial", surname = "-A104BTL5", chained_to = colther1)
    print("Colther loaded")

    camera12 = Zaber(1, name = "modem", surname = 141214301)
    camera1 = camera12.device.axis(1)
    camera2 = camera12.device.axis(2)
    camera3 = Zaber(1, name = "serial", surname = "-AB0NZPLK")
    print("Camera loaded")

    tactile12 = Zaber(1, name = "modem", surname = 759331)
    tactile1 = tactile12.device.axis(1)
    tactile2 = tactile12.device.axis(2)
    tactile3 = Zaber(1, name = "serial", surname = "-AH0614UB")
    print("Tactile loaded")

    colther = {
        axes["colther"][0]: colther1,
        axes["colther"][1]: colther2,
        axes["colther"][2]: colther3,
    }
    camera = {
        axes["camera"][0]: camera1,
        axes["camera"][1]: camera2,
        axes["camera"][2]: camera3,
    }
    tactile = {
        axes["tactile"][0]: tactile1,
        axes["tactile"][1]: tactile2,
        axes["tactile"][2]: tactile3,
    }

    zabers = {"colther": colther, "camera": camera, "tactile": tactile}

    return zabers

def gridCalculation(
    zaber,
    grid_separation,
    rules,
    positions,
    step_size=default_step_sizes,
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

    one_cm_zaber_steps = grid_separation / (step_size[zaber] / 10000)

    grid = {}

    # Calculate origin
    x_origin = positions[zaber]["x"] - revDirection(zaber, "x", rules, one_cm_zaber_steps)
    y_origin = positions[zaber]["y"] - revDirection(zaber, "y", rules, one_cm_zaber_steps)

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
                    x_origin + revDirection(zaber, "x", rules, one_cm_zaber_steps * j)
                ),
                "y": math.ceil(
                    y_origin + revDirection(zaber, "y", rules, one_cm_zaber_steps * i)
                ),
                "z": positions[zaber]["z"],
            }
            # print(j, i)
            cell += 1

    print(f"\nGrid calculated for {zaber}\n")

    return grid

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


def cmToSteps(z_d, step_size):
    """
    Function to translate centimetres into Zaber steps
    """
    z_d_microm = z_d * 10000
    z_steps = z_d_microm / step_size
    return int(round(z_steps))


def stepsToCm(steps, step_size):
    """
    Function to translate Zaber steps into centimetres
    """
    microms = steps * step_size
    d_cm = microms / 10000
    return round(d_cm, 2)


def readReply(command):
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
    zaber,
    response,
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