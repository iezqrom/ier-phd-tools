#!/usr/bin/env python3
import numpy as np
import math
from functools import wraps
import matplotlib.pyplot as plt

pad_size_label = 20
pad_size_ticks = 10
width_lines = 10
length_ticks = 20
scatter_size = 300
alpha_partici = 0.1
width_participants = 6

nt_color = "#0F4C81"
t_color = "#B59A48"
degree_sign = u'\N{DEGREE SIGN}'
def plotParams(colour = "black"):
    plt.rcParams.update(
        {
            "font.size": 40,
            "axes.labelcolor": f"{colour}",
            "xtick.color": f"{colour}",
            "ytick.color": f"{colour}",
            "font.family": "sans-serif",
        }
    )

def removeSpines(ax, sides = ["top", "right"]):
    for side in sides:
        ax.spines[side].set_visible(False)

def setTickShape(ax, width_lines, length_ticks):
    ax.yaxis.set_tick_params(width=width_lines, length=length_ticks)
    ax.xaxis.set_tick_params(width=width_lines, length=length_ticks)

def setSpinesWidth(ax, width_lines):
    ax.spines["left"].set_linewidth(width_lines)
    ax.spines["bottom"].set_linewidth(width_lines)

def setTicksPad(ax, gap):
    ax.tick_params(axis="y", which="major", pad=gap)
    ax.tick_params(axis="x", which="major", pad=gap)



############################################################################################################
####### Functions PhD
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
