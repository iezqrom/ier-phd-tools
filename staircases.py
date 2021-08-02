import pickle

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
        if self.last_response != response and self.last_response is not None:
            self.tracker = 0
            self.reversals += 1
            self.reversed_bool= True
            self.first_ramp = False
            if not self.first_ramp and self.reversals == 1:
                print('\nTracking algorithm triggered\n')

    def XupYdownFixedStepSizesTrackingAlgorithm(self, move_down, move_up, step_down, step_up):
        '''
            Execute tracking algorithm for a stairse X UP / Y DOWN with fixed step sizes (but the length of the steps up and down can be of different size)
        '''
        self.tracker += 1

        if not self.first_ramp:
            if self.tracker == move_down:
                self.tracked_stimulation = self.tracked_stimulation - step_down
                self.tracker = 0

            elif self.tracker == move_up:
                self.tracked_stimulation = self.tracked_stimulation + step_up
                self.tracker = 0
        else:
            if self.direction == 'down' and self.response == 1:
                self.tracked_stimulation = self.tracked_stimulation - step_down
            elif self.direction == 'up' and self.response == 0:
                self.tracked_stimulation = self.tracked_stimulation  + step_up

    def clampBoundary(self, upper_boundary, lower_boundary):
        '''
            Apply carry-over boundary rule
        '''
        if self.tracked_stimulation > upper_boundary:
            self.stimulation = upper_boundary
        elif self.tracked_stimulation < lower_boundary:
            self.stimulation = lower_boundary
        else:
            self.stimulation = self.tracked_stimulation