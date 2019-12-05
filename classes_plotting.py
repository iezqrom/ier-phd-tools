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


class twoD(object):
    def __init__(self):

        pass


class threeD(object):
    def __init__(self):
        pass

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


####### ANIMATIONS
def aniThermalGraphs(data, vminT, vmaxT, path, name_file, start, title = '  '):

    Writer = animation.writers['ffmpeg']
    writer = Writer(fps = 8.7, metadata=dict(artist='Me'), bitrate=1800)

    def animate(i, data, plot):

        try:

            raw_dum = data.read['image'+str(i + start)][:]

            # First subplot: 3D RAW
            ax1.clear()
            plots1 = ax1.imshow(raw_dum, cmap='hot', vmin = vminT, vmax = vmaxT)

            ax1.set_title('{}'.format(title))

        except:
            print('Done')
    ################ Plot figure
    fig = plt.figure(figsize = (20, 10))

    #######################Axes
    ax1 = fig.add_subplot(111)

    x = np.arange(0,120,1)
    y = np.arange(0,160,1)

    xs, ys = np.meshgrid(x, y)
    zs = (xs*0 + 15) + (ys*0 + 15)


    ######################Plots
    ## First subplot: 3D RAW
    plot1 = ax1.imshow(zs, cmap='hot', vmin = vminT, vmax = vmaxT)
    cbar = fig.colorbar(plot1, ax = ax1)
    cbar.set_label('($^\circ$C)')

    #Animation & save
    ani = animation.FuncAnimation(fig, animate, frames = len(data.read.keys()), fargs = (data, plot1), interval=1000/8.7)

    ani.save('./{}/{}.mp4'.format(path, name_file), writer = writer)


def aniThermal3d(data, vminT, vmaxT, path, name_file, start, title = '  '):
    x = np.arange(0,160,1)
    y = np.arange(0,120,1)

    xs, ys = np.meshgrid(x, y)
    zs = (xs*0 + 15) + (ys*0 + 15)

    Writer = animation.writers['ffmpeg']
    writer = Writer(fps = 8.7, metadata=dict(artist='Me'), bitrate=1800)

    def animate(i, data, plot):

        try:
            zs = data.read['image'+str(i + start)][:]
            ax.clear()
            ax.set_zlim(vminT,vmaxT)
            plot = ax.plot_surface(xs, ys, zs, cmap='hot', vmin = vminT, vmax = vmaxT)
            ax.set_zlabel('($^\circ$C)')

        except:
            print('Done')


    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    plot = ax.plot_surface(xs, ys, zs, rstride=1, cstride=1, cmap='hot', vmin = vminT, vmax = vmaxT)
    cbar = fig.colorbar(plot)
    cbar.set_label('($^\circ$C)')

    ani = animation.FuncAnimation(fig, animate, frames = len(data.read.keys()), fargs = (data, plot), interval=1000/8.7)

    ani.save('./{}/{}.mp4'.format(path, name_file), writer = writer)

####### DECORATORS
def no_right_top_spines(function):

    @wraps(function)
    def wrapper(self = None, *args, **kwargs):
        # print(*args, **kwargs)
        print(function(self))
        fig, ax = function(self) #, *args, **kwargs)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

    return wrapper

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
