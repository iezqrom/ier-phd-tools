import numpy as np

class TestingDataHandler():
    def __init__(self, parameters, *conds):    
        self.conditions = np.array(np.meshgrid(*conds)).T.reshape(-1,len(conds))
        self.data = {}
        self.parameters = parameters
        for entry in self.conditions:
            condname = '.'.join(entry)
            paras = {}
            for p in parameters:
                paras['{}'.format(p)] = []
            self.data[condname] = paras
    
    def TrialAppend(self, trial_data, *conds):
        # Save data to data library
        condname = '.'.join([*conds])
 
        for i in np.arange(len(trial_data)):
            self.data[condname][self.parameters[i]].append(trial_data[i])