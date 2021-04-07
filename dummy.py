#!/usr/bin/env python3

try:
    import winsound
except:
    # print('This is not a Windows device')
    import simpleaudio as sa

import numpy as np
import matplotlib.pyplot as plt
import math
frequency = 440 # Our played note will be 440 Hz
fs = 44100  # 44100 samples per second
seconds = 3  # Note duration of 3 seconds

# Generate array with seconds*sample_rate steps, ranging between 0 and seconds
t = np.linspace(0, seconds, seconds * fs, False)

# t = [math.sqrt(x) for x in t[:]]
# t = np.asarray(t)

# t = [math.sqrt(x) for x in t[:]]
# t = np.asarray(t)

t = t**2
b = np.arange(1, 0, -1/len(t))

# Generate a 440 Hz sine wave
note = np.sin(frequency * (t) * 2 * np.pi)

bb = [math.sqrt(x) for x in b]

note = note * bb

plt.plot(note)

# Ensure that highest value is in 16-bit range
audio = note * (2**15 - 1) / np.max(np.abs(note))
# Convert to 16-bit data
audio = audio.astype(np.int16)

# %%
play_obj = sa.play_buffer(audio, 1, 2, fs)

# %%
