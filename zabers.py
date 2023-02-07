#!/usr/bin/env python3
import numpy as np
import math
from termios import TCIFLUSH, tcflush
import sys
import os
import threading
import zaber.serial as zs
import keyboard

from failing import errorloc
from grabPorts import grabPorts

default_amount = 10000

default_haxes = {
    "colther": ["z", "x", "y"],
    "camera": ["x", "z", "y"],
    "tactile": ["y", "x", "z"],
}

default_step_sizes = {"colther": 0.49609375, "camera": 0.1905, "tactile": 0.1905}

default_positions = {
    "colther": {"x": 233126, "y": 106874, "z": 0},
    "camera": {"x": 49507, "y": 535098, "z": 287000},
    "tactile": {"x": 336000, "y": 380000, "z": 270000},
}

zaber_models_default = {
    "colther": {"x": "end_X-LSQ150B", "y": "end_A-LSQ150B", "z": "end_A-LSQ150B"},
    "camera": {"x": "end_LSM100B-T4", "y": "end_LSM100B-T4", "z": "end_LSM100B-T4"},
    "tactile": {"x": "end_LSM100B-T4", "y": "end_LSM100B-T4", "z": "end_LSM100B-T4"},
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

    def __repr__(self):

        return "Device {} at port {}".format(self.device, self.port)


################################################################################################################
################################################################################################################
############################ FUNCTIONS
################################################################################################################
################################################################################################################

def move(zaber, amount, rules):
    amount = revDirection(zaber.device_name, zaber.axis, rules, amount)
    try:
        response = zaber.device.move_rel(amount)
    except:
        response = zaber.move_rel(amount)

    handleOutOfRange(
        response,
        zaber,
        amount,
        zaber_models_default,
        zaber_models_end_default,
    )
    

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
    camera3 = Zaber(1, name = "serial", surname = "-AH0614UB")
    print("Camera loaded")

    tactile12 = Zaber(1, name = "modem", surname = 759331)
    tactile1 = tactile12.device.axis(1)
    tactile2 = tactile12.device.axis(2)
    tactile3 = Zaber(1, name = "serial", surname = "-AB0NZPLK")
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

    for zaber in zabers:
        for axis in zabers[zaber]:
            zabers[zaber][axis].device_name = zaber
            zabers[zaber][axis].axis = axis

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

def homingZabersConcu(zabers, axes=None, concurrently = True, speed=153600 * 4):
    """
    This function is to home all zabers in a Zaber object concurrently
    """

    def homeOneAxis(kaxes, d, speed):
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
            hz = threading.Thread(target=homeOneAxis, args=[kaxes, d, speed])
            threads_zabers.append(hz)

        for x in threads_zabers:
            x.start()
            if not concurrently:
                x.join()

        if concurrently:
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
    amount,
    models,
    ends,
):

    try:
        pos = zaber.send("/get pos")
    except:
        pos = zaber.device.send("/get pos")

    if response.data == "BADDATA":
        if int(pos.data) < abs(amount):
            try:
                zaber.move_abs(0)
            except:
                zaber.device.move_abs(0)
            print("OUT OF START")
        else:
            model = models[zaber.device_name][zaber.axis]
            try:
                zaber.move_abs(ends[model])
            except:
                zaber.device.move_abs(ends[model])
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