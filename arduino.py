#!/usr/bin/env python3
from grabPorts import grabPorts
from text import printme, waitForEnter
from failing import errorloc
from saving_data import writeSingleValue

# OTHER'S CODE
import time
import serial
import numpy as np
import struct
import os
import keyboard

class ArdUIno(grabPorts):
    def __init__(
        self, winPort=None, num_ards=1, usb_port=None, n_modem=None, name="Arduino"
    ):

        self.ports = grabPorts()
        self.n_modem = n_modem
        self.usb_port = usb_port
        self.name = name
        self.ports.arduinoPort(winPort, num_ards, usb_port, self.n_modem)
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

################################################################################
############################# FUNCTIONS #########################################
################################################################################


def reLoad(ard, up = 5, down = 6):
    os.system("clear")
    was_pressed = False
    printme('Position syringe pusher ("d" for down / "u" for up / "e" to move on)')
    while True:
        if keyboard.is_pressed("e"):
            break

        elif keyboard.is_pressed("d"):
            if not was_pressed:
                try:
                    ard.arduino.write(struct.pack(">B", down))
                except Exception as e:
                    errorloc(e)
                was_pressed = True

        elif keyboard.is_pressed("u"):
            if not was_pressed:
                try:
                    ard.arduino.write(struct.pack(">B", up))
                except Exception as e:
                    errorloc(e)
                was_pressed = True
        else:
            was_pressed = False


def shakeShutter(ard, times, open = 1, close = 0):
    for i in np.arange(times):
        ard.arduino.write(struct.pack(">B", open))
        printme("Open shutter")

        time.sleep(0.2)

        ard.arduino.write(struct.pack(">B", close))

        printme("Close shutter")
        time.sleep(0.2)


def tryexceptArduino(ard, signal):
    try:
        ard.arduino.write(struct.pack(">B", signal))
        print(f"TALKING TO {ard.name}")
        time.sleep(0.1)

    except Exception as e:
        os.system("clear")
        errorloc(e)
        waitForEnter(f"\n\n Press enter when {ard.name} is fixed...")
        ard = ArdUIno(usb_port=ard.usb_port, n_modem=ard.n_modem)
        ard.arduino.flushInput()
        time.sleep(1)
        ard.arduino.write(struct.pack(">B", signal))
        time.sleep(0.1)

    if signal == 6:
        file_path = "./data/"
        file_name = "pusher_counter"
        file = open((file_path + file_name))
        old_value = int(file.read())
        old_value += 1
        writeSingleValue(file_path, file_name, old_value)


def movePanTilt(ard, trio_array, usb_port_pantilt, modem_port_pantilt, keydelay = 0.15, trigger_move=8):
    printme(
        f"Sending to PanTilt x: {trio_array[0]}, y: {trio_array[1]}, z: {trio_array[2]}"
    )
    try:
        ard.arduino.write(struct.pack(">B", trigger_move))
        time.sleep(keydelay)
        ard.arduino.write(
            struct.pack(">BBB", trio_array[0], trio_array[1], trio_array[2])
        )
    except Exception as e:
        os.system("clear")
        errorloc(e)
        waitForEnter(f"\n\n Press enter when Arduino PanTilt is fixed...")
        ard = ArdUIno(
            usb_port=usb_port_pantilt, n_modem=modem_port_pantilt
        )
        ard.arduino.flushInput()
        time.sleep(1)
        ard.arduino.write(struct.pack(">B", trigger_move))
        time.sleep(keydelay)
        ard.arduino.write(
            struct.pack(">BBB", trio_array[0], trio_array[1], trio_array[2])
        )

    print("TALKING TO PANTILT")