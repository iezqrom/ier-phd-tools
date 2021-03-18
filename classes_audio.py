#!/usr/bin/env python3

try:
    import winsound
except:
    # print('This is not a Windows device')
    import simpleaudio as sa

import numpy as np
import time
import math
import globals

class Sound(object):
    def __init__(self, freq, duration):

        self.frequency = freq # Our played note will be 440 Hz
        self.fs = 44100  # 44100 samples per second
        self.seconds = duration  

        # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
        t = np.linspace(0, self.seconds, int(math.ceil(self.seconds * self.fs)), False)

        # Generate a 440 Hz sine wave
        self.note = np.sin(self.frequency * t * 2 * np.pi)

        # Ensure that highest value is in 16-bit range
        self.audio = self.note * (2**15 - 1) / np.max(np.abs(self.note))
        # Convert to 16-bit data
        self.audio = self.audio.astype(np.int16)

        print(f"\nObject audio initiliased\n")

    def play(self, event = None):
        try:
            if event != None:
                event.wait()
                # time.sleep(1)
            # Start playback
            self.play_obj = sa.play_buffer(self.audio, 1, 2, self.fs)
            print(f"\nTONE ON\n")
            
            if event != None:
                event.clear()
                
            # Logic to terminate sound while in thread
            # print('HEREEEEE')
            if event != None:
                event.wait()
                sa.stop_all()
                print(f"\nTone OFF\n")

        except Exception as e:
            print(e)

    def playEndGlobal(self, event = None):
        try:
            while True:
                if globals.stimulus == 2:
                    self.play_obj = sa.play_buffer(self.audio, 1, 2, self.fs)
                    print(f"\nTONE ON\n")
                    break
                
            while True:                  
                if globals.stimulus == 4:
                    print(f"\nTone OFF\n")
                    break

            sa.stop_all()
            

        except Exception as e:
            print(e)








        
