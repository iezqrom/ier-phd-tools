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

try:
    import os
except:
    pass

# My stuff
try:
    import globals
except:
    pass
from grabPorts import grabPorts
from classes_text import *
from failing import *

# Maths
import numpy as np
import pandas as pd
import curses
import re
import struct
from scipy import signal

class ArdUIno(grabPorts):

    def __init__(self, winPort = None, num_ards = 1, usb_port = None, n_modem = None, name = 'Arduino'):

        self.ports = grabPorts()
        self.n_modem = n_modem
        self.usb_port = usb_port
        self.name = name
        self.ports.arduinoPort(winPort, num_ards, usb_port, self.n_modem)
        # printme(f'Arduino port: {print_var_name(self)}')
        print(str(self.ports.arduino_ports))

        if num_ards == 1:
            try:
                self.arduino = serial.Serial(self.ports.arduino_ports[0], 9600, timeout = 1)
            except IndexError:
                print('I cannot find any arduino boards!')
        elif num_ards > 1:
            self.arduino1 = serial.Serial(self.ports.arduino_ports[0], 9600, timeout = 1)
            self.arduino2 = serial.Serial(self.ports.arduino_ports[1], 9600, timeout = 1)

        self.arduino.flushInput()

    def readData(self, dataParser = float, event = None):
        while True:
            try:
                read = self.arduino.readline()
                read_float = dataParser(read)
                print('Data_ard: ' + str(read_float))
                if read_float > 400:
                    globals.data = globals.data
                else:
                    globals.data = read_float
            except Exception as e:
                print(e)
                globals.data = globals.data
            
            if event != None:
                event.set()
                # print('EVENT')

            if keyboard.is_pressed('e'):
                break
        
        printme('Reading done')

    def OpenClose(self, wait_close, wait_open, devices = None):

        if devices != None:
            devices[0].device.move_abs(globals.posX)
            devices[1].device.move_abs(globals.posY)
            devices[2].device.move_abs(globals.posZ)

        while True:

            try:

                time.sleep(wait_close*1/10)

                globals.stimulus = 1
                self.arduino.write(struct.pack('>B', globals.stimulus))


                time.sleep(wait_open)

                globals.stimulus = 0
                self.arduino.write(struct.pack('>B', globals.stimulus))


                time.sleep(wait_close*9/10)

                globals.counter +=1

                if globals.counter == 3:
                    globals.stimulus = 0
                    self.arduino.write(struct.pack('>B', globals.stimulus))
                    break
                # if keyboard.is_pressed('e'):
                #
                #     globals.stimulus = 0
                #     self.arduino.write(struct.pack('>B', globals.stimulus))
                #     break

            except KeyboardInterrupt:
                sys.exit(1)

    def controlShu(self, devices):

        while True:
            try:

                if keyboard.is_pressed('c'):
                    globals.stimulus = 0
                    self.arduino.write(struct.pack('>B', globals.stimulus))

                if keyboard.is_pressed('o'):
                    globals.stimulus = 1
                    self.arduino.write(struct.pack('>B', globals.stimulus))

                if keyboard.is_pressed('u'):
                    devices['colther'][0].device.move_rel(-20000)

                if keyboard.is_pressed('d'):
                    devices['colther'][0].device.move_rel(20000)

                if keyboard.is_pressed('e'):

                    globals.stimulus = 0
                    self.arduino.write(struct.pack('>B', globals.stimulus))
                    break

                try:
                    pos = devices['colther'][0].device.send("/get pos")
                    globals.pos = int(pos.data)
                except:
                    pass
            except KeyboardInterrupt:
                sys.exit(1)

    def OpenCloseMoL(self, event):
        """
            Method to perform Method of Limits with the shutter
        """

        if event != None:
            event.wait()

        globals.stimulus = 2

        if event != None:
            event.clear()
        
        self.arduino.write(struct.pack('>B', globals.stimulus))
        printme('Start reaction time')
        start = time.time()
        # time.sleep(0.2)

        while True:
            time.sleep(0.001)
            if globals.stimulus == 4:
                globals.rt = time.time() - start
                self.arduino.write(struct.pack('>B', globals.stimulus))
                # time.sleep(0.1)
                break

    def readFloat(self, start, finish, globali, event):
        while True:
            read = self.arduino.readline()
            cropp = read[start:finish]
            # print(read)
            try:
                float_cropp = float(cropp)
                rounded_float_cropp = round(float_cropp, 3)

                globali.set(rounded_float_cropp)
            except Exception as e:
                print(e)

            if keyboard.is_pressed('enter'):
                event[0].set()
                break
            elif keyboard.is_pressed('l'):
                event[0].set()
                # print('Waiting for Zaber to move')
                event[1].wait()

    def closeOpenTemp(self, range):
        """
            Method of function to close and open shutter depending on the temperature
        """

        while True:
            # print(globals.temp)
            if globals.temp < range[0]:
                # print('Close')
                globals.stimulus = 0
                self.arduino.write(struct.pack('>B', globals.stimulus))
            elif globals.temp > range[1]:
                # print('Open')
                globals.stimulus = 1
                self.arduino.write(struct.pack('>B', globals.stimulus))
            
            if globals.momen > globals.timeout:
                printme('Finish shutter')
                globals.stimulus = 0
                self.arduino.write(struct.pack('>B', globals.stimulus))
                break

    def readDistance(self):
        """
            Method to read distance and save it during a period set manually
        """
        self.buffer = []
        save_buffer = False
        pressed = False
        while True:
            # 
            read = self.arduino.readline()
            if save_buffer:
                self.buffer.append(float(read))
            try:
                print(float(read))
            except:
                printme('Arduino sent garbage')

            if keyboard.is_pressed('e'):
                printme('Done reading distance...')
                break
            elif keyboard.is_pressed('s'):
                if not pressed:
                    printme('STARTED saving readings from Arduino')
                    save_buffer = True
                    pressed = True
            elif keyboard.is_pressed('o'):
                if not pressed:
                    printme('STOPPED saving readings from Arduino')
                    save_buffer = False
                    pressed = True
            else:
                pressed = False



################################################################################
############################# FUNCTION #########################################
################################################################################

def reLoad(ard):
    os.system('clear')
    was_pressed = False
    print('\nPosition syringe pusher ("d" for down / "u" for up / "e" to move on)\n')
    while True:
        if keyboard.is_pressed('e'):
            break

        elif keyboard.is_pressed('d'):
            if not was_pressed:
                try:
                    globals.stimulus = 6
                    ard.arduino.write(struct.pack('>B', globals.stimulus))
                except Exception as e:
                    errorloc(e)
                was_pressed = True

        elif keyboard.is_pressed('u'):
            if not was_pressed:
                try:
                    globals.stimulus = 5
                    ard.arduino.write(struct.pack('>B', globals.stimulus))
                except Exception as e:
                    errorloc(e)
                was_pressed = True
        else:
            was_pressed = False

def shakeShutter(ard, times):
    for i in np.arange(times):
        globals.stimulus = 1
        ard.arduino.write(struct.pack('>B', globals.stimulus))
        printme('Open shutter')

        time.sleep(0.2)

        globals.stimulus = 0
        ard.arduino.write(struct.pack('>B', globals.stimulus))

        printme('Close shutter')
        time.sleep(0.2)

def tryexceptArduino(ard, signal, name = 'Arduino', n_modem = None, usb_port = 1):
    try:
        ard.arduino.write(struct.pack('>B', signal))
        print(f'TALKING TO {ard.name}')
        # print(signal)

        time.sleep(0.2)
    except Exception as e:
        os.system('clear')
        errorloc(e)
        waitForEnter(f'\n\n Press enter when {ard.name} is fixed...')
        ard = ArdUIno(usb_port = ard.usb_port, n_modem = ard.n_modem)
        ard.arduino.flushInput()
        time.sleep(1)
        ard.arduino.write(struct.pack('>B', signal))

        time.sleep(0.2)

def movePanTilt(ard, trio_array, trigger_move = 8):
    print(trio_array[0], trio_array[1], trio_array[2])
    try:
        ard.arduino.write(struct.pack('>B', trigger_move))
        time.sleep(globals.keydelay)
        ard.arduino.write(struct.pack('>BBB', trio_array[0], trio_array[1], trio_array[2]))
    except Exception as e:
        os.system('clear')
        errorloc(e)
        waitForEnter(f'\n\n Press enter when Arduino PanTilt is fixed...')
        ard = ArdUIno(usb_port = globals.usb_port_pantilt, n_modem = globals.modem_port_pantilt)
        ard.arduino.flushInput()
        time.sleep(1)
        ard.arduino.write(struct.pack('>B', trigger_move))
        time.sleep(globals.keydelay)
        ard.arduino.write(struct.pack('>BBB', trio_array[0], trio_array[1], trio_array[2]))

    print('TALKING TO PANTILT')

Fs = 20; # sampling freq
Fc = 2; # cutoff
[b, a] = signal.butter(2, Fc/(Fs/2))

def smoother(datapoint):
    d_cen_round_filtered = b[0] * data2[-1] + b[1] * data2[-2] + b[2] * data2[-3] - a[1] * df2[-1] - a[2] * df2[-2]

def print_var_name(variable):
 for name in globals():
     if eval(name) == variable:
        print(name)


################ Developing Trash
# def ardRun(self, save = 'N', subjN = None, trial_counter = None):
#     # import time
#     self.arduino.flushInput()
#     counter = 0
#
#     temp_array = []
#     threshold = []
#     time_array = []
#
#     while globals.distance > globals.distance_limit and globals.trial == 'on':
#         if globals.status == 'active':
#
#             if counter == 0:
#
#                 # print('we are here')
#
#                 self.arduino.flushInput()
#
#                 shutter = 'open'
#
#                 sleep(2)
#
#                 self.arduino.write(shutter.encode())
#                 winsound.PlaySound('beep.wav', winsound.SND_ASYNC)
#                 counter += 1
#
#
#             else:
#
#                 sleep(0.0001)
#                 data = self.arduino.readline()
#                 # print('still readin arduino')
#                 sleep(0.0001)
#
#
#                 try:
#                     data = str(data)
#                     data = data[2:9]
#                     # print(data)
#                     var, value = data.split("_")
#                     # print("var: " + var)
#                     # print("value: " + value)
#
#                     if var == 't':
#                         # print('This is MAI temp: ' + value)
#                         value_t = float(value)
#                         globals.temp = value_t
#                         time = time.time()
#
#                         temp_array.append(globals.temp)
#                         threshold.append(globals.thres)
#                         time_array.append(time)
#
#
#                     elif var == 'd':
#                         # print('This is MAI distance: ' + value)
#                         value_d = float(value)
#                         globals.distance = value_d
#
#                 except:
#                     continue
#
#             if globals.status == 'inactive':
#                 # sleep(2)
#                 # print('killing')
#                 shutter = globals.shutter
#                 print(shutter)
#                 self.arduino.write(shutter.encode())
#
#                 if save == 'Y':
#                     dataFile = open('./data/subj_{}/trial_{}.csv'.format(subjN, trial_counter), 'a')
#                     data_writer = csv.writer(dataFile)
#
#                     for i in np.arange(len(temp_array)):
#                         data_writer.writerow(temp_array[i], threshold[i], time_array[i])
#                     dataFile.close()
#
#                 break
#
#
#         elif globals.status == 'inactive':
#             shutter = globals.shutter
#             self.arduino.write(shutter.encode())
#             # print('ard')
#             continue
#
#     globals.shutter = 'close'
#     shutter = globals.shutter
#     self.arduino.write(shutter.encode())
#     # print(globals.temp)
#     # print(globals.distance)
#     print('Arduino dead')
#
# def AllIn(self):
#
#     ports = grabPorts()
#     ports.arduinoPort()
#     arduino = serial.Serial(ports.arduino_port, 9600, timeout = 5)
#
#     time.sleep(0.01)
#     arduino.flush()
#
#     state = 'open'
#     arduino.write(state)
#     time.sleep(0.001)
#
#     while globals.status == None and globals.distance > globals.distance_limit and globals.elapsed < globals.time_limit:
#         data = arduino.readline()
#         time.sleep(0.0001)
#         # print(globals.status)
#         # print(globals.distance)
#         # print(globals.elapsed)
#
#         try:
#             data = str(data)
#             data = data[2:9]
#             # print(data)
#             var, value = data.split("_")
#             # print("var: " + var)
#             # print("value: " + value)
#
#             if var == 't':
#                 # print('This is MAI temp: ' + value)
#                 value_t = float(value)
#                 globals.temp = value_t
#
#
#             elif var == 'd':
#                 # print('This is MAI distance: ' + value)
#                 value_d = float(value)
#                 globals.distance = value_d
#
#         except:
#             continue
#
#     state = 'close'
#     arduino.write(state)
#     time.sleep(0.001)
#
# def writeString(self):
#
#     while True:
#
#         written = self.arduino.write(globals.meanStr.encode())
#         # print(written)
#
#         read = self.arduino.readline()
#         print(read)
#
#         if keyboard.is_pressed('e'):
#
#             break
