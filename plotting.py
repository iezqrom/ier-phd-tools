#!/usr/bin/env python3
import numpy as np
import math
from functools import wraps
import matplotlib.pyplot as plt
import scipy

params_figure = {
    "scatter_size": 400,
    "width_lines": 9,
    "width_spines": 5,
    "length_ticks": 20,
    "pad_size_ticks": 10,
    "pad_size_label": 20,
    "alpha": 0.5,
    "adjust_parti_line": 5,
    "width_ticks": 5
}


colours = {
    'cold': "#0F4C81",
    'cold_touch': "#B59A48",
    'none': "#000000",
    'touch': "#417743",
    'sound': "#47c6a3", #'#757a4e'
}

degree_sign = u'\N{DEGREE SIGN}'

path_thesis = '/Users/ivan/Documents/aaa_online_stuff/research/phd_2018_2023/aaa_phd/comms/thesis/figures/'
path_figures = "../../globalfigures/thesis"

def plotParams(colour = "black", size = 15):
    plt.rcParams.update(
        {
            "font.size": size,
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

def prettifySpinesTicks(ax, width_ticks = params_figure['width_lines'], length_ticks = params_figure['length_ticks'], width_spines = params_figure['width_lines'], pad_size_ticks = params_figure['pad_size_ticks'], pad_size_label = params_figure['pad_size_label'], colour = 'lightgrey'):
    ax.yaxis.set_tick_params(width=width_ticks, length=length_ticks, color=colour)
    ax.xaxis.set_tick_params(width=width_ticks, length=length_ticks, color=colour)

    for spine in ax.spines.values():
        spine.set_edgecolor(colour)

    for spine in ax.spines.values():
        spine.set_linewidth(width_spines)

    ax.tick_params(axis="y", which="major", pad=pad_size_ticks)
    ax.tick_params(axis="x", which="major", pad=pad_size_ticks)
    
    ax.xaxis.labelpad = pad_size_label
    ax.yaxis.labelpad = pad_size_label

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

# function to calculate the effect size
def cohenD(group1, group2):
    diff = np.mean(group1) - np.mean(group2)

    n1, n2 = len(group1), len(group2)
    # calculate variance of a list
    var1 = np.var(group1)
    var2 = np.var(group2)

    pooled_var = (n1 * var1 + n2 * var2) / (n1 + n2)
    d = diff / np.sqrt(pooled_var)

    return d

############################################################################################################
####### Thesis figures
############################################################################################################
def percCorrectPlot(data, cond, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    ax.scatter(
        np.repeat(0, len(data[f"{cond}-correct-present-notouch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-present-notouch"]],
        s=params_figure["scatter_size"],
        color=colours["cold"],
        clip_on=False
    )
    ax.scatter(
        np.repeat(1, len(data[f"{cond}-correct-absent-notouch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-absent-notouch"]],
        s=params_figure["scatter_size"],
        color=colours["cold"],
        clip_on=False
    )

    ax.scatter(
        np.repeat(3, len(data[f"{cond}-correct-present-touch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-present-touch"]],
        s=params_figure["scatter_size"],
        color=colours["cold_touch"],
        clip_on=False
    )
    ax.scatter(
        np.repeat(4, len(data[f"{cond}-correct-absent-touch"])),
        [data_point*100 for data_point in data[f"{cond}-correct-absent-touch"]],
        s=params_figure["scatter_size"],
        color=colours["cold_touch"],
        clip_on=False
    )

    m_cpnt = np.mean(data[f"{cond}-correct-present-notouch"]) * 100
    m_cant = np.mean(data[f"{cond}-correct-absent-notouch"]) * 100

    m_cpt = np.mean(data[f"{cond}-correct-present-touch"]) * 100
    m_cat = np.mean(data[f"{cond}-correct-absent-touch"]) * 100


    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [m_cpnt, m_cpnt], color=colours["cold"], lw=params_figure["width_lines"])
    ax.plot([1 - offset, 1 + offset], [m_cant, m_cant], color=colours["cold"], lw=params_figure["width_lines"])

    ax.plot([3 - offset, 3 + offset], [m_cpt, m_cpt], color=colours["cold_touch"], lw=params_figure["width_lines"])
    ax.plot([4 - offset, 4 + offset], [m_cat, m_cat], color=colours["cold_touch"], lw=params_figure["width_lines"])

    # for i, dd in enumerate(data[f"{cond}-correct-present-touch"]):
    ax.plot(
        [0, 1, 3, 4],
        [
            [data_point*100 for data_point in data[f"{cond}-correct-present-notouch"]],
            [data_point*100 for data_point in data[f"{cond}-correct-absent-notouch"]],
            [data_point*100 for data_point in data[f"{cond}-correct-present-touch"]],
            [data_point*100 for data_point in data[f"{cond}-correct-absent-touch"]],
        ],
        color="grey",
        lw=params_figure["width_lines"] - params_figure["adjust_parti_line"],
        alpha=params_figure["alpha"],
        zorder=0
    )

    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("Percentage of correct responses (%)", labelpad=params_figure["pad_size_label"])

    ax.set_ylim([0, 100])

    ax.set_xticks([0, 1, 3, 4])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    labels[0] = "Cooling"
    labels[1] = "No cooling"

    labels[2] = "Cooling & touch"
    labels[3] = "Touch"

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
        np.repeat(0, len(data[f"{cond}-hr-notouch-loglinear"])),
        data[f"{cond}-hr-notouch-loglinear"],
        s=params_figure["scatter_size"],
        color=colours["cold"],
        clip_on=False
    )
    ax.scatter(
        np.repeat(1, len(data[f"{cond}-fa-notouch-loglinear"])),
        data[f"{cond}-fa-notouch-loglinear"],
        s=params_figure["scatter_size"],
        color=colours["cold"],
        clip_on=False
    )

    ax.scatter(
        np.repeat(3, len(data[f"{cond}-hr-touch-loglinear"])),
        data[f"{cond}-hr-touch-loglinear"],
        s=params_figure["scatter_size"],
        color=colours["cold_touch"],
        clip_on=False
    )
    ax.scatter(
        np.repeat(4, len(data[f"{cond}-fa-touch-loglinear"])),
        data[f"{cond}-fa-touch-loglinear"],
        s=params_figure["scatter_size"],
        color=colours["cold_touch"],
        clip_on=False
    )

    m_hrt = np.mean(data[f"{cond}-hr-touch-loglinear"])
    m_fat = np.mean(data[f"{cond}-fa-touch-loglinear"])

    m_hrnt = np.mean(data[f"{cond}-hr-notouch-loglinear"])
    m_fant = np.mean(data[f"{cond}-fa-notouch-loglinear"])

    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [m_hrnt, m_hrnt], color=colours["cold"], lw=params_figure["width_lines"])
    ax.plot([1 - offset, 1 + offset], [m_fant, m_fant], color=colours["cold"], lw=params_figure["width_lines"])

    ax.plot([3 - offset, 3 + offset], [m_hrt, m_hrt], color=colours["cold_touch"], lw=params_figure["width_lines"])
    ax.plot([4 - offset, 4 + offset], [m_fat, m_fat], color=colours["cold_touch"], lw=params_figure["width_lines"])

    # for i, dd in enumerate(data[f"{cond}-hr-touch-loglinear"]):
    ax.plot(
        [0, 1, 3, 4],
        [
            data[f"{cond}-hr-notouch-loglinear"],
            data[f"{cond}-fa-notouch-loglinear"],
            data[f"{cond}-hr-touch-loglinear"],
            data[f"{cond}-fa-touch-loglinear"],
        ],
        color="grey",
        lw=params_figure["width_lines"] - params_figure["adjust_parti_line"],
        alpha=params_figure["alpha"],
        zorder=0
    )

    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("Rate", labelpad=params_figure["pad_size_label"])

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
        np.repeat(0, len(data[f"{cond}-d-prime-notouch"])),
        data[f"{cond}-d-prime-notouch"],
        s=params_figure["scatter_size"],
        color=colours["cold"],
    )

    ax.scatter(
        np.repeat(1, len(data[f"{cond}-d-prime-touch"])),
        data[f"{cond}-d-prime-touch"],
        s=params_figure["scatter_size"],
        color=colours["cold_touch"],
    )

    md_notouch = np.mean(data[f"{cond}-d-prime-notouch"])
    md_touch = np.mean(data[f"{cond}-d-prime-touch"])

    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [md_notouch, md_notouch], lw=params_figure["width_lines"], color=colours["cold"])
    ax.plot([1 - offset, 1 + offset], [md_touch, md_touch], lw=params_figure["width_lines"], color=colours["cold_touch"])

    # for i, dd in enumerate(data[f"{cond}-d-prime-touch"]):
    ax.plot(
        [0, 1],
        [data[f"{cond}-d-prime-notouch"], data[f"{cond}-d-prime-touch"]],
        color="grey",
        lw=params_figure["width_lines"] - params_figure["adjust_parti_line"],
        alpha=params_figure["alpha"],
        zorder=0
    )

    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("Sensitivity (d')", labelpad=params_figure["pad_size_label"])
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
        np.repeat(0, len(data[f"{cond}-c-response-notouch"])),
        data[f"{cond}-c-response-notouch"],
        s=params_figure["scatter_size"],
        color=colours["cold"],
    )
    ax.scatter(
        np.repeat(1, len(data[f"{cond}-c-response-touch"])),
        data[f"{cond}-c-response-touch"],
        s=params_figure["scatter_size"],
        color=colours["cold_touch"],
    )

    mc_notouch = np.mean(data[f"{cond}-c-response-notouch"])
    mc_touch = np.mean(data[f"{cond}-c-response-touch"])

    offset = 0.2
    ax.plot([0 - offset, 0 + offset], [mc_notouch, mc_notouch], color=colours["cold"], lw=params_figure["width_lines"])
    ax.plot([1 - offset, 1 + offset], [mc_touch, mc_touch], color=colours["cold_touch"], lw=params_figure["width_lines"])

    # for i, dd in enumerate(data[f"{cond}-c-response-touch"]):
    ax.plot(
        [0, 1],
        [data[f"{cond}-c-response-notouch"], data[f"{cond}-c-response-touch"]],
        color="grey",
        lw=params_figure["width_lines"] - params_figure["adjust_parti_line"],
        alpha=params_figure["alpha"],
        zorder=0
    )

    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("Bias (c)", labelpad=params_figure["pad_size_label"])

    ax.set_ylim([-1.5, 1.5])

    ax.set_xticks([])
    ax.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])

    plt.tight_layout()

    ax.text(
        -0.4,
        1.1,
        "'Yes'",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="black",
        fontsize=45,
    )

    ax.text(
        -0.4,
        -0.15,
        "'No'",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="black",
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
            np.repeat((i), len(data[f"{cond}-d-prime-notouch"])),
            data[f"{cond}-d-prime-notouch"],
            s=params_figure["scatter_size"],
            color=colours["cold"],
        )

        ax.scatter(
            np.repeat((i + 0.5), len(data[f"{cond}-d-prime-touch"])),
            data[f"{cond}-d-prime-touch"],
            s=params_figure["scatter_size"],
            color=colours["cold_touch"],
        )

        md_notouch = np.mean(data[f"{cond}-d-prime-notouch"])
        md_touch = np.mean(data[f"{cond}-d-prime-touch"])

        offset = 0.1
        ax.plot([i - offset, i + offset], [md_notouch, md_notouch], lw=params_figure["width_lines"], color=colours["cold"])
        ax.plot(
            [(i + 0.5) - offset, (i + 0.5) + offset],
            [md_touch, md_touch],
            lw=params_figure["width_lines"],
            color=colours["cold_touch"],
        )

        ax.plot(
            [i, (i + 0.5)],
            [data[f"{cond}-d-prime-notouch"], data[f"{cond}-d-prime-touch"]],
            color="grey",
            lw=params_figure["width_lines"] - params_figure["adjust_parti_line"],
            alpha=params_figure["alpha"],
            zorder=0
        )

    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("Sensitivity (d')", labelpad=params_figure["pad_size_label"])
    ax.set_ylim([0, 3.5])

    ax.set_xlim([-0.2, 2.7])

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
            np.repeat(i, len(data[f"{cond}-c-response-notouch"])),
            data[f"{cond}-c-response-notouch"],
            s=params_figure["scatter_size"],
            color=colours["cold"],
        )
        ax.scatter(
            np.repeat((i + 0.5), len(data[f"{cond}-c-response-touch"])),
            data[f"{cond}-c-response-touch"],
            s=params_figure["scatter_size"],
            color=colours["cold_touch"],
        )

        md_notouch = np.mean(data[f"{cond}-c-response-notouch"])
        md_touch = np.mean(data[f"{cond}-c-response-touch"])

        offset = 0.1
        ax.plot(
            [i - offset, i + offset],
            [md_notouch, md_notouch],
            lw=params_figure["width_lines"],
            color=colours["cold"]
        )
        ax.plot(
            [(i + 0.5) - offset, (i + 0.5) + offset],
            [md_touch, md_touch],
            lw=params_figure["width_lines"],
            color=colours["cold_touch"],
        )

        ax.plot(
            [i, (i + 0.5)],
            [data[f"{cond}-c-response-notouch"], data[f"{cond}-c-response-touch"]],
            color="grey",
            lw=params_figure["width_lines"] - params_figure["adjust_parti_line"],
            alpha=params_figure["alpha"],
            zorder=0
        )

    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("Response bias (C)", labelpad=params_figure["pad_size_label"])
    ax.set_ylim([-1.5, 1.5])
    ax.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])
    ax.set_xticks([0.25, 1.25, 2.25])
    ax.set_xlim([-0.2, 2.7])

    # horizontal line at 0
    ax.axhline(y=0, color="grey", alpha=0.5, linestyle = "--", lw = params_figure["width_lines"] - params_figure["adjust_parti_line"])

    labels = [item.get_text() for item in ax.get_xticklabels()]

    for idx, label in enumerate(labels):
        labels[idx] = name_labels[idx]

    ax.set_xticklabels(labels)

    ax.text(
        -0.16,
        0.9,
        "'Yes'",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="k",
        fontsize=45,
    )

    ax.text(
        -0.16,
        0.05,
        "'No'",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="k",
        fontsize=45,
    )

    doubleSave(name, thesis_expt_path)

def diffPlotD(data, conditions, name, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    offset = 0.1
    all_diffs = []
    x_for_diffs = []
    for index, condition in enumerate(conditions.values()):
        ax.plot([index + 0.25 - offset, index + 0.25 + offset],
                [data[f"{condition}-d-prime-diffs-mean"], data[f"{condition}-d-prime-diffs-mean"]],
                color="black",
                lw=params_figure["width_lines"],
                )
        ax.scatter(np.repeat(index + 0.25, len(data[f"{condition}-d-prime-diffs"])), data[f"{condition}-d-prime-diffs"], s=params_figure["scatter_size"], color="black", clip_on=False)
        
        x_for_diffs.append(index + 0.25)
        all_diffs.append(data[f"{condition}-d-prime-diffs"])
    
    ax.plot(x_for_diffs, all_diffs, color="grey", lw=params_figure["width_lines"] - params_figure["adjust_parti_line"], alpha=params_figure["alpha"], zorder=0)
    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("(Cold d') - (Cold & touch d')", labelpad=params_figure["pad_size_label"])
    ax.set_ylim([-2, 2])
    ax.set_yticks(np.arange(-2, 2.1, 0.5))
    ax.set_xlim([-0.2, 2.7])

    ax.axhline(y=0, color="grey", alpha=0.5, linestyle = "--", lw = params_figure["width_lines"] - params_figure["adjust_parti_line"])

    ax.set_xticks([0.25, 1.25, 2.25])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    data[f"{condition}-d-prime-diffs"]

    for idx, label in enumerate(conditions.values()):
        # capitalise first letter
        labels[idx] = label.capitalize()

    ax.set_xticklabels(labels)

    doubleSave(name, thesis_expt_path)

def diffPlotC(data, conditions, name, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(20, 15))

    offset = 0.1
    all_diffs = []
    x_for_diffs = []
    for index, condition in enumerate(conditions.values()):
        ax.plot([index + 0.25 - offset, index + 0.25 + offset],
                [data[f"{condition}-c-response-diffs-mean"], data[f"{condition}-c-response-diffs-mean"]],
                color="black",
                lw=params_figure["width_lines"],
                )
        ax.scatter(np.repeat(index + 0.25, len(data[f"{condition}-c-response-diffs"])), data[f"{condition}-c-response-diffs"], s=params_figure["scatter_size"], color="black", clip_on=False)
        
        x_for_diffs.append(index + 0.25)
        all_diffs.append(data[f"{condition}-c-response-diffs"])
    
    ax.plot(x_for_diffs, all_diffs, color="grey", lw=params_figure["width_lines"] - params_figure["adjust_parti_line"], alpha=params_figure["alpha"], zorder=0)
    removeSpines(ax)
    prettifySpinesTicks(ax, params_figure["width_lines"], params_figure["length_ticks"], params_figure["width_lines"], params_figure["pad_size_ticks"])

    ax.set_ylabel("(Cold C) - (Cold & touch C)", labelpad=params_figure["pad_size_label"])
    ax.set_ylim([-1.5, 1.5])
    ax.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])
    ax.set_xlim([-0.2, 2.7])

    ax.axhline(y=0, color="grey", alpha=0.5, linestyle = "--", lw = params_figure["width_lines"] - params_figure["adjust_parti_line"])

    ax.text(
        -0.16,
        0.9,
        "'Yes'",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="k",
        fontsize=45,
    )

    ax.text(
        -0.16,
        0.05,
        "'No'",
        verticalalignment="bottom",
        horizontalalignment="left",
        transform=ax.transAxes,
        color="k",
        fontsize=45,
    )

    ax.set_xticks([0.25, 1.25, 2.25])
    labels = [item.get_text() for item in ax.get_xticklabels()]

    for idx, label in enumerate(conditions.values()):
        labels[idx] = label.capitalize()

    ax.set_xticklabels(labels)

    doubleSave(name, thesis_expt_path)

def exampleStaircase(staircase, low_bound_yaxis, high_bound_xaxis, clamps, thesis_expt_path, experiment_name, zero_indexed=False, steps_yaxis=0.2):
    
    darkdark = "#28282D"
    dark = "#615c61"
    fail = '#E4445E'
    fail_not_used = '#f4b6c0'
    green = "#476A30"
    end_color = "#84A295"

    staircase.estimateValue()
    print(round(staircase.estimated_point, 2))

    fig, ax = plt.subplots(1, 1, figsize=(20, 15))
    # staircase.plotStaircase(path_figures, "staircase", "Delta", [0, 3], fig = fig, ax = ax, show=False)

    if zero_indexed:
        index_correction = 1
    else:
        index_correction = 0
    failed_used_trials = [x + index_correction for x in staircase.list_to_plot[0]["trial"][3:]]
    failed_used_stimulations = staircase.list_to_plot[0]["stimulation"][3:]
    ax.scatter(
        failed_used_trials,
        makeNegative(failed_used_stimulations),
        color = fail,
        s = params_figure["scatter_size"],
        zorder = 10,
    )

    failed_notused_trials = [x + index_correction for x in staircase.list_to_plot[0]["trial"][:3]]
    failed_notused_stimulations = staircase.list_to_plot[0]["stimulation"][:3]
    ax.scatter(
        failed_notused_trials,
        makeNegative(failed_notused_stimulations),
        color = fail_not_used,
        s=params_figure["scatter_size"],
        zorder = 10,
        # alpha = 0.6
    )

    ax.scatter(
        [x + index_correction for x in staircase.list_to_plot[1]["trial"]],
        makeNegative(staircase.list_to_plot[1]["stimulation"]),
        color = dark,
        s = params_figure["scatter_size"],
        zorder =10,
    )

    ax.scatter(
        staircase.list_to_plot[0]['trial'][-1] + index_correction,
        -staircase.list_to_plot[0]['stimulation'][-1],
        color=fail,
        s=params_figure["scatter_size"],
        zorder=10,
    )

    ax.plot(
        list(range(1, len(staircase.list_stimulations) + 1)),
        makeNegative(staircase.list_stimulations),
        color=darkdark,
        alpha = 0.5,
        lw=params_figure["width_lines"] - 2,
    )
    ax.plot(
        list(range(1, len(staircase.list_tracked_stimulations) + 1)),
        makeNegative(staircase.list_tracked_stimulations),
        color= green,
        alpha = 0.5,
        lw=params_figure["width_lines"] - 2,
    )

    ax.axhline(-staircase.estimated_point,
            color=darkdark,
            alpha = 0.5,
            lw=params_figure["width_lines"] - params_figure["adjust_parti_line"],
            linestyle="--",)

    ax.axhline(clamps[0], color = 'black', alpha = 0.5, linewidth = params_figure["width_lines"]- params_figure["adjust_parti_line"])
    ax.axhline(clamps[1], color = 'black', alpha = 0.5, linewidth = params_figure["width_lines"]- params_figure["adjust_parti_line"])

    ax.set_ylim([low_bound_yaxis, 0])
    ax.set_yticks(np.arange(low_bound_yaxis, 0.01, steps_yaxis))

    ax.set_xlim([0, high_bound_xaxis])
    ax.set_xticks(np.arange(0, high_bound_xaxis + 0.01, 10))

    ax.set_xlabel("Trials")
    ax.set_ylabel("Relative temperature decrease\n\n(ΔT $^\circ$C)", linespacing=0.6)

    removeSpines(ax)
    prettifySpinesTicks(ax)
    plotParams()
    filename = f"staircase_example_{experiment_name}"
    doubleSave(filename, thesis_expt_path)

# start figure
def plotAllStaircases(deltas_data, low_bound_yaxis, high_bound_yaxis, steps_yaxis, clamps, thesis_expt_path):
    fig, ax = plt.subplots(1, 1, figsize=(6, 15))

    # jitter x axis
    x = np.random.normal(1, 0.03, size=len(deltas_data))
    ax.scatter(list(x), deltas_data, s = params_figure["scatter_size"], color = colours['cold'])

    # mean all deltals
    mean_delta = np.mean(deltas_data)
    ax.plot([0.95, 1.05], [mean_delta, mean_delta], color = colours['cold'], linewidth = params_figure["width_lines"])

    removeSpines(ax)
    prettifySpinesTicks(ax)

    # remove x ticks and labels
    ax.set_xticks([])
    ax.set_xlim([0.85, 1.2])

    ax.set_ylim([low_bound_yaxis, high_bound_yaxis])
    ax.set_yticks(np.arange(low_bound_yaxis, (high_bound_yaxis + 0.01), steps_yaxis))

    # horizontal line at 0
    ax.axhline(clamps[0], color = 'black', alpha = 0.5, linewidth = params_figure["width_lines"]- params_figure["adjust_parti_line"])
    ax.axhline(clamps[1], color = 'black', alpha = 0.5, linewidth = params_figure["width_lines"]- params_figure["adjust_parti_line"])

    ax.set_ylabel("Percent-correct point\n\n(ΔT $^\circ$C)", linespacing=0.6)

    # y ticks every 0.5
    # ax.set_title(f"Staircase {participant}")
    filename = "all_staircases"
    doubleSave(filename, thesis_expt_path)

############################################################################################################
####### Functions PhD
############################################################################################################

def framesToseconds(axis, steps, x, num_format=int):
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
        labelsx[j[0]] = num_format(j[1])

    axis.set_xticklabels(labelsx)

def meanSD(data):
    mean = np.mean(data)
    sd = np.std(data)
    return round(mean, 4), round(sd, 2)

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

def makeNegative(l):
    negative = [-x for x in l]
    return negative



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
