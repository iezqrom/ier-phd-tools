#!/usr/bin/env python3

#Time
from datetime import datetime
import time

#Array and maths
import numpy as np
import math
import random
import csv
import pandas as pd
import scipy as sci
from scipy import stats
import sklearn as skl
import scipy.stats as st
import statsmodels as sm
# import matplotlib
# matplotlib.use("TkAgg")
# import matplotlib.pyplot as plt

from numpy import (isscalar, r_, log, around, unique, asarray,
                   zeros, arange, sort, amin, amax, any, atleast_1d,
                   sqrt, ceil, floor, array, compress,
                   pi, exp, ravel, count_nonzero, sin, cos, arctan2, hypot)

#System
import threading
from multiprocessing import pool
from multiprocessing.pool import ThreadPool
import sys
import warnings
import itertools
import keyboard
from tkinter import *
from tkinter import filedialog as tkfd
import zaber.serial as zs
import serial

# # MATLAB
# try:
#     import matlab.engine as me
# except:
#     print('No module Matlab')
## NIDAQMX
import nidaqmx.system.watchdog as nsw
import nidaqmx.stream_writers as nsw
import nidaqmx.stream_readers as nsr
import nidaqmx._task_modules.out_stream as nto
import nidaqmx._task_modules.timing as ntt
import nidaqmx.constants as NC
import nidaqmx.task as NT

#Image
from PIL import Image
from PIL import ImageTk

## Sound
try:
    import winsound
except:
    pass
    # print('This is not a Windows device')
    # import audio

## My scripts
try:
    import globals
except:
    pass

class laser(object):

     def __init__(self, lower = 30, upper = 60):
         self.range_temp = np.arange(30, 60, 0.3)
         self.temp = np.array([30, 60])
         self.mVolts = np.array([0, 1])
         # Interpolating
         self.range_volt = np.interp(self.range_temp, self.temp, self.mVolts)
         self.temp_volt = np.stack((self.range_temp, self.range_volt))
     def ramp(self, start_temp, target_temp):
         self.start_temp = start_temp
         self.target_temp = target_temp

         self.nearest_temp_start = find_nearest(self.temp_volt[0], start_temp)
         self.nearest_temp_target = find_nearest(self.temp_volt[0], target_temp)

         self.volt_ref_start = self.temp_volt[1, self.nearest_temp_start]
         self.volt_ref_target = self.temp_volt[1, self.nearest_temp_target]

         if start_temp > target_temp:
             self.data = np.arange(self.volt_ref_start, self.volt_ref_target, - self.volt_ref_target/1000)

         elif target_temp > start_temp:
            self.data = np.arange(self.volt_ref_start, self.volt_ref_target, self.volt_ref_target/1000)


     def constant(self, target_temp, length):
         self.target_temp = target_temp
         self.nearest_temp = find_nearest(self.temp_volt[0], target_temp)
         self.volt_ref = self.temp_volt[1, self.nearest_temp]

         self.data = np.repeat(self.volt_ref, length)

     def oscillation(self, lower_bound, upper_bound, freq, phase = 0, repeats = 1, rate = globals.rate_NI):

        self.nearest_temp_low = find_nearest(self.temp_volt[0], lower_bound)
        self.nearest_temp_upper = find_nearest(self.temp_volt[0], upper_bound)

        self.volt_ref_low = self.temp_volt[1, self.nearest_temp_low]
        self.volt_ref_upper = self.temp_volt[1, self.nearest_temp_upper]


        self.t = np.arange(0, repeats * 10, 0.01)
        self.w = 2 * math.pi * freq
        self.phi = phase # phase to change the phase of sine function

        self.A = (self.volt_ref_upper - self.volt_ref_low)/2
        self.data = self.A * np.sin(self.w * self.t + self.phi) + (self.volt_ref_upper + self.volt_ref_low)/2

        self.duration = int(1000 * repeats/rate) # duration of sound

     def run(self, rate = globals.rate_NI):

        # print('we are here')
        self.tosk = NT.Task()
        self.tosk.ao_channels.add_ao_voltage_chan('/{}/{}'.format(globals.dev, globals.nqO))
        self.tosk.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len(self.data), sample_mode = NC.AcquisitionType.FINITE) # samps_per_chan = 1000

        globals.status = 'active'
        # print('laser almost on')
        time.sleep(1)
        self.tosk.write(self.data)
        self.tosk.start()
        # print('laser on')
        self.tosk.wait_until_done(timeout = 50)
        self.tosk.close()
        # print('laser killed')
        # globals.status = 'inactive'

     def runTGIfam(self, rate = globals.rate_NI):
        while True:
            if globals.fam == 'tgi':

                self.tosk = NT.Task()
                self.tosk.ao_channels.add_ao_voltage_chan('/{}/{}'.format(globals.dev, globals.nqO))
                self.tosk.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len(self.data), sample_mode = NC.AcquisitionType.FINITE) # samps_per_chan = 1000

                self.tosk.write(self.data)
                self.tosk.start()
                self.tosk.wait_until_done(timeout = 50)
                self.tosk.close()

                input('Press to close the shutter')

                globals.status = 'inactive'

                input('Press to stop noise and laser the shutter')

                winsound.PlaySound(None, winsound.SND_PURGE)
                globals.trial == 'off'

                break
            else:
                continue


     def threshold(self):
        start = time.time()
        while True:  #making a loop
            try:
                if keyboard.is_pressed(' '):
                    # print('space pressed')
                    globals.status = 'inactive'
                    end = time.time()
                    self.threshold = end - start

                    winsound.PlaySound(None, winsound.SND_PURGE)
                    globals.trials = 'off'
                    globals.shutter = 'close'

                    globals.thres = 1

                    print(self.threshold)

                    break #finishing the loop
            except:
                pass

        # print('thres killed')


class screening(object):
    def __init__(self):

        pass

    def instructions(self, message):
        self.win = Tk()

        self.win.attributes('-fullscreen', True)
        label = Label(self.win, text="{}".format(message), bg = 'black', fg = 'white', font = "none 50 bold", anchor=CENTER)

        label.grid(column=0, row=0)

        self.win.configure(background = 'black')
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(0, weight=1)

        self.win.bind('<Return>', lambda e: self.win.destroy())
        self.win.mainloop()

    def instructionsTime(self, message, seconds):
        self.win = Tk()

        self.win.attributes('-fullscreen', True)
        label = Label(self.win, text="{}".format(message), bg = 'black', fg = 'white',
            font = "none 50 bold", anchor=CENTER)

        label.grid(column=0, row=0)

        self.win.configure(background = 'black')
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(0, weight=1)

        self.win.after(int(seconds * 1000), lambda: self.win.destroy()) # Destroy the widget after 30 seconds

        self.win.mainloop()

    def handTGI(self, n_subject):
        self.win = Tk()

        ### Getting image
        self.img = Image.open('./hands/subj_{}.jpg'.format(n_subject))
        self.basewidth = 500
        self.wpercent = (self.basewidth/float(self.img.size[0]))
        self.hsize = int((float(self.img.size[1])*float(self.wpercent)))
        self.image = self.img.resize((self.basewidth, self.hsize), Image.ANTIALIAS)
        # self.image.save('./hands/test.jpg')

        ### Configuration of the frame
        self.win.geometry('{}x{}'.format(self.basewidth, self.hsize))

        #setting up a tkinter canvas
        self.frame = Frame(self.win, bd=2, relief=SUNKEN)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)


        self.canvas = Canvas(self.frame, bd=0)
        self.canvas.grid(row=0, column=0, sticky=N+S+E+W)

        self.frame.pack(fill=BOTH,expand=1)

        #adding the image
        self.image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0,0,image = self.image,anchor="nw")
        self.canvas.config(scrollregion = self.canvas.bbox(ALL))

        #function to be called when mouse is clicked
        def getcoords(event):
            #outputting x and y coords to console
            self.xCOOR = event.x
            self.yCOOR = event.y

            self.win.destroy()

        #mouseclick event
        self.canvas.bind("<Button 1>", getcoords)

        self.win.mainloop()

    def PayAttention(self, message):
        self.win = Tk()

        time.sleep(0.0001)
        # winsound.PlaySound('beep.wav', winsound.SND_ASYNC)

        self.win.attributes('-fullscreen', True)
        label = Label(self.win, text="{}".format(message), bg = 'black', fg = 'white',
            font = "none 50 bold", anchor=CENTER)

        label.grid(column=0, row=0)

        self.win.configure(background = 'black')
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(0, weight=1)

        self.win.bind('<space>', lambda event: self.win.destroy())

        self.win.mainloop()

    def Scores(self, score1, score2):

        self.win = Tk()
        message1 = 'Your score was {} out of 10 and {} out of 10'.format(score1, score2)

        self.win.attributes('-fullscreen', True)
        label = Label(self.win, text="{}".format(message1), bg = 'black', fg = 'white',
            font = "none 30 bold", anchor=CENTER)
        label2 = Label(self.win, text="{}".format('\n\n\n Click and press enter to continue'), bg = 'black', fg = 'white',
            font = "none 20 bold", anchor=CENTER)

        label.grid(column=0, row=0)
        label2.grid(column=1, row=0)

        self.win.configure(background = 'black')
        self.win.columnconfigure(0)
        self.win.rowconfigure(0, weight=1)

        self.win.bind('<Return>', lambda e: self.win.destroy())
        self.win.mainloop()

    def FinalScore(self, score):

        self.win = Tk()
        message = '                                       Your had {} % correct responses'.format(score)

        self.win.attributes('-fullscreen', True)
        label = Label(self.win, text="{}".format(message), bg = 'black', fg = 'white',
            font = "none 30 bold", anchor=CENTER)
        label2 = Label(self.win, text="{}".format('\n\n\n Click and press enter to continue'), bg = 'black', fg = 'white',
            font = "none 20 bold", anchor=CENTER)

        label.grid(column=0, row=0)
        label2.grid(column=1, row=0)

        self.win.configure(background = 'black')
        self.win.columnconfigure(0)
        self.win.rowconfigure(0, weight=1)

        self.win.bind('<Return>', lambda e: self.win.destroy())
        self.win.mainloop()


def find_nearest(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx


    # def subjHandIn(self, library):
    #     pass
