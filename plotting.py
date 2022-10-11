#!/usr/bin/env python3
import numpy as np
import math
from functools import wraps
import matplotlib.pyplot as plt
import scipy

pad_size_label = 20
pad_size_ticks = 10

width_spines = 5

width_lines = 9

length_ticks = 20
width_ticks = 5

scatter_size = 300
alpha_partici = 0.1

adjust_parti_line = 4

nt_color = "#0F4C81"
t_color = "#B59A48"
none_color = "#000000"
only_touch_color = "#417743"

degree_sign = u'\N{DEGREE SIGN}'

path_thesis = '/Users/ivan/Documents/aaa_online_stuff/phd_2018_2023/aaa_phd/comms/thesis/figures'
path_figures = "../../globalfigures/thesis"

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

def prettifySpinesTicks(ax, colour = 'grey'):
    ax.yaxis.set_tick_params(width=width_ticks, length=length_ticks, color=colour)
    ax.xaxis.set_tick_params(width=width_ticks, length=length_ticks, color=colour)

    for spine in ax.spines.values():
        spine.set_edgecolor(colour)

    for spine in ax.spines.values():
        spine.set_linewidth(width_spines)

    ax.tick_params(axis="y", which="major", pad=pad_size_ticks)
    ax.tick_params(axis="x", which="major", pad=pad_size_ticks)

def doubleSave(name, thesis_expt_path):
    plt.savefig(f"{path_figures}/{name}.svg", transparent=True, dpi=300)
    plt.savefig(f"{path_thesis}/{thesis_expt_path}/{name}.svg", transparent=True, dpi=300)

def saveStatsFigure(func, thesis_expt_path, name):
    # save result from func in a text file in the thesis thesis_expt_path folder with name
    with open(f"{path_thesis}/{thesis_expt_path}/stats_{name}.txt", "w") as f:
        f.write(f"{type(func).__name__}\n")
        f.write(str(func))
    # close the file
    f.close()

############################################################################################################
####### Thesis figures
############################################################################################################
def percCorrectPlot(data, cond, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    ax.scatter(
        np.repeat(0, len(data[f"{cond}-correct-present-touch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-present-touch"]],
        s=scatter_size,
        color=t_color,
        clip_on=False
    )
    ax.scatter(
        np.repeat(1, len(data[f"{cond}-correct-absent-touch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-absent-touch"]],
        s=scatter_size,
        color=only_touch_color,
        clip_on=False
    )
    ax.scatter(
        np.repeat(2, len(data[f"{cond}-correct-present-notouch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-present-notouch"]],
        s=scatter_size,
        color=nt_color,
        clip_on=False
    )
    ax.scatter(
        np.repeat(3, len(data[f"{cond}-correct-absent-notouch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-absent-notouch"]],
        s=scatter_size,
        color=none_color,
        clip_on=False
    )

    m_cpt = np.mean(data[f"{cond}-correct-present-touch"]) * 100
    m_cat = np.mean(data[f"{cond}-correct-absent-touch"]) * 100

    m_cpnt = np.mean(data[f"{cond}-correct-present-notouch"]) * 100
    m_cant = np.mean(data[f"{cond}-correct-absent-notouch"]) * 100

    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [m_cpt, m_cpt], color=t_color, lw=width_lines)
    ax.plot([1 - offset, 1 + offset], [m_cat, m_cat], color=only_touch_color, lw=width_lines)
    ax.plot([2 - offset, 2 + offset], [m_cpnt, m_cpnt], color=nt_color, lw=width_lines)
    ax.plot([3 - offset, 3 + offset], [m_cant, m_cant], color=none_color, lw=width_lines)

    for i, dd in enumerate(data[f"{cond}-correct-present-touch"]):
        ax.plot(
            [0, 1, 2, 3],
            [
                [data_point*100 for data_point in data[f"{cond}-correct-present-touch"]],
                [data_point*100 for data_point in data[f"{cond}-correct-absent-touch"]],
                [data_point*100 for data_point in data[f"{cond}-correct-present-notouch"]],
                [data_point*100 for data_point in data[f"{cond}-correct-absent-notouch"]],
            ],
            color="k",
            lw=width_lines - adjust_parti_line,
            alpha=alpha_partici,
            zorder=0
        )

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Percent correct (%)", labelpad=pad_size_label)

    ax.set_ylim([0, 100])

    ax.set_xticks([0, 1, 2, 3])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    labels[0] = "Cold + Touch"
    labels[1] = "Touch"
    labels[2] = "Cold"
    labels[3] = "None"

    ax.set_xticklabels(labels)

    plt.tight_layout()

    name = f"perc_correct_{cond}_derma"
    doubleSave(name, thesis_expt_path)
    saveStatsFigure(
                scipy.stats.ttest_rel(
            data[f"{cond}-correct-present-notouch"],
            data[f"{cond}-correct-present-touch"],
            alternative="greater",
        ),
        thesis_expt_path,
        name
    )

def hrFsPlot(data, cond, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    ax.scatter(
        np.repeat(0, len(data[f"{cond}-hr-touch-loglinear"])),
        data[f"{cond}-hr-touch-loglinear"],
        s=scatter_size,
        color=t_color,
        clip_on=False
    )
    ax.scatter(
        np.repeat(1, len(data[f"{cond}-fa-touch-loglinear"])),
        data[f"{cond}-fa-touch-loglinear"],
        s=scatter_size,
        color=only_touch_color,
        clip_on=False
    )
    ax.scatter(
        np.repeat(3, len(data[f"{cond}-hr-notouch-loglinear"])),
        data[f"{cond}-hr-notouch-loglinear"],
        s=scatter_size,
        color=nt_color,
        clip_on=False
    )
    ax.scatter(
        np.repeat(4, len(data[f"{cond}-fa-notouch-loglinear"])),
        data[f"{cond}-fa-notouch-loglinear"],
        s=scatter_size,
        color=none_color,
        clip_on=False
    )

    m_hrt = np.mean(data[f"{cond}-hr-touch-loglinear"])
    m_fat = np.mean(data[f"{cond}-fa-touch-loglinear"])

    m_hrnt = np.mean(data[f"{cond}-hr-notouch-loglinear"])
    m_fant = np.mean(data[f"{cond}-fa-notouch-loglinear"])

    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [m_hrt, m_hrt], color=t_color, lw=width_lines)
    ax.plot([1 - offset, 1 + offset], [m_fat, m_fat], color=only_touch_color, lw=width_lines)
    ax.plot([3 - offset, 3 + offset], [m_hrnt, m_hrnt], color=nt_color, lw=width_lines)
    ax.plot([4 - offset, 4 + offset], [m_fant, m_fant], color=none_color, lw=width_lines)

    for i, dd in enumerate(data[f"{cond}-hr-touch-loglinear"]):
        ax.plot(
            [0, 1, 3, 4],
            [
                data[f"{cond}-hr-touch-loglinear"],
                data[f"{cond}-fa-touch-loglinear"],
                data[f"{cond}-hr-notouch-loglinear"],
                data[f"{cond}-fa-notouch-loglinear"],
            ],
            color="k",
            lw=width_lines - adjust_parti_line,
            alpha=alpha_partici,
            zorder=0
        )

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Rate", labelpad=pad_size_label)

    ax.set_ylim([0, 1])

    ax.set_xticks([0, 1, 3, 4])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    labels[0] = "Hit\nrate"
    labels[1] = "False alarm\nrate"
    labels[2] = "Hit\nrate"
    labels[3] = "False alarm\nrate"

    ax.set_xticklabels(labels)

    plt.tight_layout()

    name = f"hr_fa_{cond}_derma"
    doubleSave(name, thesis_expt_path)
    saveStatsFigure(
        scipy.stats.ttest_rel(
            data[f"{cond}-hr-notouch-loglinear"],
            data[f"{cond}-hr-touch-loglinear"],
            alternative="greater",
        ),
        thesis_expt_path,
        name
    )

def dPrimePlot(data, cond, thesis_expt_path):
    print(cond.upper())
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    ax.scatter(
        np.repeat(0, len(data[f"{cond}-d-prime-touch"])),
        data[f"{cond}-d-prime-touch"],
        s=scatter_size,
        color=t_color,
    )
    ax.scatter(
        np.repeat(1, len(data[f"{cond}-d-prime-notouch"])),
        data[f"{cond}-d-prime-notouch"],
        s=scatter_size,
        color=nt_color,
    )

    md_notouch = np.mean(data[f"{cond}-d-prime-notouch"])
    md_touch = np.mean(data[f"{cond}-d-prime-touch"])

    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [md_touch, md_touch], lw=width_lines, color=t_color)
    ax.plot([1 - offset, 1 + offset], [md_notouch, md_notouch], lw=width_lines, color=nt_color)

    for i, dd in enumerate(data[f"{cond}-d-prime-touch"]):
        ax.plot(
            [0, 1],
            [data[f"{cond}-d-prime-touch"], data[f"{cond}-d-prime-notouch"]],
            color="k",
            lw=width_lines - adjust_parti_line,
            alpha=alpha_partici,
            zorder=0
        )

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Sensitivity (d')", labelpad=pad_size_label)
    # ax.set_xlabel('Time (s)', labelpad=20)
    ax.set_ylim([0, 3.5])

    ax.set_xticks([])

    plt.tight_layout()

    name = f"d_prime_{cond}_derma"
    doubleSave(name, thesis_expt_path)
    saveStatsFigure(
        scipy.stats.ttest_rel(
            data[f"{cond}-d-prime-notouch"],
            data[f"{cond}-d-prime-touch"],
            alternative="greater",
        ),
        thesis_expt_path,
        name
    )

def responseBiasPlot(data, cond, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    ax.scatter(
        np.repeat(0, len(data[f"{cond}-c-response-touch"])),
        data[f"{cond}-c-response-touch"],
        s=scatter_size,
        color=t_color,
    )
    ax.scatter(
        np.repeat(1, len(data[f"{cond}-c-response-notouch"])),
        data[f"{cond}-c-response-notouch"],
        s=scatter_size,
        color=nt_color,
    )

    mc_notouch = np.mean(data[f"{cond}-c-response-notouch"])
    mc_touch = np.mean(data[f"{cond}-c-response-touch"])

    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [mc_touch, mc_touch], color=t_color, lw=width_lines)
    ax.plot([1 - offset, 1 + offset], [mc_notouch, mc_notouch], color=nt_color, lw=width_lines)

    for i, dd in enumerate(data[f"{cond}-c-response-touch"]):
        ax.plot(
            [0, 1],
            [data[f"{cond}-c-response-touch"], data[f"{cond}-c-response-notouch"]],
            color="k",
            lw=width_lines - adjust_parti_line,
            alpha=alpha_partici,
            zorder=0
        )

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Bias (c)", labelpad=pad_size_label)

    ax.set_ylim([-1.5, 1.5])

    ax.set_xticks([])
    ax.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])

    plt.tight_layout()

    ax.text(
        -0.4,
        1.1,
        "Yes",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="red",
        fontsize=45,
    )

    ax.text(
        -0.4,
        -0.15,
        "No",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="red",
        fontsize=45,
    )

    name = f"response_bias_{cond}"
    doubleSave(name, thesis_expt_path)
    saveStatsFigure(
        scipy.stats.ttest_rel(
            data[f"{cond}-c-response-notouch"],
            data[f"{cond}-c-response-touch"]
        ),
        thesis_expt_path,
        name
    )

def ianettiPlotD(data, conditions, name_labels, name, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    for i, cond in enumerate(conditions.values()):

        ax.scatter(
            np.repeat(i, len(data[f"{cond}-d-prime-touch"])),
            data[f"{cond}-d-prime-touch"],
            s=scatter_size,
            color=t_color,
        )
        ax.scatter(
            np.repeat((i + 0.5), len(data[f"{cond}-d-prime-notouch"])),
            data[f"{cond}-d-prime-notouch"],
            s=scatter_size,
            color=nt_color,
        )

        md_notouch = np.mean(data[f"{cond}-d-prime-notouch"])
        md_touch = np.mean(data[f"{cond}-d-prime-touch"])

        offset = 0.1
        ax.plot([i - offset, i + offset], [md_touch, md_touch], lw=width_lines, color=t_color)
        ax.plot(
            [(i + 0.5) - offset, (i + 0.5) + offset],
            [md_notouch, md_notouch],
            lw=width_lines,
            color=nt_color,
        )

        for un_ied, dd in enumerate(data[f"{cond}-d-prime-touch"]):
            ax.plot(
                [i, (i + 0.5)],
                [data[f"{cond}-d-prime-touch"], data[f"{cond}-d-prime-notouch"]],
                color="k",
                lw=width_lines - adjust_parti_line,
                alpha=alpha_partici,
                zorder=0
            )

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Sensitivity (d')", labelpad=pad_size_label)
    ax.set_ylim([0, 3.5])

    ax.set_xticks([0.25, 1.25, 2.25])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    for idx, label in enumerate(labels):
        labels[idx] = name_labels[idx]

    ax.set_xticklabels(labels)

    doubleSave(name, thesis_expt_path)

def ianettiPlotC(data, conditions, name_labels, name, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    for i, cond in enumerate(conditions.values()):

        ax.scatter(
            np.repeat(i, len(data[f"{cond}-c-response-touch"])),
            data[f"{cond}-c-response-touch"],
            s=scatter_size,
            color=t_color,
        )
        ax.scatter(
            np.repeat((i + 0.5), len(data[f"{cond}-c-response-notouch"])),
            data[f"{cond}-c-response-notouch"],
            s=scatter_size,
            color=nt_color,
        )

        md_notouch = np.mean(data[f"{cond}-c-response-notouch"])
        md_touch = np.mean(data[f"{cond}-c-response-touch"])

        offset = 0.1
        ax.plot([i - offset, i + offset], [md_touch, md_touch], lw=width_lines, color=t_color)
        ax.plot(
            [(i + 0.5) - offset, (i + 0.5) + offset],
            [md_notouch, md_notouch],
            lw=width_lines,
            color=nt_color,
        )

        for un_ied, dd in enumerate(data[f"{cond}-c-response-touch"]):
            ax.plot(
                [i, (i + 0.5)],
                [data[f"{cond}-c-response-touch"], data[f"{cond}-c-response-notouch"]],
                color="k",
                lw=width_lines - adjust_parti_line,
                alpha=alpha_partici,
                zorder=0
            )

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Response bias (c)", labelpad=pad_size_label)
    ax.set_ylim([-1.5, 1.5])
    ax.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])
    ax.set_xticks([0.25, 1.25, 2.25])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    for idx, label in enumerate(labels):
        labels[idx] = name_labels[idx]

    ax.set_xticklabels(labels)

    ax.text(
        -0.16,
        1.1,
        "Yes",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="red",
        fontsize=45,
    )

    ax.text(
        -0.16,
        -0.15,
        "No",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="red",
        fontsize=45,
    )

    doubleSave(name, thesis_expt_path)

def diffPlotD(dfs, name_labels, name, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    ax.plot([0.25, 1.25, 2.25], dfs, color="k", lw=width_lines)

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Cold d' - (Cold + Touch) d'", labelpad=pad_size_label)
    ax.set_ylim([-0.1, 0.5])
    ax.set_yticks([-0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5])

    ax.set_xticks([0.25, 1.25, 2.25])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    for idx, label in enumerate(labels):
        labels[idx] = name_labels[idx]

    ax.set_xticklabels(labels)

    doubleSave(name, thesis_expt_path)

def diffPlotC(dfs, name_labels, name, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    ax.plot([0.25, 1.25, 2.25], dfs, color="k", lw=width_lines)

    removeSpines(ax)
    prettifySpinesTicks(ax)

    ax.set_ylabel("Cold response bias - (Cold + Touch) response bias", labelpad=pad_size_label)
    ax.set_ylim([-1.5, 1.5])
    ax.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])

    ax.set_xticks([0.25, 1.25, 2.25])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    for idx, label in enumerate(labels):
        labels[idx] = name_labels[idx]

    ax.set_xticklabels(labels)

    doubleSave(name, thesis_expt_path)
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
