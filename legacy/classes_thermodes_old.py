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
from numpy import (
    isscalar,
    r_,
    log,
    around,
    unique,
    asarray,
    zeros,
    arange,
    sort,
    amin,
    amax,
    any,
    atleast_1d,
    sqrt,
    ceil,
    floor,
    array,
    compress,
    pi,
    exp,
    ravel,
    count_nonzero,
    sin,
    cos,
    arctan2,
    hypot,
)
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


class Thermode(object):

    steps_range = 0.1

    # We first initialise the object by mapping temperatures onto the voltages given by the manual of the thermodes.
    # This manual can be found in office 207a as of December 2019
    def __init__(self, dev, rate, lower=0, upper=51):
        """
        This class is to use a single thermode through a NIDAQ box
        """
        self.dev = dev
        self.rate = rate
        ## We need to map the temperatures with the Voltages ##
        self.range_temp = np.arange(lower, upper, self.steps_range)
        self.range_temp = self.range_temp.round(decimals=1)

        self.temp = np.arange(0, 51, 5)  # From manual

        self.mVolts = np.array(
            [-62.2, -12.9, 35.9, 85, 134.6, 182.2, 234.2, 286, 338.2, 389.3, 440.9]
        )  # Analog Output mV AOP
        self.volts = np.divide(self.mVolts, 1000)  # conversion from mV to V
        self.volts = self.volts.round(decimals=4)

        # Interpolating
        self.range_volt = np.interp(self.range_temp, self.temp, self.volts)

        # We stack the data
        self.temp_volt = np.stack((self.range_temp, self.range_volt))

    def readTemp(self, Ai, samples=100):
        """
        Method of Zaber (object) to obtain the current temperature.
        Important created attributes: self.temp_current (current temperature) & self.volt_current (voltage equivalent of current temperature).
        """
        self.ai_task = NT.Task()
        self.ai_task.ai_channels.add_ai_voltage_chan(
            physical_channel="/{}/{}".format(self.dev, Ai)
        )
        self.ai_task.timing.cfg_samp_clk_timing(
            rate=self.rate, samps_per_chan=samples, sample_mode=NC.AcquisitionType.FINITE
        )

        self.ai_task.wait_until_done(timeout=50)

        self.ai_task.start()
        self.currentTdata = self.ai_task.read(number_of_samples_per_channel=samples)

        self.ai_task.close()

        self.meancurrentTdata = np.mean(np.asarray(self.currentTdata))
        self.nearest_volt = find_nearest(self.temp_volt[1], self.meancurrentTdata)

        self.indx_currT = np.where(self.temp_volt[1] == self.nearest_volt)

        self.temp_current = self.temp_volt[0, self.indx_currT]
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

        if self.temp_current > target_temp:
            self.volt = np.arange(
                self.volt_current, self.volt_ref_target, -self.volt_ref_target / 1000
            )

        elif target_temp > self.temp_current:
            self.volt = np.arange(
                self.volt_current, self.volt_ref_target, self.volt_ref_target / 1000
            )

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

        self.volt_ref_start = self.temp_volt[1, self.indx_start]
        self.volt_ref_target = self.temp_volt[1, self.indx_target]

        if start_temp > target_temp:
            self.volt = np.arange(
                self.volt_ref_start, self.volt_ref_target, -self.volt_ref_target / 1000
            )

        elif target_temp > start_temp:
            self.volt = np.arange(
                self.volt_ref_start, self.volt_ref_target, self.volt_ref_target / 1000
            )

    def IO_thermode(
        self, Ai, Ao, voltI=None
    ):  # Ai ai8 // Ao ao0
        """
        Method of Zaber (object) to write voltage to and read data (voltage) from thermode.
        The attribute self.volt is written if one (voltI) is not given.

        Important attributes created: self.data (data read from thermode) & self.end_TT (time to write and execute volt)
        """
        if voltI == None:
            volt = self.volt
        else:
            volt = voltI

        print("Length voltage")
        print(len(volt))

        self.ai_task = NT.Task()
        self.ai_task.ai_channels.add_ai_voltage_chan(
            physical_channel="/{}/{}".format(self.dev, Ai)
        )
        self.ai_task.timing.cfg_samp_clk_timing(
            rate=self.rate, samps_per_chan=len(volt), sample_mode=NC.AcquisitionType.FINITE
        )

        # configuring ao task: writing data

        self.ao_task = NT.Task()
        self.ao_task.ao_channels.add_ao_voltage_chan("/{}/{}".format(self.dev, Ao))
        self.ao_task.timing.cfg_samp_clk_timing(
            rate=self.rate,
            samps_per_chan=len(volt),
            sample_mode=NC.AcquisitionType.FINITE,
            source="ai/SampleClock",
        )

        self.start_TT = datetime.now()

        while True:
            try:
                self.ao_task.write(volt)
            except:
                # print('We are trying')
                continue
            else:
                break

        # run the task
        self.ao_task.start()
        self.ai_task.start()

        self.ao_task.wait_until_done(timeout=50)
        self.ai_task.wait_until_done(timeout=50)

        self.data = self.ai_task.read(number_of_samples_per_channel=len(self.volt))

        self.ai_task.close()
        self.ao_task.close()

        self.end_TT = datetime.now() - self.start_TT
        print(self.end_TT)

    def method_of_limits(
        self, Ai, Ao, direction, temp_rate=0.2, amount=0.1
    ):
        """
        Method of Zaber (object) to find thresholds with method of limits strategy.

        rate: rate at each the NIDAQ box will read the voltage signal (self.volt)
        Ia: input pin
        Io: output pin
        direction: 'up' (warm threshold) or 'down' (cold threshold)
        amount:

        Import attributes created: self.final_temp (threshold)
        """

        if direction == "up":
            drt = 1
        elif direction == "down":
            drt = -1
        else:
            raise NameError("Value direction can only be 'up' or 'down'")

        def stop_ramp():
            global button_state
            button_state = False
            if keyboard.is_pressed("space"):
                self.final_temp = self.data
                button_state = True

        def ramp_loop():
            global button_state
            while button_state == True:
                time.sleep(temp_rate)
                self.readTemp(Ai)

                # security noxious temperature check
                if self.temp_current > 42 or self.temp_current < 17:
                    button_state = True

                temp_next_amount = self.temp_current + (drt * amount)
                self.rampCurrTarget(temp_next_amount)
                self.IO_thermode(self.rate, Ai, Ao)
                if button_state == False:
                    break

        ramp_thread = threading.Thread(target=ramp_loop)
        stop_ramp_thread = threading.Thread(target=stop_ramp)

        ramp_thread.start()
        stop_ramp_thread.start()

        ramp_thread.join()
        stop_ramp_thread.join()

    ##### Working progress
    def adjust_single(self, Ia, Io, start_temp, target_temp):
        """
        Method of Zaber (object)
        This method is in working progress. The aim is to develop a matching paradigm
        """

        self.ramp(start_temp, target_temp)
        self.IO_thermode(self.rate, Ia, Io)

        while True:

            if keyboard.is_pressed("up"):
                self.volt = self.data + 0.0000992
                self.IO_thermode(self.rate, Ia, Io)

            elif keyboard.is_pressed("up"):
                self.volt = self.data + 0.0000992
                self.IO_thermode(self.rate, Ia, Io)

            elif keyboard.is_pressed("e"):
                break


class Gethermodes(object):
    def __init__(self, thermodes="all"):
        # This class is to run the thermodes, __init__ starts a global task and set thermode array
        self.tisk = NT.Task()
        self.tosk = NT.Task()
        self.nameTisk = self.tisk.name
        self.nameTosk = self.tosk.name

        if thermodes == "all":
            self.array_thermodes = [("ai28", "ao3"), ("ai24", "ao2"), ("ai8", "ao0")]
            self.n_channels = 3
        elif thermodes == ("1", "2"):
            self.array_thermodes = [("ai28", "ao3"), ("ai24", "ao2")]
            self.n_channels = 2
        elif thermodes == ("1", "3"):
            self.array_thermodes = [("ai28", "ao3"), ("ai8", "ao0")]
            self.n_channels = 2
        elif thermodes == ("2", "3"):
            self.array_thermodes = [("ai24", "ao2"), ("ai8", "ao0")]
            self.n_channels = 2

    def InputChannels(self, data):

        if self.n_channels != 2 and self.n_channels != 3:
            print("Wrong number of channels")
        elif self.n_channels == 2:
            self.tisk.ai_channels.add_ai_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[0][0])
            )
            self.tisk.ai_channels.add_ai_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[1][0])
            )
        elif self.n_channels == 3:
            self.tisk.ai_channels.add_ai_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[0][0])
            )
            self.tisk.ai_channels.add_ai_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[1][0])
            )
            self.tisk.ai_channels.add_ai_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[2][0])
            )

        self.tisk.timing.cfg_samp_clk_timing(
            rate=self.rate, samps_per_chan=len(data), sample_mode=NC.AcquisitionType.FINITE
        )

    def OutputChannels(self, data):

        if self.n_channels != 2 and self.n_channels != 3:
            print("Wrong number of channels")
        elif self.n_channels == 2:
            self.tosk.ao_channels.add_ao_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[0][1])
            )
            self.tosk.ao_channels.add_ao_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[1][1])
            )
        elif self.n_channels == 3:
            self.tosk.ao_channels.add_ao_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[0][1])
            )
            self.tosk.ao_channels.add_ao_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[1][1])
            )
            self.tosk.ao_channels.add_ao_voltage_chan(
                physical_channel="/{}/{}".format(self.dev, self.array_thermodes[2][1])
            )

        self.tosk.timing.cfg_samp_clk_timing(
            rate=self.rate,
            samps_per_chan=len(data),
            sample_mode=NC.AcquisitionType.FINITE,
            source="ai/SampleClock",
        )

    def run(self, data):
        self.stacked = np.stack(data)

        total += 1

        start = time.time()

        self.tosk.write(self.stacked)

        self.tosk.start()
        self.tisk.start()

        self.tosk.wait_until_done(timeout=50)
        self.tisk.wait_until_done(timeout=50)

        self.data = self.tisk.read(number_of_samples_per_channel=len(data[0]))

        # print('Run' + str(self.nameTosk))

        end = time.time()
        # print('{}'.format(end - start))

        time.sleep(0.05)
        self.tosk.close()
        self.tisk.close()
        winsound.PlaySound(None, winsound.SND_PURGE)
        total -= 1

    def PlotScreen(self, repeats):
        self.duration = int(1000 * 1 / self.rate)
        self.duration = self.duration * repeats
        self.time = np.arange(0, self.duration, self.duration / (1000 * repeats))

        fig, axes = plt.subplots(1, self.n_channels)
        # print('Len time:  ' + str(len(self.time)))
        # print('Len data:  ' + str(len(self.data[0])))
        counter = 0
        for ax in axes:
            ax.plot(self.time, self.data[counter], label="Voltage from Thermode")
            ax.plot(self.time, self.stacked[counter], label="Signal sent to Thermode")
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
            ax.set_title("Thermode {}".format(counter + 1))
            ax.set_xlabel("Seconds")
            ax.set_ylabel("Voltage")
            counter += 1

        handles, labels = ax.get_legend_handles_labels()
        fig.legend(handles, labels, loc="best")

        plt.show()


class Oscillation(Thermode, Gethermodes):
    def __init__(self, lower, upper, thermodes="all"):
        thermode.__init__(self, lower=lower, upper=upper)
        gethermodes.__init__(self, thermodes="all")

    def sineWave(self, freq, phase=0, repeats=1):

        ## Sine wave
        self.t = np.arange(0, repeats * 10, 0.01)
        self.w = 2 * math.pi * freq
        self.phi = phase  # phase to change the phase of sine function

        self.A = (max(self.range_volt) - min(self.range_volt)) / 2
        self.volt = (
            self.A * np.sin(self.w * self.t + self.phi)
            + (max(self.range_volt) + min(self.range_volt)) / 2
        )

        # self.volt = np.tile(self.volt, repeats)
        self.duration = int(1000 * repeats / self.rate)  # duration of sound

    def IO_osc(self, IaT, OaT):

        self.start_osc = datetime.now()

        # print('Length:  ' + str(len(self.volt_long)))

        # for i in range(0, len(self.volt_long), 2):
        #     # print('We are here')
        #
        #     self.volt = self.volt_long[i:i + 2]
        #     print(self.volt)
        thermode.IO_thermode(self, rate, IaT, OaT)

        self.data_osc = self.data

        self.end_osc = datetime.now() - self.start_osc
        # print(self.end_osc)

    def plotSingleSine(self, name_save=None, path_save=None, save="Y"):
        self.durationSine = int(1000 * 1 / self.rate)  # duration of sound
        fig, ax = plt.subplots(1, 1)
        self.timePlotSine = np.arange(0, self.durationSine, self.durationSine / 1000)
        plt.plot(self.timePlotSine, self.data_osc, label="Voltage from Thermode")
        plt.plot(self.timePlotSine, self.volt, "r", label="Wave create for Thermode")

        ax.legend()
        plt.ylabel("Voltage")
        plt.xlabel("Seconds")

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.show()

        if save in "Y":
            fig.savefig("./{}/{}.svg".format(path_save, name_save))
            plt.close()


class Constant(Thermode, Gethermodes):
    def __init__(self, cons_temp, repeats, length, thermodes="all"):
        thermode.__init__(self, lower=17, upper=51)
        gethermodes.__init__(self, thermodes="all")
        self.cons_temp = cons_temp

        # super().__init__(range_temp, temp, mVolts, volts, range_volt)

        # Stacking array
        self.temp_volt = np.stack((self.range_temp, self.range_volt))
        self.temp_volt = self.temp_volt.T

        # Finding voltage for corresponding text temp
        self.nearest_temp = find_nearest(self.temp_volt[:, 0], cons_temp)
        self.volt_ref = self.temp_volt[
            np.where(self.temp_volt[:, 0] == self.nearest_temp)
        ]
        self.volt_ref = self.volt_ref[0, 1]
        self.volt = np.repeat(self.volt_ref, length)
        # print(len(self.volt))
        self.durationCons = int(1000 * repeats / rate_NI)  # duration of sound
        self.repeats = repeats

    def IO_constant(self, IaT, OaT, rate=rate_NI):

        thermode.IO_thermode(self, rate, IaT, OaT)
        self.data_cons = self.data

    def plotSingleCons(self):

        fig, ax = plt.subplots(1, 1)
        self.timePlotCons = np.arange(
            0, self.durationCons, self.durationCons / (self.repeats * 1000)
        )

        plt.plot(self.timePlotCons, self.data_cons, label="Voltage from Thermode")
        plt.plot(self.timePlotCons, self.volt, "r", label="Wave create for Thermode")

        ax.legend()
        plt.ylabel("Voltage")
        plt.xlabel("Seconds")

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

        plt.show()

    def IO_constantTrioText(self, data):

        self.start_ref = datetime.now()
        self.data_target = []

        while True:

            trio = gethermodes()
            trio.InputChannels(self.volt)
            trio.OutputChannels(self.volt)
            trio.run(data)

            if text_state == 1:
                break
            else:
                continue

    # def IO_cons(self, IaT, OaT, time, cons_dummy = 0.001, rate = rate_NI):
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

    # def IO_constantTrio(self, data, ref_dummy = 0.01, rate = rate_NI):
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


class Target(Thermode, Gethermodes):

    steps_range = 0.004

    def __init__(self, reach_temp, thermodes="all", lower=17, upper=51):
        thermode.__init__(self, lower=17, upper=51)
        gethermodes.__init__(self, thermodes="all")

        # super().__init__(range_temp, temp, mVolts, volts, range_volt)

        # Stacking array
        self.temp_volt = np.stack((self.range_temp, self.range_volt))
        self.temp_volt = self.temp_volt.T

        # Finding voltage for corresponding text temp
        self.nearest_temp = find_nearest(self.temp_volt[:, 0], reach_temp)
        self.volt_ref = self.temp_volt[
            np.where(self.temp_volt[:, 0] == self.nearest_temp)
        ]
        self.volt_ref = self.volt_ref[0, 1]
        self.volt = np.repeat(self.volt_ref, 2)

    def IO_referenceSingle(self, IaT, OaT, ref_dummy=0.01, rate=rate_NI):
        self.start_ref = datetime.now()
        self.data_target = []

        while True:

            thermode.IO_thermode(self, rate, IaT, OaT)

            if np.mean(self.data) > (np.mean(self.volt) - ref_dummy) and np.mean(
                self.data
            ) < (np.mean(self.volt) + ref_dummy):
                self.while_ref = datetime.now() - self.start_ref
                self.data_target = np.asarray(list(itertools.chain(*self.data_target)))
                break
            else:
                print("\n Reaching reference temperature...")
                self.volt = np.repeat(self.volt_ref, 2)
                self.data_target.append(self.data)
                continue

    def IO_referenceTrio(self, ref_dummy=0.01, rate=rate_NI):
        self.start_ref = datetime.now()
        self.data_target = []

        while True:
            trio = gethermodes()
            trio.InputChannels(self.volt)
            trio.OutputChannels(self.volt)
            trio.run((self.volt, self.volt, self.volt))

            mean_trio = np.mean(trio.data, axis=1)

            if all(i > (np.mean(self.volt) - ref_dummy) for i in mean_trio) and all(
                i < (np.mean(self.volt) + ref_dummy) for i in mean_trio
            ):
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

    def plotSingleReference(self, name_save=None, path_save=None, save="Y"):
        fig, ax = plt.subplots(1, 1)
        self.time_target = np.arange(0, len(self.data_target))
        print(np.asarray(self.data_target))
        test = np.asarray(self.data_target)
        print(test.shape)

        plt.plot(self.time_target, self.data_target, label="Voltage from Thermode")

        ax.legend()
        plt.ylabel("Voltage")
        plt.xlabel("Seconds")

        plt.text(1, np.mean(self.data_target), str(self.end_TT) + "s")
        # print(self.volt)
        plt.text(2, np.mean(self.data_target) + 0.009, str(self.volt[0]) + "Voltage")

        if save in "Y":
            fig.savefig("./{}/{}.png".format(path_save, name_save))

        plt.close()

    def IO_targetTrio(self, data, ref_dummy=0.01, rate=rate_NI):
        self.start_ref = datetime.now()
        self.data_target = []  # hola

        while True:

            trioT = gethermodes()
            trioT.InputChannels(self.volt)
            trioT.OutputChannels(self.volt)
            trioT.run(data)

            mean_trioT = np.mean(trioT.data, axis=1)

            if (
                data[0][0] > (mean_trioT[0] - ref_dummy)
                and data[0][0] < (mean_trioT[0] + ref_dummy)
                and data[1][0] > (mean_trioT[1] - ref_dummy)
                and data[1][0] < (mean_trioT[1] + ref_dummy)
                and data[2][0] > (mean_trioT[2] - ref_dummy)
                and data[2][0] < (mean_trioT[2] + ref_dummy)
            ):

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


######################## FUNCTIONS


def find_nearest(array, value):
    array = np.asarray(array)
    # print(array)
    # print(value)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
