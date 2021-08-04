import time
import pickle
import matplotlib.pyplot as plt

class Staircase():
    """
        Class to perform staircase
    """

    def __init__(self, total_reversals, initial, direction, name = '1'):
        self.reversals = 0
        self.first_ramp = True
        self.tracker = 0
        self.stimulation = initial
        self.tracked_stimulation = initial
        self.reversed_bool = False
        self.last_response = None
        self.trial = 1
        self.direction = direction
        self.total_reversals = total_reversals
        self.name = name

        self.reversal_values = []
        self.estimated_point = None

        self.list_stimulations = []
        self.list_tracked_stimulations = []

        self.list_to_plot = {0: {'trial': [], 'stimulation': []}, 1: {'trial': [], 'stimulation': []}}


    def __str__(self):
        return f'Name: {self.name}; Reversals: {self.reversals}; Tracker: {self.tracker}; Stimulation: {self.stimulation}; Tracked stimulation: {self.tracked_stimulation}'

    def saveStaircase(self, path_data, name_file):
        '''
            Pickle save your object staircase at each iteration so you can recover it if something fails
        '''
        backup_file = open(f"{path_data}/{name_file}.pkl", "wb")
        pickle.dump(self, backup_file)
        backup_file.close()

    def reversal(self, response):
        '''
            Check whether there's a reversal in the staircase after the last response
        '''
        self.response = response
        self.reversed_bool = False

        self.list_stimulations.append(self.stimulation)
        self.list_tracked_stimulations.append(self.tracked_stimulation)

        self.list_to_plot[self.response]['trial'].append(self.trial)
        self.list_to_plot[self.response]['stimulation'].append(self.stimulation)

        if self.last_response != response and self.last_response is not None:
            self.tracker = 0
            self.reversals += 1
            self.reversed_bool= True
            self.first_ramp = False
            self.reversal_values.append(self.stimulation)
            if not self.first_ramp and self.reversals == 1:
                print('\nTracking algorithm triggered\n')

    def XupYdownFixedStepSizesTrackingAlgorithm(self, move_down, move_up, step_down, step_up):
        '''
            Execute tracking algorithm for a stairse X UP / Y DOWN with fixed step sizes (but the length of the steps up and down can be of different size)
        '''
        self.tracker += 1

        if not self.first_ramp:
            if self.tracker == move_down and self.response == 1:
                self.tracked_stimulation = self.tracked_stimulation - step_down
                self.tracker = 0

            elif self.tracker == move_up and self.response == 0:
                self.tracked_stimulation = self.tracked_stimulation + step_up
                self.tracker = 0
        else:
            if self.direction == 'down' and self.response == 1:
                self.tracked_stimulation = self.tracked_stimulation - step_down
            elif self.direction == 'up' and self.response == 0:
                self.tracked_stimulation = self.tracked_stimulation  + step_up

    def clampBoundary(self, lower_boundary, upper_boundary):
        '''
            Apply carry-over boundary rule
        '''
        if self.tracked_stimulation > upper_boundary:
            self.stimulation = upper_boundary
        elif self.tracked_stimulation < lower_boundary:
            self.stimulation = lower_boundary
        else:
            self.stimulation = self.tracked_stimulation

    def estimateValue(self, drop_reversals = 3):
        '''
            Estimate the value based on the self.reversal_values list
        '''
        self.estimated_point = sum(self.reversal_values[drop_reversals:])/len(self.reversal_values[drop_reversals:])

    def plotStaircase(self, path_figs, name, ylabel, ylim, fig = None, ax = None):
        '''
            Plot staircase
        '''

        if not fig and not ax:
            fig, ax = plt.subplots(1)

        ax.plot(list(range(1, len(self.list_stimulations) + 1)), self.list_stimulations, color = 'k')
        ax.plot(list(range(1, len(self.list_tracked_stimulations) + 1)), self.list_tracked_stimulations, color = 'g')

        ax.scatter(self.list_to_plot[0]['trial'], self.list_to_plot[0]['stimulation'], color = 'red')
        ax.scatter(self.list_to_plot[1]['trial'], self.list_to_plot[1]['stimulation'], color = 'k')

        ax.axhline(self.estimated_point, color = 'k')

        ax.set_ylim(ylim)
        ax.set_ylabel(ylabel)
        ax.set_xlabel('Trials')

        plt.savefig(f'{path_figs}/{name}.png')

        plt.show()