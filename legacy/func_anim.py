#!/usr/bin/env python3

import numpy as np

## Media
import time
import cv2
from imutils.video import VideoStream
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation

import os

####### ANIMATIONS
# Simple 2-D
def aniThermalGraphsSimplest(data, vminT, vmaxT, path, name_file, start, title="  "):
    """
    It generates an animation of thermal image saved as h5py.
    The plot is 2-D.

    """
    Writer = animation.writers["ffmpeg"]
    writer = Writer(fps=8.7, metadata=dict(artist="Me"), bitrate=1800)

    def animate(i, data, plot):

        try:

            raw_dum = data["image" + str(i + start)][0:120]

            # First subplot: 3D RAW
            ax1.clear()
            plots1 = ax1.imshow(raw_dum, cmap="hot", vmin=vminT, vmax=vmaxT)
            print(raw_dum)

            ax1.set_title("{}".format(title))

        except:
            print("Done")

    ################ Plot figure
    fig = plt.figure(figsize=(20, 10))

    #######################Axes
    ax1 = fig.add_subplot(111)

    x = np.arange(0, 120, 1)
    y = np.arange(0, 160, 1)

    xs, ys = np.meshgrid(x, y)
    zs = (xs * 0 + 15) + (ys * 0 + 15)

    ######################Plots
    ## First subplot: 3D RAW
    plot1 = ax1.imshow(zs, cmap="hot", vmin=vminT, vmax=vmaxT)
    cbar = fig.colorbar(plot1, ax=ax1)
    cbar.set_label("($^\circ$C)")

    # Animation & save
    ani = animation.FuncAnimation(
        fig, animate, frames=len(data.keys()), fargs=(data, plot1), interval=1000 / 8.7
    )

    ani.save("./{}/{}.mp4".format(path, name_file), writer=writer)


####### ANIMATIONS
# Simple 2-D with fixed and dynamic ROI
def aniThermalGraphsSimFnDROI(
    data, vminT, vmaxT, path, name_file, start, fROI, dROI, r=20, title="  "
):
    """
    It generates an animation of thermal image saved as h5py.
    The plot is 2-D. It shows the fixed and the dynamic ROI

    """
    Writer = animation.writers["ffmpeg"]
    writer = Writer(fps=8.7, metadata=dict(artist="Me"), bitrate=1800)

    def animate(i, data, plot):

        try:

            raw_dum = data["image" + str(i + start)][0:120]

            f_roi = data["image" + str(i + start)][fROI]
            d_roi = data["image" + str(i + start)][dROI]

            cirD = plt.Circle((d_roi[-1], d_roi[1]), r, color="b", fill=False)
            cirF = plt.Circle((f_roi[-1], f_roi[1]), r, color="g", fill=False)

            # First subplot: 3D RAW
            ax1.clear()
            ax1.imshow(raw_dum, cmap="hot", vmin=vminT, vmax=vmaxT)

            ax1.set_title("{}".format(title))
            ax1.add_artist(cirD)
            ax1.add_artist(cirF)

            print("In process...")

        except:
            print("Done")

    ################ Plot figure
    fig = plt.figure(figsize=(20, 10))

    #######################Axes
    ax1 = fig.add_subplot(111)

    x = np.arange(0, 120, 1)
    y = np.arange(0, 160, 1)

    xs, ys = np.meshgrid(x, y)
    zs = (xs * 0 + 15) + (ys * 0 + 15)

    ######################Plots
    ## First subplot:
    plot1 = ax1.imshow(zs, cmap="hot", vmin=vminT, vmax=vmaxT)
    cbar = fig.colorbar(plot1, ax=ax1)
    cbar.set_label("($^\circ$C)")

    # Animation & save
    ani = animation.FuncAnimation(
        fig, animate, frames=len(data.keys()), fargs=(data, plot1), interval=1000 / 8.7
    )

    ani.save("./{}/{}.mp4".format(path, name_file), writer=writer)
    print("Animation generation is done!")


def aniThermalGraphsSimFnDROITextPos(
    data, vminT, vmaxT, path, name_file, start, fROI, dROI, r=20, title="  "
):
    """
    It generates an animation of thermal image saved as h5py.
    The plot is 2-D. It shows the fixed and the dynamic ROI

    """
    Writer = animation.writers["ffmpeg"]
    writer = Writer(fps=8.7, metadata=dict(artist="Me"), bitrate=1800)

    def animate(i, data, plot):

        try:

            raw_dum = data["image" + str(i + start)][0:120]

            f_roi = data["image" + str(i + start)][fROI]
            d_roi = data["image" + str(i + start)][dROI]

            cirD = plt.Circle((d_roi[-1], d_roi[1]), r, color="b", fill=False)
            cirF = plt.Circle((f_roi[-1], f_roi[1]), r, color="g", fill=False)

            # First subplot: 3D RAW
            ax1.clear()
            ax1.imshow(raw_dum, cmap="hot", vmin=vminT, vmax=vmaxT)
            ax1.text(140, 110, data["image" + str(i + start)][124][0])

            ax1.set_title("{}".format(title))
            ax1.add_artist(cirD)
            ax1.add_artist(cirF)

            print("In process...")

        except Exception as e:
            print(e)

    ################ Plot figure
    fig = plt.figure(figsize=(20, 10))

    #######################Axes
    ax1 = fig.add_subplot(111)

    x = np.arange(0, 120, 1)
    y = np.arange(0, 160, 1)

    xs, ys = np.meshgrid(x, y)
    zs = (xs * 0 + 15) + (ys * 0 + 15)

    ######################Plots
    ## First subplot:
    plot1 = ax1.imshow(zs, cmap="hot", vmin=vminT, vmax=vmaxT)
    cbar = fig.colorbar(plot1, ax=ax1)
    cbar.set_label("($^\circ$C)")

    # Animation & save
    ani = animation.FuncAnimation(
        fig, animate, frames=len(data.keys()), fargs=(data, plot1), interval=1000 / 8.7
    )

    ani.save("./{}/{}.mp4".format(path, name_file), writer=writer)
    print("Animation generation is done!")


# Simple 3-D
def aniThermal3d(data, vminT, vmaxT, path, name_file, start, title="  "):
    x = np.arange(0, 160, 1)
    y = np.arange(0, 120, 1)

    xs, ys = np.meshgrid(x, y)
    zs = (xs * 0 + 15) + (ys * 0 + 15)

    Writer = animation.writers["ffmpeg"]
    writer = Writer(fps=8.7, metadata=dict(artist="Me"), bitrate=1800)

    def animate(i, data, plot):

        try:
            zs = data.read["image" + str(i + start)][:]
            ax.clear()
            ax.set_zlim(vminT, vmaxT)
            plot = ax.plot_surface(xs, ys, zs, cmap="hot", vmin=vminT, vmax=vmaxT)
            ax.set_zlabel("($^\circ$C)")

        except:
            print("Done")

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    plot = ax.plot_surface(
        xs, ys, zs, rstride=1, cstride=1, cmap="hot", vmin=vminT, vmax=vmaxT
    )
    cbar = fig.colorbar(plot)
    cbar.set_label("($^\circ$C)")

    ani = animation.FuncAnimation(
        fig,
        animate,
        frames=len(data.read.keys()),
        fargs=(data, plot),
        interval=1000 / 8.7,
    )

    ani.save("./{}/{}.mp4".format(path, name_file), writer=writer)
