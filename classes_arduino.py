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
import glob
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
from grabPorts import grabPorts


# Maths
import numpy as np
import pandas as pd
import curses
import re


class ArdUIno(grabPorts):

    def __init__(self, winPort = None, num_ards = 1, n_modem = None):

        self.ports = grabPorts()
        self.ports.arduinoPort(winPort, num_ards, n_modem)
        # print(self.ports.arduino_ports)

        if num_ards == 1:
            self.arduino = serial.Serial(self.ports.arduino_ports[0], 9600, timeout = 5)
        elif num_ards > 1:
            self.arduino1 = serial.Serial(self.ports.arduino_ports[0], 9600, timeout = 5)
            self.arduino2 = serial.Serial(self.ports.arduino_ports[1], 9600, timeout = 5)

    def OpenClose(self, wait_close, wait_open, devices = None):

        if devices != None:
            devices[0].device.move_abs(globals.posX)
            devices[1].device.move_abs(globals.posY)
            devices[2].device.move_abs(globals.posZ)

        while True:

            try:

                time.sleep(wait_close*1/10)

                shutter = 'open'

                self.arduino.write(shutter.encode())

                # time.sleep(0.9)
                temp_shutter = str(self.arduino.readline())
                # print(temp_shutter)
                globals.shutter_state = temp_shutter[temp_shutter.find("'")+1:temp_shutter.find(str("\\"))]
                print(globals.shutter_state)
                # sleep(0.0001)

                time.sleep(wait_open)

                shutter = 'close'

                self.arduino.write(shutter.encode())

                # time.sleep(0.9)
                temp_shutter = str(self.arduino.readline())
                # print(temp_shutter)
                globals.shutter_state = temp_shutter[temp_shutter.find("'")+1:temp_shutter.find(str("\\"))]
                print(globals.shutter_state)
                # sleep(0.0001)

                time.sleep(wait_close*9/10)


                if keyboard.is_pressed('e'):

                    globals.shutter_state = 'close'
                    print(globals.shutter_state)

                    self.arduino.write(globals.shutter_state.encode())

                    break

            except KeyboardInterrupt:
                sys.exit(1)

    def ardRun(self, save = 'N', subjN = None, trial_counter = None):
        # import time
        self.arduino.flushInput()
        counter = 0

        temp_array = []
        threshold = []
        time_array = []

        while globals.distance > globals.distance_limit and globals.trial == 'on':
            if globals.status == 'active':

                if counter == 0:

                    # print('we are here')

                    self.arduino.flushInput()

                    shutter = 'open'

                    sleep(2)

                    self.arduino.write(shutter.encode())
                    winsound.PlaySound('beep.wav', winsound.SND_ASYNC)
                    counter += 1


                else:

                    sleep(0.0001)
                    data = self.arduino.readline()
                    # print('still readin arduino')
                    sleep(0.0001)


                    try:
                        data = str(data)
                        data = data[2:9]
                        # print(data)
                        var, value = data.split("_")
                        # print("var: " + var)
                        # print("value: " + value)

                        if var == 't':
                            # print('This is MAI temp: ' + value)
                            value_t = float(value)
                            globals.temp = value_t
                            time = time.time()

                            temp_array.append(globals.temp)
                            threshold.append(globals.thres)
                            time_array.append(time)


                        elif var == 'd':
                            # print('This is MAI distance: ' + value)
                            value_d = float(value)
                            globals.distance = value_d

                    except:
                        continue

                if globals.status == 'inactive':
                    # sleep(2)
                    # print('killing')
                    shutter = globals.shutter
                    print(shutter)
                    self.arduino.write(shutter.encode())

                    if save == 'Y':
                        dataFile = open('./data/subj_{}/trial_{}.csv'.format(subjN, trial_counter), 'a')
                        data_writer = csv.writer(dataFile)

                        for i in np.arange(len(temp_array)):
                            data_writer.writerow(temp_array[i], threshold[i], time_array[i])
                        dataFile.close()

                    break


            elif globals.status == 'inactive':
                shutter = globals.shutter
                self.arduino.write(shutter.encode())
                # print('ard')
                continue

        globals.shutter = 'close'
        shutter = globals.shutter
        self.arduino.write(shutter.encode())
        # print(globals.temp)
        # print(globals.distance)
        print('Arduino dead')

    def AllIn(self):

        ports = grabPorts()
        ports.arduinoPort()
        arduino = serial.Serial(ports.arduino_port, 9600, timeout = 5)

        time.sleep(0.01)
        arduino.flush()

        state = 'open'
        arduino.write(state)
        time.sleep(0.001)

        while globals.status == None and globals.distance > globals.distance_limit and globals.elapsed < globals.time_limit:
            data = arduino.readline()
            time.sleep(0.0001)
            # print(globals.status)
            # print(globals.distance)
            # print(globals.elapsed)

            try:
                data = str(data)
                data = data[2:9]
                # print(data)
                var, value = data.split("_")
                # print("var: " + var)
                # print("value: " + value)

                if var == 't':
                    # print('This is MAI temp: ' + value)
                    value_t = float(value)
                    globals.temp = value_t


                elif var == 'd':
                    # print('This is MAI distance: ' + value)
                    value_d = float(value)
                    globals.distance = value_d

            except:
                continue

        state = 'close'
        arduino.write(state)
        time.sleep(0.001)

    def writeString(self):

        while True:

            written = self.arduino.write(globals.meanStr.encode())
            # print(written)

            read = self.arduino.readline()
            print(read)

            if keyboard.is_pressed('e'):

                break
