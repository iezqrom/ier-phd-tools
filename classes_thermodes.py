#!/usr/bin/env python3

# System
from datetime import datetime
import threading
import time
import keyboard

import warnings
import itertools
import sys


# Maths
import matplotlib.pyplot as plt
import numpy as np
import math
import random

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

default_rate = 100
steps_range = 0.1
analog_output_mVolts = np.array([-62.2, -12.9, 35.9, 85, 134.6, 182.2, 234.2, 286, 338.2, 389.3, 440.9])

class Thermode(object):

    default_rate = 100
    steps_range = 0.1
    analog_output_mVolts = np.array([-62.2, -12.9, 35.9, 85, 134.6, 182.2, 234.2, 286, 338.2, 389.3, 440.9])

    # We first initialise the object by mapping temperatures onto the voltages given by the manual of the thermodes.
    # This manual can be found in office 207a as of December 2019
    def __init__(self, dev, pins, lower = 0, upper = 51):
        """
            This class is to use a single thermode through a NIDAQ box
        """
        self.dev = dev
        self.Ai = pins["input_pin"]
        self.Ao = pins["output_pin"]
        self.rate = self.default_rate

        ## We need to map the temperatures with the Voltages ##
        self.range_temp = np.arange(lower, upper, self.steps_range)
        self.range_temp = self.range_temp.round(decimals=1)

        self.temp = np.arange(0, 51, 5) # From manual

        self.mVolts = self.analog_output_mVolts # Analog Output mV AOP
        self.volts = np.divide(self.mVolts, 1000) # conversion from mV to V
        self.volts = self.volts.round(decimals=4)

############################################

        def voltToTemp(volt, steps_range = 0.1, lower = 0, upper = 51):

            ## We need to map the temperatures with the Voltages ##
            range_temp = np.arange(lower, upper, steps_range)
            range_temp = range_temp.round(decimals=1)

            temps = np.arange(0, 51, 5) # From manual

            mVolts = analog_output_mVolts # Analog Output mV AOP
            volts = np.divide(mVolts, 1000) # conversion from mV to V
            volts = volts.round(decimals=4)

            # Interpolating
            range_volt = np.interp(range_temp, temps, volts)

            # We stack the data
            temp_volt = np.stack((range_temp, range_volt))

            nearest_volt = find_nearest(temp_volt[1], volt)

            indx_currT = np.where(temp_volt[1] == nearest_volt)

            temp_current = temp_volt[0,  indx_currT]
            temp = temp_current[0][0]

            return temp

############################################

        # Interpolating
        self.range_volt = np.interp(self.range_temp, self.temp, self.volts)

        # We stack the data
        self.temp_volt = np.stack((self.range_temp, self.range_volt))

    def readTemp(self, samples = 100):
        """
            Method of Zaber (object) to obtain the current temperature.
            Important created attributes: self.temp_current (current temperature) & self.volt_current (voltage equivalent of current temperature).
        """
        self.ai_task = NT.Task()
        self.ai_task.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(self.dev, self.Ai))
        self.ai_task.timing.cfg_samp_clk_timing(rate = self.rate, samps_per_chan =  samples, sample_mode= NC.AcquisitionType.FINITE)

        self.ai_task.wait_until_done(timeout = 50)

        self.ai_task.start()
        self.currentTdata = self.ai_task.read(number_of_samples_per_channel = samples)

        self.ai_task.close()

        self.meancurrentTdata = np.mean(np.asarray(self.currentTdata))
        self.nearest_volt = find_nearest(self.temp_volt[1], self.meancurrentTdata)

        self.indx_currT = np.where(self.temp_volt[1] == self.nearest_volt)

        self.temp_current = self.temp_volt[0,  self.indx_currT]
        self.temp_current = self.temp_current[0][0]
        self.volt_current = self.nearest_volt

    def rampCurrTarget(self, target_temp):
        """
            Method of Zaber (object) to create a ramp to reach temperature X from the current temperature.
            Important created attributes: self.volt (voltage to write with IO_thermode).
        """
        self.target_temp = target_temp

        self.nearest_temp_target = find_nearest(self.temp_volt[0], target_temp)

        self.indx_target = np.where(self.temp_volt[0] == self.nearest_temp_target)

        self.volt_ref_target = self.temp_volt[1, self.indx_target]

        print(self.volt_ref_target)

        if self.temp_current > target_temp:
            self.volt = np.arange(self.volt_current, self.volt_ref_target, - self.volt_ref_target/1000)

        elif target_temp > self.temp_current:
            self.volt = np.arange(self.volt_current, self.volt_ref_target, self.volt_ref_target/1000)

    def rampStartTarget(self, start_temp, target_temp):
        """
            Method of Zaber (object) to create a ramp to reach temperature X from temperature Y.
            Important created attributes: self.volt (voltage to write with IO_thermode).
        """
        self.start_temp = start_temp
        self.target_temp = target_temp

        self.nearest_temp_start = find_nearest(self.temp_volt[0], start_temp)
        self.nearest_temp_target = find_nearest(self.temp_volt[0], target_temp)

        self.indx_start = np.where(self.temp_volt[0] == self.nearest_temp_start)
        self.indx_target = np.where(self.temp_volt[0] == self.nearest_temp_target)

        self.volt_ref_start = self.temp_volt[1,  self.indx_start]
        self.volt_ref_target = self.temp_volt[1, self.indx_target]

        if start_temp > target_temp:
            self.volt = np.arange(self.volt_ref_start, self.volt_ref_target, - self.volt_ref_target/1000)

        elif target_temp > start_temp:
            self.volt = np.arange(self.volt_ref_start, self.volt_ref_target, self.volt_ref_target/1000)

    def IO_thermode(self, voltI = None): #Ai ai8 // Ao ao0
        """
            Method of Zaber (object) to write voltage to and read data (voltage) from thermode.
            The attribute self.volt is written if one (voltI) is not given.

            Important attributes created: self.data (data read from thermode) & self.end_TT (time to write and execute volt)
        """
        try:
            if voltI == None:
                volt = self.volt
        except:
            volt = voltI

        try:
            len_volt = len(volt)
        except:
            volt = [volt, volt]
            len_volt = len(volt)
            raise('Voltage output has to be an array of minimum 2 values')

        print('Length voltage: {}'.format(len_volt))

        self.ai_task = NT.Task()
        self.ai_task.ai_channels.add_ai_voltage_chan(physical_channel = '/{}/{}'.format(self.dev, self.Ai))
        self.ai_task.timing.cfg_samp_clk_timing(rate = self.rate, samps_per_chan = len_volt, sample_mode= NC.AcquisitionType.FINITE)

        # configuring ao task: writing data
        self.ao_task = NT.Task()
        self.ao_task.ao_channels.add_ao_voltage_chan('/{}/{}'.format(self.dev, self.Ao))
        self.ao_task.timing.cfg_samp_clk_timing(rate = self.rate, samps_per_chan = len_volt, sample_mode = NC.AcquisitionType.FINITE,
        source = 'ai/SampleClock')

        self.start_TT = datetime.now()

        while True:
            try:
                self.ao_task.write(volt)
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

        self.data = self.ai_task.read(number_of_samples_per_channel = len_volt)

        self.ai_task.close()
        self.ao_task.close()

        self.end_TT = datetime.now() - self.start_TT

    def method_of_limits(self, direction, temp_rate = 0.2 , amount = 1):
        """
            Method of Zaber (object) to find thresholds with method of limits strategy.

            rate: rate at each the NIDAQ box will read the voltage signal (self.volt)
            Ia: input pin
            Io: output pin
            direction: 'up' (warm threshold) or 'down' (cold threshold)
            amount:

            Import attributes created: self.final_temp (threshold)
        """

        if direction == 'up':
            self.rampCurrTarget(42)
        elif direction == 'down':
            self.rampCurrTarget(17)
        else:
            raise NameError("Value direction can only be 'up' or 'down'")

        try:
            len_volt = len(self.volt)
        except:
            volt = [self.volt, self.volt]
            len_volt = len(volt)
            raise('Voltage output has to be an array of minimum 2 values')


        def ramp_loop(volt, len_volt, dev, Ao, Ai, rate):
            self.ao_task = NT.Task()
            self.ao_task.ao_channels.add_ao_voltage_chan('/{}/{}'.format(dev, Ao))
            self.ao_task.timing.cfg_samp_clk_timing(rate = rate, samps_per_chan = len_volt, sample_mode = NC.AcquisitionType.FINITE)

            self.start_TT = datetime.now()

            while True:
                try:
                    self.ao_task.write(volt)
                except:
                    continue
                else:
                    break

            # run the task
            self.ao_task.start()

            while True:
                print('looping')
                if keyboard.is_pressed('space'):
                    self.ao_task.close()
                    self.readTemp(Ai)
                    print(self.temp_current)
                    print('we are here')
                    break
            # self.ao_task.wait_until_done(timeout = 50)

        ramp_loop(self.volt, len_volt, self.dev, self.Ao, self.Ai, self.rate)


    ##### Working progress
    def adjust_single(self, start_temp, target_temp):
        """
            Method of Zaber (object)
            This method is in working progress. The aim is to develop a matching paradigm
        """

        self.ramp(start_temp, target_temp)
        self.IO_thermode(self.rate, self.Ia, self.Io)

        while True:

            if keyboard.is_pressed('up'):
                self.volt = self.data + 0.0000992
                self.IO_thermode(self.rate, self.Ia, self.Io)

            elif keyboard.is_pressed('up'):
                self.volt = self.data + 0.0000992
                self.IO_thermode(self.rate, self.Ia, self.Io)

            elif keyboard.is_pressed('e'):
                break

######################## FUNCTIONS

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def voltToTemp(volt, steps_range = 0.1, lower = 0, upper = 51):

    ## We need to map the temperatures with the Voltages ##
    range_temp = np.arange(lower, upper, steps_range)
    range_temp = range_temp.round(decimals=1)

    temps = np.arange(0, 51, 5) # From manual

    mVolts = analog_output_mVolts # Analog Output mV AOP
    volts = np.divide(mVolts, 1000) # conversion from mV to V
    volts = volts.round(decimals=4)

    # Interpolating
    range_volt = np.interp(range_temp, temps, volts)

    # We stack the data
    temp_volt = np.stack((range_temp, range_volt))

    nearest_volt = find_nearest(temp_volt[1], volt)

    indx_currT = np.where(temp_volt[1] == nearest_volt)

    temp_current = temp_volt[0,  indx_currT]
    temp = temp_current[0][0]

    return temp