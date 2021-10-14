#!/usr/bin/env python3

#Time
from datetime import datetime
import time
from time import sleep
#System
try:
    import sys
except:
    pass

try:
    import tty
except:
    pass

try:
    import termios
except:
    pass

import keyboard
try:
    import winsound
except:
    pass

# My stuff
try:
    import globals
except:
    pass

import re

# Maths
import numpy as np
import curses
from termios import TCIFLUSH, tcflush

class TextIO:
    def __init__(self):
        pass

    def intensity(self):

        while True:
            self.intense = input("\n From 0 to 10, how cold did that feel? (0 is no cold - 10 is painfully cold)  ")
            if self.intense in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'):
                break
            else:
                print('\n Only "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" and "10" are valid answers')
                continue

    def lowFam(self):
        while True:
            self.low_bound = input("\n What is the minimum temperature for COLTHER? ")
            try:
                self.low_bound = float(self.low_bound)
                break
            except:
                print("\n Only numbers are valid answers")
                continue

    def highFam(self):
        while True:
            self.high_bound = input("\n What is the maximum temperature for COLTHER? ")
            try:
                self.high_bound = float(self.high_bound)
                break
            except:
                print("\n Only numbers are valid answers")
                continue

    def amplitudeFam(self):
        while True:
            self.amplitude = input("\n What is the amplitude range for COLTHER?   ")
            try:
                self.amplitude = float(self.high_bound)/2
            except:
                print("\n Only numbers are valid answers")

    def CspotB(self):
        while True:
            self.Cwalle = input("\n Have we found a cold spot? (Y/n)   ")
            if self.Cwalle in ('Y', 'n'):
                break
            else:
                print("\n ")
                continue

    def printValues(self):
            while globals.status == None and globals.distance > globals.distance_limit and globals.elapsed < globals.time_limit:
                print('Temperature:  ' + str(globals.temp))
                print('Distance:  ' + str(globals.distance))

    def famOrder(self):
        while True:
            self.f_order = input("\n What spots are we finding first? (C / W)  ")
            if self.f_order in ('C', 'W'):
                break
            else:
                print("\n Only C and W are valid answers \n")
                continue

    def WspotB(self):
        while True:
            self.Wwalle = input("\n Have we found a warm spot? (Y/n)   ")
            if self.Wwalle in ('Y', 'n'):
                break
            else:
                print("\n ")
                continue

    def laserTfam(self):
        while True:
            self.laserT = input("\n At what temperature should the LASER be?    ")
            try:
                self.laserT = float(self.laserT)
                break
            except:
                print("\n Only numbers are valid answers")
                continue
    def TGIfam(self):
        while True:
            self.tgi_fam = input("\n Are we happy with the sensation? (Y/n)")
            if self.tgi_fam in ('Y', 'n'):
                break
            else:
                print("\n ")
                continue

    def famTGI(self):
        while True:
            self.famTGIs = input("\n What familiarisation step are we doing now? (C / W / TGI)  ")
            if self.famTGIs in ('C', 'W'):
                break
            else:
                print("\n Only C and W are valid answers \n")
                continue

    def spotTGIfam(self):
        while True:
            self.spot_TGIfam = input("What COLD spot would you like to choose? (C1/C2)")
            if self.spot_TGIfam in ('C1', 'C2'):
                break
            else:
                print("\n Only 'C1' and 'C2' are valid answers")
                continue


    def blocks(self):

        while True:
            self.n_blocks = input("\n How many blocks are we doing?  ")
            if self.n_blocks in ('1', '2', '3', '4', '5', '6'):
                self.n_blocks = int(self.n_blocks)
                break
            else:
                print("\n Only 1, 2, 3, 4, 5 and 6 are valid answers \n")
                continue

    def trials(self):

        while True:
            self.n_trials = input("\n How many trials are we doing?  ")
            try:
                self.n_trials = int(self.n_trials)
                break
            except:
                print("\n Only numbers are valid answers \n")
                continue

    def famStage(self):

        while True:
            self.BolStage = input("\n Are we doing the preparatory stage? (Y/n)  ")
            if self.BolStage in ('Y', 'n'):
                break
            else:
                print('\n Only "Y" and "n" are valid answers \n')
                continue
    def AFC(self):

        while True:
            self.decision = input("\n Which stimulus was oscillating? (Press 1 or 2. Then, press Enter)  ")
            if self.decision in ('1', '2'):
                globals.text_state += 1
                break
            else:
                print('\n Only 1 and 2 are valid answers \n')
                continue

    def AFCDummy(self):

        while True:
            self.decision_dummy = input("\n Which stimulus was oscillating? (Press 1 or 2. Then, press Enter)  ")
            if self.decision_dummy in ('1', '2'):
                globals.text_state += 1
                break
            else:
                print('\n Only 1 and 2 are valid answers \n')
                continue

    def subjectN(self):
        while True:
            self.subject_n = input("\n Subject number:  ")
            if self.subject_n in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'):
                break
            else:
                print('\n Only 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 are valid answers \n')
                continue

    def rangeTest(self):
        while True:
            self.range = input("\n What range are we testing? (warm/cold)  ")
            if self.range in ('warm', 'cold'):
                break
            else:
                print('\n Only "warm" and "cold" are valis answers \n')

    def meanOsc(self, range):
        while True:
            if range == 'warm':
                self.mean_warm = input("\n What is the mean temperature in the warm range?  ")
                try:
                    self.mean_warm = float(self.mean_warm)

                except:
                    print('\n Only numbers are valid answers \n')
                    continue

                break

            elif range == 'cold':
                self.mean_cold = input("\n What is the mean temperature in the cold range?  ")
                try:
                    self.mean_cold = float(self.mean_cold)

                except:
                    print('\n Only numbers are valid answers \n')
                    continue
                break

    def ampTemp(self):
        while True:
            self.amp_T = input("\n What is the amplitude tested?  ")
            try:
                self.amp_T = float(self.amp_T)
                try:
                    self.low_bound = self.mean_warm - self.amp_T/2
                    self.high_bound = self.mean_warm + self.amp_T/2
                except:
                    self.low_bound = self.mean_cold - self.amp_T/2
                    self.high_bound = self.mean_cold + self.amp_T/2
            except:
                print('\n Only numbers are valid answers \n')
                continue

            break

    def age(self):
        while True:
            self.agef = input("\n How old are you?  Type your answer and press enter    ")
            try:
                self.agef = float(self.agef)
                break

            except:
                print('\n Only numbers are valid answers \n')
                continue


    def TargetTemp(self):
        while True:
            self.target_temp= input("\n What temperature do we want to reach?    ")
            try:
                self.target_temp = float(self.target_temp)

            except:
                print('\n Only numbers are valid answers \n')
                continue

            break

    def breaks(self):

        while True:
            self.n_breaks = input("\n When are we taking breaks?  ")
            if self.n_breaks in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '15', '16', '17', '18', '19', '20'):
                self.n_breaks = int(self.n_breaks)
                break
            else:
                print("\n Only 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 and 20 are valid answers \n")
                continue

    def pracAns(self):

        while True:
            self.prac_ans = input('\n How did that feel? (constant or changing)  ')
            if self.prac_ans in ('constant', 'changing'):
                break
            else:
                print("\n Only constant or changing are valid answers")
                continue

    def famOp(self):

        while True:
            self.fam_op = input("\n What condition are we familiarising with? (c1 / c2 / c3)   ")
            if self.fam_op in ('c1', 'c2', 'c3', 'd'):
                break
            else:
                print("\n Only c1, c2, c3 or d are valid inputs")

    def counterB(self):

        while True:
            self.counter = input("\n What block are we doing first?   ")
            if self.counter in ('I', 'A'):
                break
            else:
                print("\n Only I and A valid inputs")

    def PracOp(self):

        while True:
            self.prac_op = input("\n Are we doing the practise trials? (y / n)   ")
            if self.prac_op in ('y', 'n'):
                break
            else:
                print("\n Only y and n are valid inputs")

########################################################################
########################## FUNCTIONS ##################################
########################################################################
def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

def waitForEnter(text):
    print(text)
    was_pressed = True

    while True:
        if keyboard.is_pressed('enter') and not was_pressed:
            break

        if not keyboard.is_pressed('enter'):
            was_pressed = False

def printme(text):
    """
        Quick function to print with space at the beginning and end
    """
    print(f'\n{text}\n')

def agebyExperimenter():
    while True:
        age_input = input('\n Ask the participants for their age and input it here: ')
        age_no_letters = re.sub(r"\D", "", age_input)
        try:
            age = int(age_no_letters[-2:])
            print(age)
            break

        except Exception as e:
            print(e)
            print('\n Only numbers are valid answers \n')
            continue

    return age

def scale_reponse(question, start = 0, end = 11):
    """
        Read participant responses for a scaling experiment
    """
    time_response_start = time.time()
    while True:
        tcflush(sys.stdin, TCIFLUSH)
        response = input(question)
        print('input', response)
        if response in [f'{i}' for i in range(start, end)]:
            break
        else:
            print(response)
            printme(f"\n Try again. Only {[f'{i}' for i in range(start, end)]} are accepted responses\n")
            continue

    print(response)
    time_response_end = time.time() - time_response_start

    return response, time_response_end


def binary_response(question, values = {'0': 'no', '1':'yes'}):
    """
        Read participant responses for a scaling experiment
    """
    time_response_start = time.time()
    while True:
        tcflush(sys.stdin, TCIFLUSH)
        response = input(question)
        print('input', type(response))
        if response in list(values.keys()):
            break
        else:
            print(response)
            printme(f"\n Try again. Only {list(values.keys())} are accepted responses\n")
            continue

    print(response)
    time_response_end = time.time() - time_response_start

    return response, time_response_end