import csv
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter  # Counter counts the number of occurrences of each item
from itertools import tee, count
import string
import scipy.stats as stats
import seaborn as sns
import math
import re
import os
import itertools


class ParseDirectos(object):
    """
    A class to extract 'direct' imotion data from csv files
    """

    def __init__(self, path, file, sep=","):
        self.read = pd.read_csv(f"./{path}/{file}.csv", sep=sep)
        self.cropread = self.read.iloc[25:-2, :]
        self.readhead = self.cropread.rename(columns=self.read.iloc[24])

        self.stringified_columns = [
            x.lower().replace(" ", "_") for x in list(self.readhead.columns)
        ]
        uniquify(self.stringified_columns, (f"_{x!s}" for x in string.ascii_lowercase))

        self.readhead.columns = self.stringified_columns
        self.dataframe = self.readhead.set_index("row")
        self.cuadrar = False
        self.fps = 30

    def extractSingle(self, tosingle):
        self.tosingle = tosingle
        self.temp_single_list = []

        for n_ts in self.tosingle:
            self.temp_single_list.append(self.dataframe[n_ts].iloc[1])

        try:
            self.dataframe = self.dataframe.drop(self.tosingle, axis=1)
        except Exception as e:
            print(e)
            print("You maybe have deleted that row already")

    def shiftCuadrar(self):
        if not self.cuadrar:
            self.dataframe = self.dataframe.shift(-4)
            self.dataframe = self.dataframe.shift(1, fill_value=0)
            self.dataframe = self.dataframe.iloc[:-3]
            # self.dataframe = self.dataframe.apply(pd.to_numeric)
        else:
            print("This method was already ran once")

        self.cuadrar = True

    def dropToDict(self, todrop):
        for i in todrop:
            try:
                self.dataframe = self.dataframe.drop(i, axis=1)
            except Exception as e:
                print(e)
                print("You maybe have deleted that row already")

    def allToDict(self):
        self.dataframe = self.dataframe.apply(pd.to_numeric)
        self.data = self.dataframe.to_dict("list")

    def injectToDict(self):
        if self.temp_single_list:
            for i, n_ts in enumerate(self.tosingle):
                self.data[n_ts] = float(self.temp_single_list[i])

    def featureToDict(self, sub="feature", time="timestamp"):
        self.features = {}
        for k, v in self.data.items():
            if k.find(sub) != -1:
                self.features[k] = v

        self.features[time] = self.data[time]

    def emotionToDict(self, sub="_a", time="timestamp"):
        self.emotions = {}
        for k, v in self.data.items():
            if k.find(sub) != -1:
                subitems = k.split("_")
                self.emotions[subitems[0]] = v

        self.emotions[time] = self.data[time]
        self.emotions["valence"] = self.data["valence"]

    def aucToDict(self, sub="_b", time="timestamp"):
        self.aucs = {}
        for k, v in self.data.items():
            if k.find(sub) != -1:
                subitems = k.split("_")
                self.aucs[subitems[0]] = v

        self.aucs[time] = self.data[time]

    def headToDict(self, time="timestamp"):
        self.nameshead = ["pitch", "yaw", "roll", "interocular_distance"]
        self.headpos = {}

        for nhp in self.nameshead:
            self.headpos[nhp] = self.data[nhp]

        self.headpos[time] = self.data[time]


#### PARSING FUNCTIONS
def uniquify(seq, suffs=count(1)):
    """
    Make all the items unique by adding a suffix (1, 2, etc).

    `seq` is mutable sequence of strings.
    `suffs` is an optional alternative suffix iterable.
    """
    not_unique = [
        k for k, v in Counter(seq).items() if v > 1
    ]  # so we have: ['name', 'zip']
    # suffix generator dict - e.g., {'name': <my_gen>, 'zip': <my_gen>}
    suff_gens = dict(zip(not_unique, tee(suffs, len(not_unique))))
    for idx, s in enumerate(seq):
        try:
            suffix = str(next(suff_gens[s]))
        except KeyError:
            # s was unique
            continue
        else:
            seq[idx] += suffix


def chunkify(signal, chunk_duration, fps=30):
    """
    Function to chunk imotion direct data into windows in seconds
    """
    print(f"\nChunking a list into windows of {chunk_duration} seconds each\n")
    length_chunk = chunk_duration * fps
    print(f"\nThe signal is {round(len(signal)/fps, 4)} seconds long")

    rows_array = math.ceil(len(signal) / length_chunk)
    tofill = np.zeros((rows_array, length_chunk))

    for i, chu in enumerate(range(0, len(signal), length_chunk)):
        try:
            tofill[i, :] = signal[chu : chu + length_chunk]
        except Exception as e:
            lastin = np.pad(
                signal[chu : chu + length_chunk],
                (0, (length_chunk - len(signal[chu : chu + length_chunk]))),
            )
            tofill[i, :] = lastin

    return tofill


def thresholdNbinarise(chunked_signal, threshold=50):
    """
    Function to threshold and binarise the signal (this is meant to replicate what the emotion does when you manually select the intervals to binarise).
    The signal has to be chunked by the chunkify function OR
    the signal must be in an array, in which each row is an interval
    """
    thresholded_binarised_array = []
    for n in chunked_signal:
        boolean_threshold = n > 50
        boolean_threshold.sum()

        temp_perc_time = boolean_threshold.sum() / len(n)

        thresholded_binarised_array.append(temp_perc_time)

    return thresholded_binarised_array


def thresholdNmean(chunked_signal, threshold=50):
    thresholded = np.where(
        chunked_signal > threshold, chunked_signal, 0 * chunked_signal
    )
    thresholdNmeaned = np.mean(thresholded, axis=1)

    return thresholdNmeaned


#### PLOTTING FUNCTIONS
def framesTominutes(axis, steps, x):
    """
    Function to convert the x axis from frames to seconds:
    Parameters
        - Axis: name of the axis from the figure you want to change the x axis
        - Steps:
        - x: the independent variable (x)
    """
    steps = steps
    hz = 30

    minutes = np.arange(0, len(x) / hz / 60, steps / 60)
    frames = np.arange(0, len(x), hz * steps)
    axis.xaxis.set_ticks(frames)
    labelsx = [item.get_text() for item in axis.get_xticklabels()]

    for j in enumerate(minutes):
        labelsx[j[0]] = int(j[1])

    axis.set_xticklabels(labelsx)


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """
    return [atoi(c) for c in re.split(r"(\d+)", text)]


def getNames(path, pattern):
    patternc = re.compile(pattern)
    names = []
    for filename in os.listdir(f"{path}"):
        if patternc.match(filename):
            print(filename)
            name, form = filename.split(".")
            names.append(name)
        else:
            continue

    names.sort(key=natural_keys)
    return names


def runningMean(signal, window, fps=30):
    """
    Running mean. Parameters are the size of the window. At each step the window moves one frame.
    The boundary rules is to create a buffer at the beginning and end. The values in the buffer are the start/end value.
    """
    size_window = window * fps

    if size_window % 2 == 0:
        size_window += 1
        print("Even number of frames")
    else:
        print("Odd number of frames")

    index_centre_window = math.ceil(size_window / 2) - 1
    size_pad = math.floor(size_window / 2)

    start_pad = [signal[0]] * size_pad
    end_pad = [signal[-1]] * size_pad

    padded_list = list(itertools.chain(start_pad, signal, end_pad))

    runned_list = []
    for index in range(len(signal)):
        window_data = padded_list[index : int((size_window + index))]
        runned_list.append(np.mean(window_data))

    return runned_list
