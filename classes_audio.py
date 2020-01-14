#!/usr/bin/env python3

try:
    import winsound
except:
    # print('This is not a Windows device')
    import simpleaudio as sa

import numpy as np


class Sound(object):
    def __init__(self, freq, duration):

        self.frequency = freq # Our played note will be 440 Hz
        self.fs = 44100  # 44100 samples per second
        self.seconds = duration  # Note duration of 3 seconds

        # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
        t = np.linspace(0, self.seconds, self.seconds * self.fs, False)

        # Generate a 440 Hz sine wave
        self.note = np.sin(self.frequency * t * 2 * np.pi)

        # Ensure that highest value is in 16-bit range
        self.audio = self.note * (2**15 - 1) / np.max(np.abs(self.note))
        # Convert to 16-bit data
        self.audio = self.audio.astype(np.int16)

    def play(self, event = None):
        if event != None:
            event.wait()
        # Start playback
        self.play_obj = sa.play_buffer(self.audio, 1, 2, self.fs)
