#!/usr/bin/env python3

### Data structure
from __future__ import print_function
import numpy as np
import ctypes
import struct
import h5py
import keyboard

## Media
import time
import cv2
from imutils.video import VideoStream
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation

## Comms
from uvctypes import *

try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform
# from pynput import keyboard
import os
import argparse
import imutils

try:
    import globals
except:
    pass

from functools import wraps


############################################################################################################
############################################################################################################
####### Functions
############################################################################################################
############################################################################################################

def framesToseconds(axis, steps, x):
    """
        Function to convert the x axis from frames to seconds:
        Parameters
            - Axis: name of the axis from the figure you want to change the x axis
            - Steps: 
            - x: the independent variable (x)
    """
    steps = steps
    #
    seconds = np.arange(0, round(len(x)/8.7*1, 2), round(10/8.7) * steps)
    frames = np.arange(0, len(x), 8.7 * steps)
    axis.xaxis.set_ticks(frames)

    labelsx = [item.get_text() for item in axis.get_xticklabels()]

    for j in enumerate(seconds):
        labelsx[j[0]] = int(j[1])

    axis.set_xticklabels(labelsx)

####### FITTING SINE
def guesses(data, phase, freq, amp):
    guess_mean = np.mean(data)
    guess_std = 3*np.std(data)/(2**0.5)/(2**0.5)
    guess_phase = math.pi/2
    guess_freq = freq
    guess_amp = amp

    params = [guess_mean, guess_std, guess_phase, guess_freq, guess_amp]
    return params

def estimates(params, data):

    data_first_guess = params[1]*np.sin(params[3]*np.arange(len(data))+params[2]) + params[0]

    optimize_func = lambda x: x[0]*np.sin(x[1] * np.arange(len(data)) + x[2]) + x[3] - data
    est_amp, est_freq, est_phase, est_mean = optimize.leastsq(optimize_func, [params[4], params[3], params[2], params[0]])[0]

    # recreate the fitted curve using the optimized parameters
    est_params = [est_amp, est_freq, est_phase, est_mean]
    data_fit = est_amp*np.sin(est_freq * np.arange(len(data)) + est_phase) + est_mean

    return data_first_guess, est_params, data_fit

############################################################################################################
####### DECORATORS
############################################################################################################
def no_right_top_spines(function):

    @wraps(function)
    def wrapper(self = None, *args, **kwargs):
        # print(*args, **kwargs)
        print(function(self))
        fig, ax = function(self) #, *args, **kwargs)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

    return wrapper
################################################################################################################################################
################################################################################################################################################
###### Trash
################################################################################################################################################
################################################################################################################################################
def frames_to_seconds(steps = None, data = None):
    # @wraps(function)
    def deco(function):
        @wraps(function)
        def wrapper(self = None, *args, **kwargs):
            # print(function)
            fig, ax = function(self, *args, **kwargs)

            seconds = np.arange(0, round(len(data)/8.7*1, 2), round(10/8.7) * steps)
            frames = np.arange(0, len(data), 8.7 * steps)
            ax.xaxis.set_ticks(frames)

            labelsx = [item.get_text() for item in ax.get_xticklabels()]

            for j in enumerate(seconds):
                labelsx[j[0]] = int(j[1])

            ax.set_xticklabels(labelsx)
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)

        return wrapper
    return deco

####################################################################################################################################################################################
####################################################################################################################################################################################
##### Plotting for experiments with thermodes
####################################################################################################################################################################################
####################################################################################################################################################################################

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



#################################################################################################
############################ Animation MASTER ####################################################
#################################################################################################

# aw3d = ReAnRaw('2cm_shutter')
#
# Writer = animation.writers['ffmpeg']
# writer = Writer(fps = 9, metadata=dict(artist='Me'), bitrate=1800)
#
# def animate(i, aw3d, plots, aucs, peaks, shutterOnOff, axes):
#     # print(i)
#     # print('image'+str(i)+'_open')
#     try:
#         raw_dum = aw3d.read['image'+str(i + 1)+'_open'][:]
#         state_shutter = 'open'
#
#         # ONE 1 is open
#     except KeyError:
#         raw_dum = aw3d.read['image'+str(i + 1)+'_close'][:]
#         state_shutter = 'close'
#
#     #Raw data
#     zs = (raw_dum - 27315) /100
#     zs = zs[60:120, 0:60]
#
#     #Gaussian
#     maxC = 32
#     zsG = abs(zs - maxC)
#     Xin, Yin = np.mgrid[0:60, 0:60]
#     paramsGau = fitgaussian(zsG)
#     dataGau = gaussian(*paramsGau)(Xin, Yin)
#     dataGau_con = gaussian(*paramsGau)
#
#     # First subplot: 3D RAW
#     ax1.clear()
#     # axes[0] = fig.add_subplot(2, 2, 1, projection = '3d')
#     plots1 = ax1.plot_surface(Xin, Yin, zs, rstride=1, cstride=1, cmap='hot', vmin = 15, vmax = 33)
#     ax1.text(50, 10, 20, state_shutter, color='black', fontsize = 12, weight = 'bold')
#
#     ax1.set_title('3D raw data')
#     ax1.set_zlabel('Celsius degrees')
#     ax1.set_zlim(15,33)
#
#     # Second subplot: 3D Gaussian
#     ax2.clear()
#     plots[1] = ax2.plot_surface(Xin, Yin, dataGau, rstride=1, cstride=1, cmap='hot', vmin = 0)
#     ax2.text(50, 10, 20, state_shutter, color='black', fontsize = 12, weight = 'bold')
#
#     ax2.set_title('3D Gaussian')
#     ax2.set_zlabel('Gaussian-transformed temperature')
#     ax2.set_zlim(0,10)
#
#     # Third subplot: Contour + Gaussian fit
#     ax3.clear()
#     # ax3 = fig.add_subplot(2, 2, 3, projection = '3d')
#     plots[2] = ax3.matshow(zs, cmap='hot')
#     ax3.contour(dataGau_con(*np.indices(zs.shape)), cmap=plt.cm.copper)
#     (height, x, y, width_x, width_y) = paramsGau
#
#     ax3.text(0.95, 0.05, """
#     height : %.1f
#     width_x : %.1f
#     width_y : %.1f""" %(height, width_x, width_y),
#             fontsize=16, horizontalalignment='right',
#             verticalalignment='bottom', transform=ax3.transAxes)
#
#     # Fourth subplot: Peak + AUC
#     ax4.clear()
#     ax5.clear()
#     # ax4 = fig.add_subplot(2, 2, 4)
#
#     ######## AUC info
#     auc = np.sum(np.trapz(dataGau, axis = 1))
#
#     normed = (auc - mean_aucs)/std_aucs
#
#     norm_auc_abs = normed - min(norm_aucs)
#
#     aucs[i] = norm_auc_abs
#
#     ########## Peak info
#     peak = paramsGau[0]
#     peak =  32 + 0 - peak
#     peaks[i] = peak
#
#     plots[3] = ax4.plot(np.arange(len(peaks)), peaks, lw = 6)
#     ax4.yaxis.set_ticks(np.arange(14.5, 30.6, 1))
#
#     peaks_fill = np.nan_to_num(peaks)
#     aucs_fill = np.nan_to_num(aucs)
#
#     # print(peaks_fill)
#     # print(aucs_fill)
#
#     ax4.fill_between(np.arange(len(peaks)), peaks, y2=peaks_fill + aucs_fill, color='k', alpha = 0.5)
#     ax4.fill_between(np.arange(len(peaks)), peaks, y2=peaks_fill - aucs_fill, color='k', alpha = 0.5)
#
#     ax4.set_title('Peak of Gaussian (blue line) + AUC (width line)')
#     ax4.set_ylabel('Peak of Gaussian Celsius degrees')
#     ax4.set_xlabel('Seconds')
#
#     plots[4] = ax5.plot(np.arange(len(shutterOnOff_cropped)), shutterOnOff_cropped, color='k')
#
#     ax5.set_ylim([0, 1.1])
#     ax4.set_ylim([15, 31])
#     ax5.set_ylabel('Shutter state')
#     ax5.yaxis.set_ticks(np.arange(0, 1, 0.9999))
#     labelsy2 = [item.get_text() for item in ax5.get_yticklabels()]
#     labelsy2[0] = 'close'
#     labelsy2[1] = 'open'
#     ax5.set_yticklabels(labelsy2)
#
#
#     frames = np.arange(0, len(aw3d.read.keys()), 1)
#     seconds = np.arange(0, len(aw3d.read.keys()), 1)
#
#     ax5.xaxis.set_ticks(frames)
#     ax5.yaxis.set_ticks(np.arange(14.5, 30.6, 1))
#
#     labelsx = [item.get_text() for item in ax5.get_xticklabels()]
#
#     for j in enumerate(seconds):
#         labelsx[j[0]] = j[1]
#
#     ax5.set_xticklabels(labelsx)
