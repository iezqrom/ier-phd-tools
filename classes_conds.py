import numpy as np 
import random

class ConditionsHandler():
    
    def __init__(self, *conds):
        self.conditions = np.array(np.meshgrid(*conds)).T.reshape(-1,len(conds))
   
    def repeatition(self, n_repeats):
        self.random_repeats = np.repeat(self.conditions, n_repeats, axis = 0)
        np.random.shuffle(self.random_repeats)