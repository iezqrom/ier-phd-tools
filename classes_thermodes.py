#!/usr/bin/env python3

# System
from datetime import datetime
import threading
import time
from multiprocessing import pool
from multiprocessing.pool import ThreadPool
import warnings
import itertools
import sys
import curses
import csv

from tkinter import *
from tkinter import filedialog as tkfd


# Maths
import matplotlib.pyplot as plt
import numpy as np
import math
import random
import scipy as sci
from scipy import stats
import sklearn as skl
import scipy.stats as st

import statsmodels as sm

# import matplotlib
from numpy import (isscalar, r_, log, around, unique, asarray,
                   zeros, arange, sort, amin, amax, any, atleast_1d,
                   sqrt, ceil, floor, array, compress,
                   pi, exp, ravel, count_nonzero, sin, cos, arctan2, hypot)
import pandas as pd


import matlab.engine as me

    # print('No module Matlab')
## NIDAQMX
import nidaqmx.system.watchdog as nsw
import nidaqmx.stream_writers as nsw
import nidaqmx.stream_readers as nsr
import nidaqmx._task_modules.out_stream as nto
import nidaqmx._task_modules.timing as ntt
import nidaqmx.constants as NC
import nidaqmx.task as NT

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

# This class is to use a single thermode, useful for simple scripts
class Thermode(object):
    steps_range = 0.1

    # We first initialise the object by mapping temperatures onto the voltages given by the manual of the thermodes.
    # This manual can be found in office 207a as of December 2019
    def __init__(self, lower = 17, upper = 51):
        ## We need to map the temperatures with the Voltages ##
        self.range_temp = np.arange(lower, upper, self.steps_range)
        self.range_temp = self.range_temp.round(decimals=1)

        self.temp = np.arange(0, 51, 5) # From manual

        self.mVolts = np.array([-62.2, -12.9, 35.9, 85, 134.6, 182.2, 234.2, 286, 338.2, 389.3, 440.9]) # Analog Output mV AOP
        self.volts = np.divide(self.mVolts,1000) # conversion from mV to V
        self.volts = self.volts.round(decimals=4)

        # Interpolating
        self.range_volt = np.interp(self.range_temp, self.temp, self.volts)

        # We stack the data
        self.temp_volt = np.stack((self.range_temp, self.range_volt))
        # self.temp_volt = self.temp_volt.T


    ## This method creates a ramp to reach temperature X from temperature Y ##
    def ramp(self, start_temp, target_temp):
         self.start_temp = start_temp
         self.target_temp = target_temp

         self.nearest_temp_start = find_nearest(self.temp_volt[0], start_temp)
         self.nearest_temp_target = find_nearest(self.temp_volt[0], target_temp)

         self.indx_start = np.where(self.temp_volt[0] == self.nearest_temp_start)
         self.indx_target = np.where(self.temp_volt[0] == self.nearest_temp_target)

         self.volt_ref_start = self.temp_volt[1,  self.indx_start]
         self.volt_ref_target = self.temp_volt[1, self.indx_target]

         # print(self.volt_ref_start)

         if start_temp > target_temp:
             self.volt = np.arange(self.volt_ref_start, self.volt_ref_target, - self.volt_ref_target/1000)

         elif target_temp > start_temp:
            self.volt = np.arange(self.volt_ref_start, self.volt_ref_target, self.volt_ref_target/1000)

    ## This is the most IMPORTANT method it is the way you write data to the box (e.g. a ramp)
    ## to the NI DAQ box and read from the boxes

    def IO_thermode(self, Ai, Ao, rate = globals.rate_NI, dev = globals.dev):

        self.ai_task = NT.Task()
        self.ai_task.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(dev, Ai))
        self.ai_task.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len(self.volt), sample_mode= NC.AcquisitionType.FINITE)

        # configuring ao task: writing data

        self.ao_task = NT.Task()
        self.ao_task.ao_channels.add_ao_voltage_chan('/{}/{}'.format(dev, Ao))
        self.ao_task.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len(self.volt), sample_mode = NC.AcquisitionType.FINITE,
        source = 'ai/SampleClock') # samps_per_chan = 1000

        self.start_TT = datetime.now()

        # print('VOLTAGE: ' + str(self.volt))
        # counter = 0
        while True:
            try:
                # counter += 1
                self.ao_task.write(self.volt)
            except:
                print('We are trying')
                continue
            else:
                break
             # run the task
        self.ao_task.start()
        self.ai_task.start()

        self.ao_task.wait_until_done(timeout = 50)
        self.ai_task.wait_until_done(timeout = 50)

        self.data = self.ai_task.read(number_of_samples_per_channel = len(self.volt))

        self.ai_task.close()
        self.ao_task.close()

        self.end_TT = datetime.now() - self.start_TT
        self.rate = rate
        # print('Counter:  ' + str(counter))

    ##### This method is in working progress. The aim is to develop a matching paradigm ####
    def adjust_single(self, rate, Ia, Io, start_temp, target_temp):

        self.ramp(start_temp, target_temp)

        self.IO_thermode(rate, Ia, Io)

        stdscr = curses.initscr()
        stdscr.keypad(1)

        stdscr.addstr(0,0,"\n Use arrows up and down to adjust the temperature of the thermode")
        stdscr.refresh()

        key = ''
        while True:

            key = stdscr.getch()

            stdscr.refresh()

            if key == curses.KEY_UP:
                self.volt = self.data + 0.0000992
                self.IO_thermode(rate, Ia, Io)

            elif key == curses.KEY_DOWN:
                self.volt = self.data + 0.0000992
                self.IO_thermode(rate, Ia, Io)

            elif key == ord('q'):
                break

# This class is to use multiple thermodes, useful for simple scripts
class gethermodes(object):
    def __init__(self, thermodes = 'all'):
        # This class is to run the thermodes, __init__ starts a global task and set thermode array
        self.tisk = NT.Task()
        self.tosk = NT.Task()
        self.nameTisk = self.tisk.name
        self.nameTosk = self.tosk.name

        if thermodes == 'all':
            self.array_thermodes = [('ai28', 'ao3'), ('ai24', 'ao2'), ('ai8', 'ao0')]
            self.n_channels = 3
        elif thermodes == ('1', '2'):
            self.array_thermodes = [('ai28', 'ao3'), ('ai24', 'ao2')]
            self.n_channels = 2
        elif thermodes == ('1', '3'):
            self.array_thermodes = [('ai28', 'ao3'), ('ai8', 'ao0')]
            self.n_channels = 2
        elif thermodes == ('2', '3'):
            self.array_thermodes = [('ai24', 'ao2'), ('ai8', 'ao0')]
            self.n_channels = 2

    def InputChannels(self, data, dev = globals.dev, rate = globals.rate_NI):

        if self.n_channels != 2 and self.n_channels != 3:
            print('Wrong number of channels')
        elif self.n_channels == 2:
            self.tisk.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[0][0]))
            self.tisk.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[1][0]))
        elif self.n_channels == 3:
            self.tisk.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[0][0]))
            self.tisk.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[1][0]))
            self.tisk.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[2][0]))

        self.tisk.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len(data), sample_mode = NC.AcquisitionType.FINITE)

    def OutputChannels(self, data, dev = globals.dev, rate = globals.rate_NI):

        if self.n_channels != 2 and self.n_channels != 3:
            print('Wrong number of channels')
        elif self.n_channels == 2:
            self.tosk.ao_channels.add_ao_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[0][1]))
            self.tosk.ao_channels.add_ao_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[1][1]))
        elif self.n_channels == 3:
            self.tosk.ao_channels.add_ao_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[0][1]))
            self.tosk.ao_channels.add_ao_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[1][1]))
            self.tosk.ao_channels.add_ao_voltage_chan(physical_channel = '/{}/{}'.format(dev, self.array_thermodes[2][1]))

        self.tosk.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len(data), sample_mode = NC.AcquisitionType.FINITE,
        source = 'ai/SampleClock')

    def run(self, data):
        self.stacked = np.stack(data)

        globals.total += 1

        start = time.time()



        self.tosk.write(self.stacked)

        self.tosk.start()
        self.tisk.start()

        self.tosk.wait_until_done(timeout = 50)
        self.tisk.wait_until_done(timeout = 50)

        self.data = self.tisk.read(number_of_samples_per_channel = len(data[0]))

        # print('Run' + str(self.nameTosk))

        end = time.time()
        # print('{}'.format(end - start))

        time.sleep(0.05)
        self.tosk.close()
        self.tisk.close()
        winsound.PlaySound(None, winsound.SND_PURGE)
        globals.total -= 1

    def PlotScreen(self, repeats):
        self.duration = int(1000*1/globals.rate_NI)
        self.duration = self.duration * repeats
        self.time = np.arange(0, self.duration, self.duration/(1000*repeats))

        fig, axes = plt.subplots(1, self.n_channels)
        # print('Len time:  ' + str(len(self.time)))
        # print('Len data:  ' + str(len(self.data[0])))
        counter = 0
        for ax in axes:
            ax.plot(self.time, self.data[counter], label = 'Voltage from Thermode')
            ax.plot(self.time, self.stacked[counter], label = 'Signal sent to Thermode')
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.set_title('Thermode {}'.format(counter + 1))
            ax.set_xlabel('Seconds')
            ax.set_ylabel('Voltage')
            counter += 1

        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc = 'best')

        plt.show()

class oscillation(thermode, gethermodes):

    def __init__(self, lower, upper, thermodes = 'all'):
        thermode.__init__(self, lower = lower, upper = upper)
        gethermodes.__init__(self, thermodes = 'all')

    def sineWave(self, freq, phase = 0, repeats = 1):

        ## Sine wave
        self.t = np.arange(0, repeats * 10, 0.01)
        self.w = 2 * math.pi * freq
        self.phi = phase # phase to change the phase of sine function

        self.A = (max(self.range_volt) - min(self.range_volt))/2
        self.volt = self.A * np.sin(self.w * self.t + self.phi) + (max(self.range_volt) + min(self.range_volt))/2

        # self.volt = np.tile(self.volt, repeats)
        self.duration = int(1000 * repeats/globals.rate_NI) # duration of sound

    def IO_osc(self, IaT, OaT, rate = globals.rate_NI):

        self.start_osc = datetime.now()

        #print('Length:  ' + str(len(self.volt_long)))

        # for i in range(0, len(self.volt_long), 2):
        #     # print('We are here')
        #
        #     self.volt = self.volt_long[i:i + 2]
        #     print(self.volt)
        thermode.IO_thermode(self, rate, IaT, OaT)

        self.data_osc = self.data

        self.end_osc = datetime.now() - self.start_osc
        # print(self.end_osc)


    def plotSingleSine(self, name_save = None, path_save = None, save = 'Y'):
        self.durationSine = int(1000*1/globals.rate_NI) # duration of sound
        fig, ax = plt.subplots(1,1)
        self.timePlotSine = np.arange(0, self.durationSine, self.durationSine/1000)
        plt.plot(self.timePlotSine, self.data_osc, label = 'Voltage from Thermode')
        plt.plot(self.timePlotSine, self.volt, 'r', label = 'Wave create for Thermode')

        ax.legend()
        plt.ylabel('Voltage')
        plt.xlabel('Seconds')

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.show()

        if save in 'Y':
            fig.savefig('./{}/{}.svg'.format(path_save, name_save))
            plt.close()


class constant(thermode, gethermodes):
    def __init__(self, cons_temp, repeats, length, thermodes = 'all'):
        thermode.__init__(self, lower = 17, upper = 51)
        gethermodes.__init__(self, thermodes = 'all')
        self.cons_temp = cons_temp

        # super().__init__(range_temp, temp, mVolts, volts, range_volt)

        # Stacking array
        self.temp_volt = np.stack((self.range_temp, self.range_volt))
        self.temp_volt = self.temp_volt.T

        # Finding voltage for corresponding text temp
        self.nearest_temp = find_nearest(self.temp_volt[:, 0], cons_temp)
        self.volt_ref = self.temp_volt[np.where(self.temp_volt[:,0] == self.nearest_temp)]
        self.volt_ref = self.volt_ref[0, 1]
        self.volt = np.repeat(self.volt_ref, length)
        # print(len(self.volt))
        self.durationCons = int(1000 * repeats/globals.rate_NI) # duration of sound
        self.repeats = repeats

    def IO_constant(self, IaT, OaT, rate = globals.rate_NI):

        thermode.IO_thermode(self, rate, IaT, OaT)
        self.data_cons = self.data

    def plotSingleCons(self):

        fig, ax = plt.subplots(1,1)
        self.timePlotCons = np.arange(0, self.durationCons, self.durationCons / (self.repeats * 1000))

        plt.plot(self.timePlotCons, self.data_cons, label = 'Voltage from Thermode')
        plt.plot(self.timePlotCons, self.volt, 'r', label = 'Wave create for Thermode')

        ax.legend()
        plt.ylabel('Voltage')
        plt.xlabel('Seconds')

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        plt.show()

    def IO_constantTrioText(self, data):

        self.start_ref = datetime.now()
        self.data_target = []

        while True:

            trio = gethermodes()
            trio.InputChannels(self.volt)
            trio.OutputChannels(self.volt)
            trio.run(data)

            if globals.text_state == 1:
                break
            else:
                continue

class target(thermode, gethermodes):
    steps_range = 0.004
    def __init__(self, reach_temp, thermodes = 'all', lower = 17, upper = 51):
        thermode.__init__(self, lower = 17, upper = 51)
        gethermodes.__init__(self, thermodes = 'all')

        # super().__init__(range_temp, temp, mVolts, volts, range_volt)

        # Stacking array
        self.temp_volt = np.stack((self.range_temp, self.range_volt))
        self.temp_volt = self.temp_volt.T

        # Finding voltage for corresponding text temp
        self.nearest_temp = find_nearest(self.temp_volt[:, 0], reach_temp)
        self.volt_ref = self.temp_volt[np.where(self.temp_volt[:,0] == self.nearest_temp)]
        self.volt_ref = self.volt_ref[0, 1]
        self.volt = np.repeat(self.volt_ref, 2)

    def IO_referenceSingle(self, IaT, OaT, ref_dummy = 0.01, rate = globals.rate_NI):
        self.start_ref = datetime.now()
        self.data_target = []

        while True:

            thermode.IO_thermode(self, rate, IaT, OaT)

            if np.mean(self.data) > (np.mean(self.volt) - ref_dummy) and np.mean(self.data) < (np.mean(self.volt) + ref_dummy):
                self.while_ref = datetime.now() - self.start_ref
                self.data_target = np.asarray(list(itertools.chain(*self.data_target)))
                break
            else:
                print("\n Reaching reference temperature...")
                self.volt = np.repeat(self.volt_ref, 2)
                self.data_target.append(self.data)
                continue

    def IO_referenceTrio(self, ref_dummy = 0.01, rate = globals.rate_NI):
        self.start_ref = datetime.now()
        self.data_target = []

        while True:
            trio = gethermodes()
            trio.InputChannels(self.volt)
            trio.OutputChannels(self.volt)
            trio.run((self.volt, self.volt, self.volt))

            mean_trio = np.mean(trio.data, axis = 1)

            if all(i > (np.mean(self.volt) - ref_dummy) for i in mean_trio) and all(i < (np.mean(self.volt) + ref_dummy) for i in mean_trio):
                self.while_ref = datetime.now() - self.start_ref
                self.data_target = np.asarray(list(itertools.chain(*self.data_target)))
                # trio.tisk.close()
                # trio.tosk.close()
                break
            else:
                print("\n Reaching reference temperature...")
                self.volt = np.repeat(self.volt_ref, 2)
                self.data_target.append(trio.data)
                # trio.tisk.close()
                # trio.tosk.close()
                continue


    def plotSingleReference(self, name_save = None, path_save = None, save = 'Y'):
        fig, ax = plt.subplots(1,1)
        self.time_target = np.arange(0, len(self.data_target))
        print(np.asarray(self.data_target))
        test = np.asarray(self.data_target)
        print(test.shape)


        plt.plot(self.time_target, self.data_target, label = 'Voltage from Thermode')

        ax.legend()
        plt.ylabel('Voltage')
        plt.xlabel('Seconds')

        plt.text(1, np.mean(self.data_target), str(self.end_TT) + 's')
        # print(self.volt)
        plt.text(2, np.mean(self.data_target) + 0.009, str(self.volt[0]) + 'Voltage')

        if save in 'Y':
            fig.savefig('./{}/{}.png'.format(path_save, name_save))

        plt.close()

    def IO_targetTrio(self, data, ref_dummy = 0.01, rate = globals.rate_NI):
        self.start_ref = datetime.now()
        self.data_target = [] # hola

        while True:

            trioT = gethermodes()
            trioT.InputChannels(self.volt)
            trioT.OutputChannels(self.volt)
            trioT.run(data)

            mean_trioT = np.mean(trioT.data, axis = 1)

            if data[0][0] > (mean_trioT[0] - ref_dummy) and data[0][0] < (mean_trioT[0] + ref_dummy) and data[1][0] > (mean_trioT[1] - ref_dummy) and data[1][0] < (mean_trioT[1] + ref_dummy) and data[2][0] > (mean_trioT[2] - ref_dummy) and data[2][0] < (mean_trioT[2] + ref_dummy):

                self.while_ref = datetime.now() - self.start_ref
                self.data_target = np.asarray(list(itertools.chain(*self.data_target)))
                # trioT.tosk.close()
                # trioT.tisk.close()
                # print('We are done')
                break
            else:
                print("\n Reaching starting temperature...")
                self.volt = np.repeat(self.volt_ref, 2)
                self.data_target.append(trioT.data)
                # trioT.tosk.close()
                # trioT.tisk.close()
                # print('we are here')
                continue


def audio_trig(duration, fs = 500, volume = 0.9, f = 4400):
    duration = duration * 1000
    while globals.total == 0:
        time.sleep(1)
        # print('\n waiting \n')
        #print(globals.total)
    else:
        if globals.total == 1:
            try:
                # print('sound')
                winsound.Beep(fs, duration)
            except:
                print("Stimulus")
                audio.audio(duration, fs, volume, f)

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
