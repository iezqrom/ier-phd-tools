#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import animation
import os 

class Animate:
    """
    Class to animate matplotlib figures.
    """

    def __init__(self, fig = False, axes = False, plots = False):
        """
        Initialize the class with the figure and axes to animate.
        """
        self.fig = fig
        self.axes = axes
        self.plots = plots


    def set_output_file(self, path, name_file, extension = 'mp4'):
        """
        Set the output file for the animation.
        """
        self.path = path
        self.name_file = name_file
        self.output_path = os.path.join(path, name_file + '.' + extension)


    def define_writer(self, frame_rate, software = 'ffmpeg', bitrate=1800):
        """
        Define the writer for the animation.
        """
        self.frames_per_second = frame_rate
        Writer = animation.writers[software]
        self.writer = Writer(fps=frame_rate, metadata=dict(artist="Me"), bitrate=bitrate)

    
    def load_data(self, data):
        """
        Load the data to be animated.
        """
        self.data = data
        self.number_of_frames = len(data)


    def create_animation(self, function):
        """
        Animate the figure using the given function.
        """
        self.ani = animation.FuncAnimation(
            self.fig, 
            function, 
            frames = self.number_of_frames,
            fargs = (self.data, self.axes),
            interval = 1000 / self.writer.fps,
        )
    

    def save_animation(self):
        """
        Save the animation.
        """
        self.ani.save(self.output_path, writer=self.writer)