import pickle
import matplotlib.pyplot as plt
import time
import numpy as np
import random


class Staircase:
    """
    Class to perform staircase
    """

    def __init__(
        self, total_reversals, initial, direction, rules_direction=1, name="1"
    ):
        self.reversals = 0
        self.first_ramp = True
        self.tracker = 0
        self.stimulation = initial
        self.tracked_stimulation = initial
        self.reversed_bool = False
        self.last_response = None
        self.trial = 0
        self.direction = direction
        self.total_reversals = total_reversals
        self.name = name
        self.block = 1
        self.within_block_counter = 0
        self.within_block_successful_counter = 0
        self.rules_direction = rules_direction
        self.force_reverse = False

        self.reversal_values = []
        self.estimated_point = None

        self.list_stimulations = []
        self.list_tracked_stimulations = []

        self.list_to_plot = {
            0: {"trial": [], "stimulation": []},
            1: {"trial": [], "stimulation": []},
        }

    def __str__(self):
        return f"Name: {self.name}; Reversals: {self.reversals}; Tracker: {self.tracker}; Stimulation: {self.stimulation}; Tracked stimulation: {self.tracked_stimulation}"

    def saveStaircase(self, path_data, name_file):
        """
        Pickle save your object staircase at each iteration so you can recover it if something fails
        """
        backup_file = open(f"{path_data}/{name_file}.pkl", "wb")
        pickle.dump(self, backup_file)
        backup_file.close()

    def reversal(self, response):
        """
        Check whether there's a reversal in the staircase after the last response
        """
        self.response = response
        self.reversed_bool = False

        self.list_stimulations.append(self.stimulation)
        self.list_tracked_stimulations.append(self.tracked_stimulation)

        self.list_to_plot[self.response]["trial"].append(self.trial)
        self.list_to_plot[self.response]["stimulation"].append(self.stimulation)

        # print('force_reverse', self.force_reverse)

        if (
            self.last_response != response
            and self.last_response is not None
            or self.force_reverse == True
        ):
            self.tracker = 0
            self.reversals += 1
            self.reversed_bool = True
            self.first_ramp = False
            self.reversal_values.append(self.stimulation)
            if (
                not self.first_ramp
                and self.reversals == 1
                or self.force_reverse == True
            ):
                print("\nTracking algorithm triggered\n")

    def XupYdownFixedStepSizesTrackingAlgorithm(
        self, move_down, move_up, step_down, step_up, step_first_reversal = 0
    ):
        """
        Execute tracking algorithm for a stairse X UP / Y DOWN with fixed step sizes (but the length of the steps up and down can be of different size)
        """
        self.tracker += 1

        if not self.first_ramp:
            if self.tracker == move_down and self.response == 1:
                if self.rules_direction == 1:
                    self.tracked_stimulation = self.tracked_stimulation - step_down
                elif self.rules_direction == 0:
                    self.tracked_stimulation = self.tracked_stimulation + step_up
                self.tracker = 0

            elif self.tracker == move_up and self.response == 0:
                if self.rules_direction == 1:
                    self.tracked_stimulation = self.tracked_stimulation + step_up
                elif self.rules_direction == 0:
                    self.tracked_stimulation = self.tracked_stimulation - step_down
                self.tracker = 0
        else:
            if self.direction == "down":
                if self.response == 1:
                    if self.rules_direction == 0:
                        self.tracked_stimulation = (
                            self.tracked_stimulation + step_first_reversal
                        )
                    elif self.rules_direction == 1:
                        self.tracked_stimulation = (
                            self.tracked_stimulation - step_first_reversal
                        )
                elif self.response == 0:
                    if self.rules_direction == 0:
                        self.tracked_stimulation = (
                            self.tracked_stimulation - step_up
                        )
                    elif self.rules_direction == 1:
                        self.tracked_stimulation = (
                            self.tracked_stimulation + step_up
                        )
                    self.first_ramp = False

            elif self.direction == "up":
                if self.response == 0:
                    if self.rules_direction == 0:
                        self.tracked_stimulation = (
                            self.tracked_stimulation - step_first_reversal
                        )
                    elif self.rules_direction == 1:
                        self.tracked_stimulation = (
                            self.tracked_stimulation + step_first_reversal
                        )
                elif self.response == 1:
                    if self.rules_direction == 0:
                        self.tracked_stimulation = (
                            self.tracked_stimulation + step_down
                        )
                    elif self.rules_direction == 1:
                        self.tracked_stimulation = (
                            self.tracked_stimulation - step_down
                        )

                    self.first_ramp = False

    def clampBoundary(self, lower_boundary, upper_boundary):
        """
        Apply carry-over boundary rule
        """
        if self.tracked_stimulation > upper_boundary:
            self.stimulation = upper_boundary
        elif self.tracked_stimulation < lower_boundary:
            self.stimulation = lower_boundary
        else:
            self.stimulation = self.tracked_stimulation

    def estimateValue(self, drop_reversals=3):
        """
        Estimate the value based on the self.reversal_values list
        """
        self.estimated_point = sum(self.reversal_values[drop_reversals:]) / len(
            self.reversal_values[drop_reversals:]
        )

    def plotStaircase(
        self,
        path_figs,
        name,
        ylabel,
        ylim,
        fig=None,
        ax=None,
        lwd=4,
        pad_size=5,
        lenD=7,
        show=True,
        colour=None
    ):
        """
        Plot staircase
        """
        mc = "black"
        plt.rcParams.update(
            {
                "font.size": 20,
                "axes.labelcolor": "{}".format(mc),
                "xtick.color": "{}".format(mc),
                "ytick.color": "{}".format(mc),
                "font.family": "sans-serif",
            }
        )

        if not fig and not ax:
            fig, ax = plt.subplots(1)

        if colour is None:
            colour = "black"

        ax.plot(
            list(range(1, len(self.list_stimulations) + 1)),
            self.list_stimulations,
            color=colour,
        )
        ax.plot(
            list(range(1, len(self.list_tracked_stimulations) + 1)),
            self.list_tracked_stimulations,
            color="g",
        )

        ax.scatter(
            [x + 1 for x in self.list_to_plot[0]["trial"]],
            self.list_to_plot[0]["stimulation"],
            color="red",
        )
        ax.scatter(
            [x + 1 for x in self.list_to_plot[1]["trial"]],
            self.list_to_plot[1]["stimulation"],
            color=colour,
        )

        ax.axhline(self.estimated_point, color=colour)

        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.spines["left"].set_linewidth(lwd)
        ax.spines["bottom"].set_linewidth(lwd)
        ax.yaxis.set_tick_params(width=lwd, length=lenD)
        ax.xaxis.set_tick_params(width=lwd, length=lenD)
        ax.tick_params(axis="y", which="major", pad=pad_size)
        ax.tick_params(axis="x", which="major", pad=pad_size)

        ax.set_title(f"{name}", pad=pad_size)
        ax.set_ylim(ylim)
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Trials")

        plt.tight_layout()

        plt.savefig(f"{path_figs}/{change_space_to_underscore(name)}.png")

        if show:
            plt.show()

    def __round__(self):
        return str(round(self.stimulation * 100))


def delay_stimulus_offset_response(lower_bound_delay, higher_bound_delay):
    delay = np.random.uniform(lower_bound_delay, higher_bound_delay)
    time.sleep(delay)
    return delay


def choose_staircase(staircases):
    valid_choice = False
    while not valid_choice:
        trial_staircase = random.choice(list(staircases.keys()))
        if (
            staircases[trial_staircase][0].reversals
            == staircases[trial_staircase][0].total_reversals
        ) and (
            staircases[trial_staircase][1].reversals
            == staircases[trial_staircase][1].total_reversals
        ):
            continue
        else:
            valid_choice = True
        return trial_staircase

def choose_substaircase(staircases):
    valid_choice = False
    while not valid_choice:
        trial_staircase = random.choice(list(staircases.keys()))
        if (
            staircases[trial_staircase].reversals
            == staircases[trial_staircase].total_reversals
        ):
            continue
        else:
            valid_choice = True
        return trial_staircase

# function to change space to underscore and small letters
def change_space_to_underscore(string):
    return string.replace(" ", "_").lower()
