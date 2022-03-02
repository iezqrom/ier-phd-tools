import numpy as np
import pickle
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from classes_text import delta_temperatre_T
import time


def power_law(x, a, b):
    return a * np.power(x, b)


class Scaling:
    """
    Class to perform scaling experiments
    """

    def __init__(self, trials_per_mag, magnitudes, start=0, end=4):
        self.start = start
        self.end = end
        self.scale = list(range(start, (end + 1)))
        self.magnitudes = magnitudes
        self.trials_per_mag = trials_per_mag
        self.magnitudes_done = []
        self.magnitudes_left = [self.magnitudes * self.trials_per_mag]
        # randomise

        assert len(self.scale) == len(
            self.magnitudes
        ), f"self.scale {len(self.scale)} and self.magnitudes {len(self.magnitudes)} are not the same length"

        self.trial = 0
        self.block = 0
        self.within_block_counter = 0
        self.within_block_successful = 0

        self.reversal_values = []
        self.estimated_point = None

        self.list_to_plot = {key: [] for key in list(range(start, (end + 1)))}
        self.power_fitted = False

    def __str__(self):
        return f"Trial: {self.trial}"

    @property
    def getResponses(self):
        return [
            np.mean(list_resp_mag) if str(np.mean(list_resp_mag)) != "nan" else 0
            for list_resp_mag in list(self.list_to_plot.values())
        ]

    def saveScaling(self, path_data, name_file):
        """
        Pickle save your object scaling at each iteration so you can recover it if something fails
        """
        backup_file = open(f"{path_data}/{name_file}.pkl", "wb")
        pickle.dump(self, backup_file)
        backup_file.close()

    def trackResponse(self, mag, response):
        """
        Track responses
        """
        self.list_to_plot[mag].append(response)

    def powerFit(self):
        """
        Fit power function to our data
        """
        self.pars, self.cov = curve_fit(
            f=power_law,
            xdata=self.magnitudes,
            ydata=self.getResponses,
            p0=[0, 0],
            bounds=(-np.inf, np.inf),
        )
        self.stdevs = np.sqrt(np.diag(self.cov))

        self.res = self.getResponses - power_law(self.magnitudes, *self.pars)
        self.res_squared = np.square(self.res)

        self.squared_diff_from_mean = np.square(
            self.getResponses - np.mean(self.getResponses)
        )
        self.r_squared = 1 - np.sum(self.res_squared) / np.sum(
            self.squared_diff_from_mean
        )

        self.y_data_fit = power_law(self.magnitudes, self.pars[0], self.pars[1])

        self.power_fitted = True

    def plotScaling(
        self,
        ylim,
        name,
        path_figs,
        ylabel="Perceived intensity",
        xlabel=delta_temperatre_T,
        fig=None,
        ax=None,
    ):
        """
        Plot staircase
        """
        if not fig and not ax:
            fig, ax = plt.subplots(1)

        ax.scatter(
            self.magnitudes,
            self.getResponses,
            color="k",
            marker="_",
            s=300,
            linewidths=5,
        )

        if self.power_fitted:
            ax.plot(self.magnitudes, self.y_data_fit, color="k", alpha=0.5)

        for ind, responses in enumerate(list(self.list_to_plot.values())):
            print(ind)
            print(responses)

            ax.scatter(
                np.repeat(self.magnitudes[ind], len(responses)),
                responses,
                color="k",
                alpha=0.5,
            )

        ax.set_ylim(ylim)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)

        plt.savefig(f"{path_figs}/{name}.png")
        plt.show()


## Logarithmic plot


class Anchoring:
    def __init__(self, anch_trials_per_mag):
        self.anch_trials_per_mag = anch_trials_per_mag

    def saveAnchoring(self, path_data, name_file):
        """
        Pickle save your object scaling at each iteration so you can recover it if something fails
        """
        backup_file = open(f"{path_data}/{name_file}.pkl", "wb")
        pickle.dump(self, backup_file)
        backup_file.close()


def delay_stimulus_offset_response(lower_bound_delay, higher_bound_delay):
    delay = np.random.uniform(lower_bound_delay, higher_bound_delay)
    time.sleep(delay)
    return delay
