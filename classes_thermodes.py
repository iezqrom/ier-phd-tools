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

try:
    import matlab.engine as me
except:
    pass
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
import globals

class thermode(object):
    steps_range = 0.1
    def __init__(self, lower = 17, upper = 51):
        ## We need to map the temperatures with the Voltages ##
        self.range_temp = np.arange(lower, upper, self.steps_range)
        self.temp = np.arange(0, 51, 5) # From manual
        self.mVolts = np.array([-62.2, -12.9, 35.9, 85, 134.6, 182.2, 234.2, 286, 338.2, 389.3, 440.9]) # Analog Output mV AOP
        self.volts = np.divide(self.mVolts,1000) # conversion from mV to V
        # Interpolating
        self.range_volt = np.interp(self.range_temp, self.temp, self.volts)

        # We stack the data
        self.temp_volt = np.stack((self.range_temp, self.range_volt))

    ## This method creates a ramp to reach temperature X from temperature Y ##
    def ramp(self, start_temp, target_temp):
         self.start_temp = start_temp
         self.target_temp = target_temp

         self.nearest_temp_start = find_nearest(self.temp_volt[0], start_temp)
         self.nearest_temp_target = find_nearest(self.temp_volt[0], target_temp)

         self.volt_ref_start = self.temp_volt[1, self.nearest_temp_start]
         self.volt_ref_target = self.temp_volt[1, self.nearest_temp_target]

         if start_temp > target_temp:
             self.volt = np.arange(self.volt_ref_start, self.volt_ref_target, - self.volt_ref_target/1000)

         elif target_temp > start_temp:
            self.volt = np.arange(self.volt_ref_start, self.volt_ref_target, self.volt_ref_target/1000)

    ## This is the most IMPORTANT method it is the way you write data to the box (e.g. a ramp)
    ## to the NI DAQ box and read from the boxes

    def IO_thermode(self, rate, Ia, Io, dev = globals.dev):

        self.ai_task = NT.Task()
        self.ai_task.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(dev, Ia))
        self.ai_task.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len(self.volt), sample_mode= NC.AcquisitionType.FINITE)

        # configuring ao task: writing data

        self.ao_task = NT.Task()
        self.ao_task.ao_channels.add_ao_voltage_chan('/{}/{}'.format(dev, Io))
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


class AttentionScreen:

    def __init__(self, message, data, repeats):

        self.win = Tk()
        # self.win.title("Python GUI")

        time.sleep(0.0001)

        self.win.attributes('-fullscreen', True)
        label = Label(self.win, text="{}".format(message), bg = 'black', fg = 'white',
            font = "none 50 bold", anchor=CENTER)

        buttonT = Button(self.win, text=' ', bg = 'black', width = 1, command = self.thermode_screen(data),
            anchor=CENTER, highlightthickness = 0.01, borderwidth = 0.01)

        self.win.after(repeats * 10000, lambda: self.win.destroy())

        buttonT.grid(column = 1, row = 0)
        # buttonD.grid(column = 2, row = 0)
        label.grid(column=0, row=0)

        self.win.configure(background = 'black')
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(0, weight=1)

        # self.win.bind('<space>', lambda e: self.win.destroy())

        self.win.mainloop()


    def thermode_screen(self, data):

        thermodS = gethermodes()

        thermodS.InputChannels(data[0])
        thermodS.OutputChannels(data[1])

        therm_screen = threading.Thread(target = thermodS.run, args = [data])

        winsound.PlaySound('beep.wav', winsound.SND_ASYNC)
        therm_screen.start()


class InputScreen:

    def __init__(self, message, data):

        self.win = Tk()

        self.win.attributes('-fullscreen', True)

        def testVal(ans, acttyp):

            if acttyp == '1': #insert
                if ans != 'y' and ans != 'n':
                    return False
            return True


        label = Label(self.win, text="{}".format(message), bg = 'black', fg = 'white',
            font = "none 30 bold", anchor = CENTER)

        label2 = Label(self.win, text="{}".format('\n\n Click on the box, type your answer \n and press enter'), bg = 'black', fg = 'white',
            font = "none 15 bold", anchor = CENTER)


        entry = Entry(self.win, validate = "key")
        entry['validatecommand'] = (entry.register(testVal),'%P','%d')


        label.grid(column = 0, row = 0)
        entry.grid(column = 1, row = 0)
        label2.grid(column = 2, row = 0)

        self.win.configure(background = 'black')
        self.win.columnconfigure(0)
        self.win.rowconfigure(0, weight=1)

        def enterEndTherm(event):

            globals.text_state += 1
            self.input = entry.get()
            self.win.destroy()

        self.win.bind('<Return>', enterEndTherm)
        self.win.mainloop()


    def thermode_screen(self, data):

        while True:

            trio = gethermodes()
            trio.InputChannels(data[0])
            trio.OutputChannels(data[1])

            therm_trio = threading.Thread(target = trio.run, args = [data])
            print('we almost started this')
            therm_trio.start()

            if globals.text_state == 1:
                break
            else:
                continue


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

    # def IO_cons(self, IaT, OaT, time, cons_dummy = 0.001, rate = globals.rate_NI):
    #     self.start_cons = datetime.now()
    #     self.elapsed_cons = 0
    #     self.data_target = []
    #
    #     while self.elapsed_cons < time:
    #
    #         thermode.IO_thermode(self, rate, IaT, OaT)
    #
    #         self.elapsed_cons = datetime.now() - self.start_cons
    #         self.elapsed_cons = self.elapsed_cons.seconds
    #
    #         print("\n Maintaining temperature at {}...".format(self.cons_temp))
    #         self.volt = np.repeat(self.volt_ref, 2)
    #         self.data_target.append(self.data)
    #         print(self.elapsed_cons)
    #
    #
    #     self.data_target = np.asarray(list(itertools.chain(*self.data_target)))

    # def IO_constantTrio(self, data, ref_dummy = 0.01, rate = globals.rate_NI):
    #     self.start_ref = datetime.now()
    #     self.data_target = []
    #
    #     while True:
    #
    #         trio = gethermodes()
    #         trio.InputChannels(self.volt)
    #         trio.OutputChannels(self.volt)
    #         trio.run(data)
    #
    #         if np.mean(self.data) > (np.mean(self.volt) - ref_dummy) and np.mean(self.data) < (np.mean(self.volt) + ref_dummy):
    #             self.while_ref = datetime.now() - self.start_ref
    #             self.data_target = np.asarray(list(itertools.chain(*self.data_target)))
    #             break
    #         else:
    #             self.volt = np.repeat(self.volt_ref, 2)
    #             self.data_target.append(self.data)
    #             continue


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

        # print('We are completely done')



class ploTTT:

    def __init__(self, file, subject):
        self.RawData = pd.read_csv(file)
        # print(len(self.RawData))
        self.RawData = self.RawData.dropna()
        self.Nsample = str(len(self.RawData['correct']))

        if subject == 'all':
            self.subject = subject
            pass
        else:
            self.RawData = self.RawData.loc[self.RawData['n_subject'] == subject]
            self.subject = str(subject)

    def exclude(self, who_out):
        for i in who_out:
            # print(i)
            self.RawData = self.RawData[self.RawData.n_subject != i]

        self.who_out = who_out

    def correctTGO(self):
        self.iso_phase = self.RawData.loc[self.RawData['phase'] == 0]
        self.aniso_phase = self.RawData.loc[self.RawData['phase'] > 3]

        self.iso_grade = pd.value_counts(self.iso_phase['grade'].values, sort=False)
        self.iso_trials = len(self.iso_phase)
        self.iso_correct = self.iso_grade[1]/self.iso_trials

        self.aniso_grade = pd.value_counts(self.aniso_phase['grade'].values, sort=False)
        self.aniso_trials = len(self.aniso_phase)
        self.aniso_correct = self.aniso_grade[1]/self.aniso_trials

        self.perCorrect = np.array([self.iso_correct, self.aniso_correct])*100

        if self.subject == 'all':
            self.participants = self.RawData['n_subject'].unique()
            self.perPartIso = []
            self.perPartAniso = []

            for i in self.participants:

                self.RawPart = self.RawData.loc[self.RawData['n_subject'] == i]

                self.iso_phasePart = self.RawPart.loc[self.RawPart['phase'] == 0]
                self.aniso_phasePart = self.RawPart.loc[self.RawPart['phase'] > 3]

                self.iso_gradePart = pd.value_counts(self.iso_phasePart['grade'].values, sort=False)
                self.iso_trialsPart = len(self.iso_phasePart)
                self.iso_correctPart = self.iso_gradePart[1]/self.iso_trialsPart

                self.aniso_gradePart = pd.value_counts(self.aniso_phasePart['grade'].values, sort=False)
                self.aniso_trialsPart = len(self.aniso_phasePart)
                self.aniso_correctPart = self.aniso_gradePart[1]/self.aniso_trialsPart

                self.perPartIso.append(self.iso_correctPart * 100)
                self.perPartAniso.append(self.aniso_correctPart * 100)


    def correctRate(self):
        # Subcharts of rates

        self.rate_100 = self.RawData.loc[self.RawData['freq'] == 0.100]
        self.rate_133 = self.RawData.loc[self.RawData['freq'] == 0.133]
        self.rate_166 = self.RawData.loc[self.RawData['freq'] == 0.166]
        self.rate_200 = self.RawData.loc[self.RawData['freq'] == 0.200]
        self.rate_233 = self.RawData.loc[self.RawData['freq'] == 0.233]
        self.rate_266 = self.RawData.loc[self.RawData['freq'] == 0.266]
        self.rate_300 = self.RawData.loc[self.RawData['freq'] == 0.300]
        self.rate_333 = self.RawData.loc[self.RawData['freq'] == 0.33299999999999996]

        self.up_phase = self.RawData.loc[self.RawData['phase'] == 0]
        self.down_phase = self.RawData.loc[self.RawData['phase'] != 0]

        # Repeats of each rate

        self.n_rate = pd.value_counts(self.RawData['freq'].values, sort=True)
        self.rate_100_n = pd.value_counts(self.rate_100['grade'].values, sort=False)
        self.rate_133_n = pd.value_counts(self.rate_133['grade'].values, sort=False)
        self.rate_166_n = pd.value_counts(self.rate_166['grade'].values, sort=False)
        self.rate_200_n = pd.value_counts(self.rate_200['grade'].values, sort=False)
        self.rate_233_n = pd.value_counts(self.rate_233['grade'].values, sort=False)
        self.rate_266_n = pd.value_counts(self.rate_266['grade'].values, sort=False)
        self.rate_300_n = pd.value_counts(self.rate_300['grade'].values, sort=False)
        self.rate_333_n = pd.value_counts(self.rate_333['grade'].values, sort=False)

        self.s = [self.rate_100_n[1], self.rate_133_n[1], self.rate_166_n[1], self.rate_200_n[1], self.rate_233_n[1], self.rate_266_n[1], self.rate_300_n[1], self.rate_333_n[1]]
        self.sf = [float(i) for i in self.s]

        try:
            self.correct_100 = self.rate_100_n[1]/self.n_rate[0.100]
        except:
            self.correct_100 = 0

        try:
            self.correct_133 = self.rate_133_n[1]/self.n_rate[0.133]
        except:
            self.correct_133 = 0

        try:
            self.correct_166 = self.rate_166_n[1]/self.n_rate[0.166]
        except:
            self.correct_166 = 3

        try:
            self.correct_200 = self.rate_200_n[1]/self.n_rate[0.200]
        except:
            self.correct_200 = 0

        try:
            self.correct_233 = self.rate_233_n[1]/self.n_rate[0.233]
        except:
            self.correct_233 = 0

        try:
            self.correct_266 = self.rate_266_n[1]/self.n_rate[0.266]
        except:
            self.correct_266 = 0

        try:
            self.correct_300 = self.rate_300_n[1]/self.n_rate[0.300]
        except:
            self.correct_300 = 0

        try:
            self.correct_333 = self.rate_333_n[1]/self.n_rate[0.33299999999999996]
        except:
            self.correct_333 = 0


        self.perCorrect = np.array([self.correct_100, self.correct_133, self.correct_166, self.correct_200, self.correct_233, self.correct_266, self.correct_300, self.correct_333])*100
        try:
            self.total_perc = self.RawData['grade'].value_counts()[1]/(self.RawData['grade'].value_counts()[1] + self.RawData['grade'].value_counts()[0])
        except:
            self.total_perc = 100

        rates = np.array([100, 133, 166, 200, 233, 266, 300, 333])
        self.rates = rates/1000
        self.ratesL = np.ndarray.tolist(self.rates)
        self.ratesLf = [float(i) for i in self.ratesL]


    def propCorrect(self):
        self.RawData['correct'].value_counts().sort_index().plot.bar()

    def propInput(self):
        self.RawData['input'].value_counts().sort_index().plot.bar()

    def propPhase(self):
        self.RawData['phase'].value_counts().sort_index().plot.bar()

    def propUp(self):
        self.up_phase['grade'].value_counts().sort_index().plot.bar()

    def propDown(self):
        self.down_phase['phase'].value_counts().sort_index().plot.bar()

    def propGrade(self):
        self.RawData['grade'].value_counts().plot.bar()

    def propRates(self, folder, temp):
        self.perRates = self.RawData['freq'].value_counts()
        self.perRates.sort_index().plot.bar()
        plt.title('Frequency of frequencies')
        plt.text(1, 3, 'n = ' + self.Nsample)
        plt.text(1, 2.5, temp)
        plt.savefig('./data/{}/figure_analysis/rates_cold_{}_N_{}_{}.svg'.format(folder, temp, self.Nsample, self.subject), transparent=True)

    def TuningCurve(self, folder, temp):

        fig, ax = plt.subplots(1, 1)
        if int(temp.split('_')[0]) < 33:
            plt.plot(self.rates, self.perCorrect, color = 'b')
            plt.xticks(self.rates)
            plt.ylabel('% correct')
            # plt.title('Cold range (28.5-29.5 degrees Celsius)')
            plt.ylim([50, 100])
            plt.xlim([0.1, 0.333])
            plt.xlabel('Hz')
            # plt.text(0.300, 60, 'Total correct: ' + str(self.total_perc))
            # plt.text(0.200, 55, 'n = ' + str(len(self.RawData)))
            plt.hlines(y = 50, xmin = 0.100, xmax = 0.333, linestyles = 'dashed', lw = 0.4)
            plt.hlines(y = 75, xmin = 0.100, xmax = 0.333, linestyles = 'dashed', lw = 0.4)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            plt.savefig('./data/{}/figure_analysis/cold_{}_N_{}_{}.svg'.format(folder, temp, self.Nsample, self.subject), transparent=True)
        else:

            plt.plot(self.rates, self.perCorrect, color = 'r')
            plt.xticks(self.rates)
            plt.ylabel('% correct')
            # plt.title('Warm range (36.5-37.5 degrees Celsius)')
            plt.ylim([50, 100])
            plt.xlim([0.1, 0.333])
            plt.xlabel('Hz')
            # plt.text(0.300, 60, 'Total correct: ' + str(self.total_perc))
            # plt.text(0.200, 55, 'n = ' + str(len((self.RawData))))
            plt.hlines(y = 50, xmin = 0.100, xmax = 0.333, linestyles = 'dashed', lw = 0.4)
            plt.hlines(y = 75, xmin = 0.100, xmax = 0.333, linestyles = 'dashed', lw = 0.4)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            plt.savefig('./data/{}/figure_analysis/hot_{}_N_{}_{}.svg'.format(folder, temp, self.Nsample, self.subject), transparent=True)

    def ThroughoutTime(self, folder, temp = None, save = 'N'):
        if self.subject == 'all':
            self.hits_time = []
            for i in np.arange(max(self.RawData['n_subject'])):
                if i == 4:
                    pass
                else:
                    temp_subset = self.RawData.loc[self.RawData['n_subject'] == i + 1]
                    # print(temp_subset)
                    self.hits_time.append(temp_subset['grade'])
                    self.grade_t = np.mean(np.asarray(self.hits_time), axis = 0)
        else:
            self.grade_t = self.RawData['grade']
            pass

        fig, ax = plt.subplots(1, 1)
        if int(temp.split('_')[0]) < 33:

            plt.plot(np.arange(len(self.grade_t)), self.grade_t, color = 'b')

            plt.yticks(np.arange(0, 1.01, step = 1), ['Miss', 'Hit'])
            plt.ylim([0, 1])
            plt.xlabel('Trials')
            plt.xticks(np.arange(0, 48.01, step = 5))

            plt.vlines(x = 12, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')
            plt.vlines(x = 24, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')
            plt.vlines(x = 36, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')

            plt.xlim([0,48])
            # plt.title('Cold range (28.5-29.5) Hits or Misses across time')
            for i in np.arange(8):
                ax.plot(np.arange(len(self.grade_t)), self.hits_time[i], color = 'k', alpha = 0.1)

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            if save in ('Y'):
                plt.savefig('./data/{}/figure_analysis/cold_across_time_{}_N_{}_{}.svg'.format(folder, temp, self.Nsample, self.subject), transparent=True)

        else:

            plt.plot(np.arange(len(self.grade_t)), self.grade_t, color = 'r')

            plt.yticks(np.arange(0, 1.01, step = 1), ['Miss', 'Hit'])
            plt.xlabel('Trials')
            plt.ylim([0, 1])
            plt.xticks(np.arange(0, 48.01, step = 4))

            plt.vlines(x = 12, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')
            plt.vlines(x = 24, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')
            plt.vlines(x = 36, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')


            plt.xlim([0, 48])
            # plt.title('Warm range (36.5-37.5) Hits or Misses across time')

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            for i in np.arange(8):
                ax.plot(np.arange(len(self.grade_t)), self.hits_time[i], color = 'k', alpha = 0.1)

            if save in ('Y'):
                plt.savefig('./data/{}/figure_analysis/warm_across_time_{}_N_{}_{}.svg'.format(folder, temp, self.Nsample, self.subject), transparent=True)

    def ThroughoutTimeALL(self, temp):
        self.hits_time = []
        fig, ax = plt.subplots(1, 1)
        for i in np.arange(max(self.RawData['n_subject'])):
            temp_subset = self.RawData.loc[self.RawData['n_subject'] == i + 1]
            self.hits_time.append(temp_subset['grade'])
            self.tt = np.mean(np.asarray(self.hits_time), axis = 0)

        if int(temp.split('_')[0]) < 33:
            plt.plot(np.arange(len(self.tt)), self.tt, color = 'b')

            plt.yticks(np.arange(0, 1.01, step = 1), ['Miss', 'Hit'])
            plt.xlabel('Trials')
            plt.title('Cold range (28.5-29.5) Hits or Misses across time')

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            plt.savefig('./data/{}/figure_analysis/cold_across_time_{}_N_{}_{}.svg'.format(folder, temp, self.Nsample, self.subject), transparent=True)

        else:

            plt.plot(np.arange(len(self.tt)), self.tt, color = 'r')

            plt.yticks(np.arange(0, 1.01, step = 1), ['Miss', 'Hit'])
            plt.xlabel('Trials')
            plt.title('Warm range (28.5-29.5) Hits or Misses across time')

            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

            plt.savefig('./data/{}/figure_analysis/warm_across_time_{}_N_{}_{}.svg'.format(folder, temp, self.Nsample, self.subject), transparent=True)

    def ThroughoutTimeTGO(self, folder, title = None, save = 'N'):
        if self.subject == 'all':
            self.hits_time = []

            label_participant = self.RawData['n_subject'].unique()

            for i in label_participant:
                # print(i)
                # for j in self.who_out:
                #     # print(j)
                #     if i + 1 == j:
                #         print('it works')
                #         pass
                #     else:
                temp_subset = self.RawData.loc[self.RawData['n_subject'] == i]
                # print(temp_subset)
                self.hits_time.append(temp_subset['grade'])
                # print(len(self.hits_time))
                self.grade_t = np.mean(np.asarray(self.hits_time), axis = 0)
                # print(self.grade_t)

        else:
            self.grade_t = self.RawData['grade']
            pass

        fig, ax = plt.subplots(1, 1)
        plt.plot(np.arange(len(self.grade_t)), self.grade_t, color = '#4D4B50')

        # plt.xticks(np.arange(0, 46, step = 5))

        plt.vlines(x = 23, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')
        # plt.vlines(x = 24, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')
        # plt.vlines(x = 36, ymin = 0, ymax = 1.01, color = 'k', linestyles = 'dashed')

        plt.xticks(np.arange(0, 46.01, step = 2))

        if self.subject == 'all':
            for i in self.hits_time:
                ax.plot(np.arange(len(self.grade_t)), i, color = 'k', alpha = 0.1)


        plt.yticks(np.arange(0, 1.01, step = 1), ['Miss', 'Hit'])
        plt.ylim([0, 1])
        plt.xlim([0, 46])
        plt.xlabel('Trials')
        # plt.title(title)

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        if save in ('Y'):
            plt.savefig('./data/{}/figure_analysis/tgo_across_time_{}.svg'.format(folder, self.subject), transparent = True)


    def BarIsoAniso(self, title = None, folder = None, all = 'N', save = 'N'):

        fig, ax = plt.subplots(1, figsize = (10, 10))
        x = [1, 2]
        widthB = 3
        plt.bar(x, self.perCorrect, color = "None", edgecolor = ['#7D5D99', '#A32857'], linewidth = widthB)
        plt.rcParams.update({'font.size': 25})
        plt.xticks([1, 2])

        labels = [item.get_text() for item in ax.get_xticklabels()]
        labels[0] = 'In-phase'
        labels[1] = 'Out-phase'
        ax.set_xticklabels(labels)

        # plt.title(title)
        plt.xlabel('Phase')
        plt.ylabel('% correct responses')
        plt.ylim([0, 100])
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

        ax.xaxis.set_tick_params(width = widthB)
        ax.yaxis.set_tick_params(width = widthB)


        for axis in ['bottom','left']:
            ax.spines[axis].set_linewidth(3)

        plt.rcParams.update({'font.size': 25})

        if all == 'Y':
            for i, j in zip(self.perPartIso, self.perPartAniso):
                ax.plot(x, [i, j], color = 'k', lw = widthB)
                ax.scatter(x, [i, j], color = ['#7D5D99', '#A32857'])

        if save in ('Y'):
            plt.savefig('./data/{}/figure_analysis/tgo_Bar_IvsA_{}.svg'.format(folder, self.subject), transparent=True)

class TextInput(object):
    def __init__(self):
        pass

    def blocks(self):

        while True:
            self.n_blocks = input("\n How many blocks are we doing?  ")
            if self.n_blocks in ('1', '2', '3', '4', '5', '6'):
                self.n_blocks = int(self.n_blocks)
                break
            else:
                print("\n Only 1, 2, 3, 4, 5 and 6 are valid answers \n")
                continue

    def trials(self):

        while True:
            self.n_trials = input("\n How many trials are we doing?  ")
            try:
                self.n_trials = int(self.n_trials)
                break
            except:
                print("\n Only numbers are valid answers \n")
                continue

    def famStage(self):

        while True:
            self.BolStage = input("\n Are we doing the preparatory stage? (Y/n)  ")
            if self.BolStage in ('Y', 'n'):
                break
            else:
                print('\n Only "Y" and "n" are valid answers \n')
                continue
    def AFC(self):

        while True:
            self.decision = input("\n Which stimulus was oscillating? (Press 1 or 2. Then, press Enter)  ")
            if self.decision in ('1', '2'):
                globals.text_state += 1
                break
            else:
                print('\n Only 1 and 2 are valid answers \n')
                continue

    def AFCDummy(self):

        while True:
            self.decision_dummy = input("\n Which stimulus was oscillating? (Press 1 or 2. Then, press Enter)  ")
            if self.decision_dummy in ('1', '2'):
                globals.text_state += 1
                break
            else:
                print('\n Only 1 and 2 are valid answers \n')
                continue

    def subjectN(self):
        while True:
            self.subject_n = input("\n Subject number:  ")
            if self.subject_n in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'):
                break
            else:
                print('\n Only 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 are valid answers \n')
                continue

    def rangeTest(self):
        while True:
            self.range = input("\n What range are we testing? (warm/cold)  ")
            if self.range in ('warm', 'cold'):
                break
            else:
                print('\n Only "warm" and "cold" are valis answers \n')

    def meanOsc(self, range):
        while True:
            if range == 'warm':
                self.mean_warm = input("\n What is the mean temperature in the warm range?  ")
                try:
                    self.mean_warm = float(self.mean_warm)

                except:
                    print('\n Only numbers are valid answers \n')
                    continue

                break

            elif range == 'cold':
                self.mean_cold = input("\n What is the mean temperature in the cold range?  ")
                try:
                    self.mean_cold = float(self.mean_cold)

                except:
                    print('\n Only numbers are valid answers \n')
                    continue
                break

    def ampTemp(self):
        while True:
            self.amp_T = input("\n What is the amplitude tested?  ")
            try:
                self.amp_T = float(self.amp_T)
                try:
                    self.low_bound = self.mean_warm - self.amp_T/2
                    self.high_bound = self.mean_warm + self.amp_T/2
                except:
                    self.low_bound = self.mean_cold - self.amp_T/2
                    self.high_bound = self.mean_cold + self.amp_T/2
            except:
                print('\n Only numbers are valid answers \n')
                continue

            break

    def age(self):
        while True:
            self.age = input("\n How old are you?  Type your answer and press enter    ")
            try:
                self.age = float(self.age)

            except:
                print('\n Only numbers are valid answers \n')
                continue

            break

    def TargetTemp(self):
        while True:
            self.target_temp= input("\n What temperature do we want to reach?    ")
            try:
                self.target_temp = float(self.target_temp)

            except:
                print('\n Only numbers are valid answers \n')
                continue

            break

    def breaks(self):

        while True:
            self.n_breaks = input("\n When are we taking breaks?  ")
            if self.n_breaks in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20'):
                self.n_breaks = int(self.n_breaks)
                break
            else:
                print("\n Only 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 and 20 are valid answers \n")
                continue

    def pracAns(self):

        while True:
            self.prac_ans = input('\n How did that feel? (constant or changing)  ')
            if self.prac_ans in ('constant', 'changing'):
                break
            else:
                print("\n Only constant or changing are valid answers")
                continue

    def famOp(self):

        while True:
            self.fam_op = input("\n What condition are we familiarising with? (c1 / c2 / c3)   ")
            if self.fam_op in ('c1', 'c2', 'c3', 'd'):
                break
            else:
                print("\n Only c1, c2, c3 or d are valid inputs")

    def counterB(self):

        while True:
            self.counter = input("\n What block are we doing first?   ")
            if self.counter in ('I', 'A'):
                break
            else:
                print("\n Only I and A valid inputs")

    def PracOp(self):

        while True:
            self.prac_op = input("\n Are we doing the practise trials? (y / n)   ")
            if self.prac_op in ('y', 'n'):
                break
            else:
                print("\n Only y and n are valid inputs")



class analyseTTT(ploTTT):
    # def __init__(self):
    #     ploTTT.__init__(self, file, subject)

    @staticmethod
    def QQplot(file, distribution, parameters, path_qq, name_qq, range):
        percs_indvs = []

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                percs_indvs.append(sub_data.perCorrect)

        theor = []
        dataD = []

        for i in np.arange(len(percs_indvs)):
            theor.append(cdfProbPlot(percs_indvs[i], dist = distribution, sparams = parameters)[0])
            dataD.append(cdfProbPlot(percs_indvs[i], dist = distribution, sparams = parameters)[1])

        subs = 1

        fig = plt.figure(figsize = (10, 10), facecolor = 'w')

        for i in np.arange(len(percs_indvs)):
            ax = fig.add_subplot(4, 2, subs)
            ax.plot(theor[i][0], theor[i][1], 'bo', theor[i][0], dataD[i][0] * theor[i][0] + dataD[i][1], 'r')
            ax.set_xlabel('Theoretical quantiles')
            ax.set_ylabel('Data quantiles')
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            subs += 1

        fig.legend(['Fit', 'Perfect fit'])
        plt.suptitle('Distribution of {}: {}'.format(range, distribution))
        plt.subplots_adjust(top = 2)
        plt.ylim([50, 100])
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        plt.savefig('./{}/{}.svg'.format(path_qq, name_qq), transparent=True)

        return[percs_indvs, theor, dataD]

    def linearFit(self):
        self.s, self.i = np.polyfit(self.rates, self.perCorrect, 1)
        self.y_line = self.s * self.rates + self.i

    def plotLinearFit(self, color, title, path_fit, name_fit, save = 'Y'):
        fig, ax = plt.subplots(1,1)
        plt.plot(self.rates, self.perCorrect, '-{}'.format(color), self.rates, self.y_line, '--{}'.format(color))

        plt.ylim([50, 100])
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.hlines(y = 75, xmin = 0.100, xmax = 0.333, linestyles = 'dashed', lw = 0.4)
        plt.xticks(self.rates)
        plt.ylabel('% correct')
        plt.xlabel('Frequencies')
        plt.text(0.2, 55, 'Slope:  ' + str(round(self.s)))
        plt.text(0.2, 51, 'Intercept: ' + str(round(self.i)))
        plt.title(title)

        if save == 'Y':
            plt.savefig('./{}/{}.svg'.format(path_fit, name_fit), transparent = True)

    def bootstrapping(self, file, function, revolts, bootedObvs):
        self.revolts = revolts
        self.percs_indvs = []

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                self.percs_indvs.append(sub_data.bootedObvs)

        self.BS_samples = []

        for i in np.arange(revolts):
            bootstrapped_sample = skl.utils.resample(self.percs_indvs, n_samples = 8)
            BS_array = np.asarray(bootstrapped_sample)
            BS_mean = function(bootstrapped_sample, axis = 0)
            self.BS_samples.append(BS_mean)

        self.funced_BS = np.mean(self.BS_samples, axis = 0)

    def plotBoot(self, title, path, name, color_funced, color_parent, functionApplied, alpha = 0.03, save = 'Y'):

        fig, ax = plt.subplots(1, 1)
        ax.plot(self.rates, self.funced_BS, '-{}'.format(color_funced))
        ax.plot(self.rates, self.perCorrect, '-{}'.format(color_parent))

        for L in self.BS_samples:
            ax.plot(self.rates, L, color = '#4D4B50', alpha = alpha)

        plt.legend(['Bootstrapped {}'.format(functionApplied), 'Parent data', 'Bootstrapped samples'])
        plt.ylim([50, 100])
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.title(title)
        plt.ylabel('% correct')
        plt.xlabel('Frequencies')
        plt.xticks(self.rates)

        if save == 'Y':
            plt.savefig('./{}/{}.svg'.format(path, name), transparent = True)

    # Here we get the slopes of all bootstrapped samples
    def slopBoot(self):

        self.s_indvs = []
        self.i_indvs = []

        for i in np.arange(len(self.BS_samples)):
            s_dummy, i_dummy = np.polyfit(self.rates, self.BS_samples[i], 1)
            self.s_indvs.append(s_dummy)
            self.i_indvs.append(i_dummy)

    # Here we plot the linear fit to all our bootstrapped samples
    def plotSlop(self, title, path, name, color_funced, color_parent, functionApplied, alpha = 0.03, save = 'Y'):

        self.y_line_indvs = []

        fig, ax = plt.subplots(1, 1)
        ax.plot(self.rates, self.funced_BS, '-{}'.format(color_funced))
        ax.plot(self.rates, self.perCorrect, '-{}'.format(color_parent))

        for i in np.arange(len(self.s_indvs)):
            self.y_line_indvs.append(self.s_indvs[i] * self.rates + self.i_indvs[i])
            ax.plot(self.rates, self.y_line_indvs[i], '--', alpha = alpha)


        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.ylim([50, 100])

        plt.ylabel('% correct')
        plt.xlabel('Frequencies')
        plt.xticks(self.rates)

        plt.legend(['Bootstrapped {}'.format(functionApplied), 'Parent data', 'Bootstrapped samples'])
        plt.title(title)
        if save == 'Y':
            plt.savefig('./{}/{}.svg'.format(path, name), transparent = True)

    def CIBoot(self, data, lowBound, highBound):
        self.sorted_data = np.sort(data)

        self.lowCI = self.sorted_data[np.round(self.revolts * (lowBound/100)/2).astype(int)]
        self.highCI = self.sorted_data[np.round(self.revolts * (highBound/100)/2).astype(int)]

    @staticmethod
    def CIdifff(data1, data2, lowBound, highBound, revolts):
        data1 = np.asarray(data1)
        data2 = np.asarray(data2)
        bootdiff = np.subtract(data1, data2)
        sorted_bootdiff = np.sort(bootdiff)

        ci_diff = (sorted_bootdiff[np.round(revolts * (lowBound/100)/2).astype(int)],
             sorted_bootdiff[np.round(revolts * (highBound/100)/2).astype(int)])

        return ci_diff, bootdiff

    @staticmethod
    def pValueBoots(data1, data2,  obvs_value, revolts, round_place, function, args = None, x = []):
        eng = me.start_matlab()

        pooled = np.append(data1, data2)
        bs_samples = []


        for i in np.arange(10000):
            bootstrapped_sample = skl.utils.resample(pooled, n_samples = (len(data1) + len(data2)))
            BS_array = np.asarray(bootstrapped_sample)
            bs_1 = BS_array[0:len(data1)]
            bs_2 = BS_array[len(data1):(len(data1) + len(data1))]

            if function == np.polyfit:
                s_1, i_1 = function(x, bs_1, args)
                s_2, i_2 = function(x, bs_2, args)

            if function == eng.nonParamAnalysis:

                [xfit, pfit, threshold, s_1, sd_th, sd_sl] = eng.nonParamAnalysis(x, nargout = 6)
                [xfit, pfit, threshold, s_2, sd_th, sd_sl] = eng.nonParamAnalysis(x, nargout = 6)


            bs_s = s_1 - s_2
            bs_samples.append(bs_s)

        thres_values = [i for i in bs_samples if i >= obvs_value]

        p_value = round((len(thres_values) + 1) / (revolts + 1), round_place)

        return p_value

    @staticmethod
    def poolST(data1, data2):
        pooled = []
        for i, j in zip((data1, data2)):
            temp = np.array([i, j])
            pooled.append(temp)

    def timePerformance(self, exclude = None):

        self.hits_time = []
        for i in np.arange(max(self.RawData['n_subject'])):
            if i == exclude:
                pass
            else:
                temp_subset = self.RawData.loc[self.RawData['n_subject'] == i + 1]
                # print(temp_subset)
                self.hits_time.append(temp_subset['grade'])
                self.grade_t = np.mean(np.asarray(self.hits_time), axis = 0)

    def AUCPerformance(self, n_chunks):
        self.AUC_chunks = []
        self.n_chunks = n_chunks
        self.chunks = np.split(self.grade_t, n_chunks)
        self.AUCS = np.empty(n_chunks)

        for i in np.arange(n_chunks):
            self.AUCS[i] = np.trapz(self.chunks[i])

        for i in np.arange(len(self.hits_time)):
            dummy_chunk = np.split(self.hits_time[i], n_chunks)
            dummy_AUCs = np.empty(n_chunks)

            for i in np.arange(len(dummy_chunk)):
                dummy_AUCs[i] = np.trapz(dummy_chunk[i])

            self.AUC_chunks.append(dummy_AUCs)

    def AUCPlot(self, path, name, color, min_y, max_y, title = None):

        fig, ax = plt.subplots(1, 1)
        ax.plot(np.arange(1, len(self.AUCS) + 0.1, step = 1) , self.AUCS, '-{}'.format(color))

        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.ylim([min_y, max_y])
        plt.xlim([1, self.n_chunks])

        for i in np.arange(len(self.hits_time)):
            ax.plot(np.arange(1, len(self.AUCS) + 0.1, step = 1), self.AUC_chunks[i], color = 'k', alpha = 0.1)

        plt.xticks(np.arange(1, self.n_chunks + 0.1, step = 1))
        plt.xlabel('Periods')
        plt.ylabel('AUC')

        # plt.title(title)
        plt.savefig('./{}/{}.svg'.format(path, name), transparent = True)

    def jackKnifeNonParametric(self, file, repeats):
        percs_indvs_T = []
        eng = me.start_matlab()

        for i in np.arange(9):
            if i == 4:
                pass
            else:
                sub_data = ploTTT(file, i + 1)
                sub_data.correctRate()
                percs_indvs_T.append(sub_data.sf)

        self.n_T = len(percs_indvs_T)
        self.indexT = np.arange(self.n_T)

        self.xfit_jkT = []
        self.pfit_jkT = []
        self.threshold_jkT = []
        self.slopes_jkT = []
        self.sd_th_jkT = []
        self.sd_sl_jkT = []

        percs_indvs_T = np.asarray(percs_indvs_T)

        for i in range(self.n_T):
            jk_sampleT = percs_indvs_T[self.indexT != i]
            summed_jkT = np.sum(jk_sampleT, axis = 0)
            summed_jkT = np.ndarray.tolist(summed_jkT)
            summed_jkT = [float(i) for i in summed_jkT]

            [xfitT, pfitT, thresholdT, slopeT, sd_thT, sd_slT] = eng.nonParamAnalysis(self.ratesLf, summed_jkT, repeats, nargout = 6)

            self.xfit_jkT.append(xfitT)
            self.pfit_jkT.append(pfitT)
            self.threshold_jkT.append(thresholdT)
            self.slopes_jkT.append(slopeT)
            self.sd_th_jkT.append(sd_thT)
            self.sd_sl_jkT.append(sd_slT)

    def plotJKs(self, color_data, color_nonPar, title = None, alpha = 0.05, save = 'Y', path = None, name = None):
            fig, ax = plt.subplots(1, 1)
            self.meaned_nonParametric = np.mean(self.pfit_jkT, axis = 0)
            ax.plot(self.rates, self.perCorrect/100, '-{}'.format(color_data))
            ax.plot(self.xfit_jkT[0], self.meaned_nonParametric, '-{}'.format(color_nonPar))

            for i in np.arange(len(self.pfit_jkT)):
                ax.plot(self.xfit_jkT[i], self.pfit_jkT[i], '--', alpha = alpha)


            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            plt.ylim([0.5, 1])
            plt.xlim([0.100, 0.333])

            plt.ylabel('% correct')
            plt.xlabel('Hz')
            plt.xticks(self.rates)

            plt.legend(['Original data', 'Mean jack-knife', 'Jack-knife samples'])
            plt.title(title)
            if save == 'Y':
                plt.savefig('./{}/{}.svg'.format(path, name), transparent = True)

################################################################################
################################ Functions ######################################
################################################################################

def cdfProbPlot(x, dist, sparams = ()):
    x = np.asarray(x)


    osm_uniform = stats.stats._calc_uniform_order_statistic_medians(len(x))
    dist = stats.stats._parse_dist_kw(dist, enforce_subclass=False)
    if sparams is None:
        sparams = ()
    if isscalar(sparams):
        sparams = (sparams,)
    if not isinstance(sparams, tuple):
        sparams = tuple(sparams)

    osm = dist.ppf(osm_uniform, *sparams)
    osr = sort(x)

    # perform a linear least squares fit.
    slope, intercept, r, prob, sterrest = stats.linregress(osm, osr)

    return (osm, osr), (slope, intercept, r)

def cdfplot(theor, data, path_qq, name_qq, range, distribution):

    fig, ax = plt.subplots(1, 1)
    plt.plot(theor[0], theor[1], 'bo', theor[0], data[0] * theor[0] + data[1], 'r')
    ax.set_xlabel('Theoretical quantiles')
    ax.set_ylabel('Data quantiles')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    fig.legend(['Fit', 'Perfect fit'])
    plt.title('Distribution of {}: {}'.format(range, distribution))
    plt.subplots_adjust(top = 2)
    plt.ylim([50, 100])
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    plt.savefig('./{}/{}.svg'.format(path_qq, name_qq), transparent=True)

    return

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

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



    # def sub_age(self):
    #     while True:
    #         self.age = input("\n How old are you?   ")
    #
    #         if self.age in np.arange(18,100):
    #           break
    #         else:
    #           print('\n Only numbers from 18-99 are valid answers')
    #           continue
    #
    # def sub_sex(self):
    #     while True:
    #         self.sex = input("\n What sex do you identify with? (f for female, m for male and o for other)")
    #
    #         if self.sex in ('f', 'm', 'o'):
    #           break
    #         else:
    #           print('\n Only f, m and o are valid answers')
    #           continue
