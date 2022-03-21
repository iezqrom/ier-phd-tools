#!/usr/bin/env python3

### Data structure
from __future__ import print_function
import numpy as np

import math

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
    seconds = np.arange(0, round(len(x) / 8.7 * 1, 2), round(10 / 8.7) * steps)
    frames = np.arange(0, len(x), 8.7 * steps)
    axis.xaxis.set_ticks(frames)

    labelsx = [item.get_text() for item in axis.get_xticklabels()]
    # print(seconds)
    # time.sleep(2)
    for j in enumerate(seconds):
        labelsx[j[0]] = int(j[1])

    axis.set_xticklabels(labelsx)


####### FITTING SINE
def guesses(data, phase, freq, amp):
    guess_mean = np.mean(data)
    guess_std = 3 * np.std(data) / (2 ** 0.5) / (2 ** 0.5)
    guess_phase = math.pi / 2
    guess_freq = freq
    guess_amp = amp

    params = [guess_mean, guess_std, guess_phase, guess_freq, guess_amp]
    return params


def estimates(params, data):

    data_first_guess = (
        params[1] * np.sin(params[3] * np.arange(len(data)) + params[2]) + params[0]
    )

    optimize_func = (
        lambda x: x[0] * np.sin(x[1] * np.arange(len(data)) + x[2]) + x[3] - data
    )
    est_amp, est_freq, est_phase, est_mean = optimize.leastsq(
        optimize_func, [params[4], params[3], params[2], params[0]]
    )[0]

    # recreate the fitted curve using the optimized parameters
    est_params = [est_amp, est_freq, est_phase, est_mean]
    data_fit = est_amp * np.sin(est_freq * np.arange(len(data)) + est_phase) + est_mean

    return data_first_guess, est_params, data_fit


############################################################################################################
####### DECORATORS
############################################################################################################
def no_right_top_spines(function):
    @wraps(function)
    def wrapper(self=None, *args, **kwargs):
        # print(*args, **kwargs)
        print(function(self))
        fig, ax = function(self)  # , *args, **kwargs)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

    return wrapper


################################################################################################################################################
################################################################################################################################################
###### Trash
################################################################################################################################################
################################################################################################################################################
def frames_to_seconds(steps=None, data=None):
    # @wraps(function)
    def deco(function):
        @wraps(function)
        def wrapper(self=None, *args, **kwargs):
            # print(function)
            fig, ax = function(self, *args, **kwargs)

            seconds = np.arange(
                0, round(len(data) / 8.7 * 1, 2), round(10 / 8.7) * steps
            )
            frames = np.arange(0, len(data), 8.7 * steps)
            ax.xaxis.set_ticks(frames)

            labelsx = [item.get_text() for item in ax.get_xticklabels()]

            for j in enumerate(seconds):
                labelsx[j[0]] = int(j[1])

            ax.set_xticklabels(labelsx)
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)

        return wrapper

    return deco
