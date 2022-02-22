# Time
from datetime import datetime
import time
from time import sleep

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


from classes_arduino import ArdUIno
from grabPorts import grabPorts


# Maths
import numpy as np
import pandas as pd
import curses

import tkinter as tk
from tkinter import font as tkfont
import threading


class AttentionScreen:
    def __init__(self, message, data, repeats):

        self.win = Tk()
        # self.win.title("Python GUI")

        time.sleep(0.0001)

        self.win.attributes("-fullscreen", True)
        label = Label(
            self.win,
            text="{}".format(message),
            bg="black",
            fg="white",
            font="none 50 bold",
            anchor=CENTER,
        )

        buttonT = Button(
            self.win,
            text=" ",
            bg="black",
            width=1,
            command=self.thermode_screen(data),
            anchor=CENTER,
            highlightthickness=0.01,
            borderwidth=0.01,
        )

        self.win.after(repeats * 10000, lambda: self.win.destroy())

        buttonT.grid(column=1, row=0)
        # buttonD.grid(column = 2, row = 0)
        label.grid(column=0, row=0)

        self.win.configure(background="black")
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(0, weight=1)

        # self.win.bind('<space>', lambda e: self.win.destroy())

        self.win.mainloop()

    def thermode_screen(self, data):

        thermodS = gethermodes()

        thermodS.InputChannels(data[0])
        thermodS.OutputChannels(data[1])

        therm_screen = threading.Thread(target=thermodS.run, args=[data])

        winsound.PlaySound("beep.wav", winsound.SND_ASYNC)
        therm_screen.start()


class InputScreen:
    def __init__(self, message, data):

        self.win = Tk()

        self.win.attributes("-fullscreen", True)

        def testVal(ans, acttyp):

            if acttyp == "1":  # insert
                #
                # try:
                #     inte = int(ans)
                #     return True
                # except:
                #     return False
                #

                if ans != "y" and ans != "n":
                    return False

            return True

        label = Label(
            self.win,
            text="{}".format(message),
            bg="black",
            fg="white",
            font="none 30 bold",
            anchor=CENTER,
        )

        label2 = Label(
            self.win,
            text="{}".format(
                "\n\n Click on the box, type your answer \n and press enter"
            ),
            bg="black",
            fg="white",
            font="none 15 bold",
            anchor=CENTER,
        )

        entry = Entry(self.win, validate="key")
        entry["validatecommand"] = (entry.register(testVal), "%P", "%d")

        label.grid(column=0, row=0)
        entry.grid(column=1, row=0)
        label2.grid(column=2, row=0)

        self.win.configure(background="black")
        self.win.columnconfigure(0)
        self.win.rowconfigure(0, weight=1)

        def enterEndTherm(event):

            globals.text_state += 1

            self.input = entry.get()
            self.win.destroy()

        self.win.bind("<Return>", enterEndTherm)
        self.win.mainloop()


class Fixation_cross(tk.Frame):
    def __init__(self, interval=1):
        """Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        """Method that runs forever"""

        # creating tkinter window
        win = Tk()

        # getting screen's height in pixels
        win.attributes("-fullscreen", True)
        win.configure(background="black")

        height = win.winfo_screenheight()
        width = win.winfo_screenwidth()

        center = width / 2, height / 2

        canvas = Canvas(
            win, background="black", width=width, height=height, highlightthickness=0
        )
        canvas.grid(row=0, column=0)
        canvas.create_line(
            center[0],
            center[1] + 100,
            center[0],
            center[1] - 100,
            fill="white",
            width=6,
        )
        canvas.create_line(
            center[0] + 100,
            center[1],
            center[0] - 100,
            center[1],
            fill="white",
            width=6,
        )

        # infinite loop

        # win.after(5000, win.destroy)
        win.mainloop()

    def thermode_screen(self, data):

        while True:

            trio = gethermodes()
            trio.InputChannels(data[0])
            trio.OutputChannels(data[1])

            therm_trio = threading.Thread(target=trio.run, args=[data])
            print("we almost started this")
            therm_trio.start()

            if globals.text_state == 1:
                break
            else:
                continue
