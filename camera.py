#!/usr/bin/env python3
### Data structure
import numpy as np
import threading
import struct
import h5py

try:
    import keyboard
except:
    pass
from datetime import datetime

## Maths
from scipy import optimize

## Media
import time
import cv2

try:
    from imutils.video import VideoStream
except:
    pass
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation
import matplotlib as mpl

## Comms
try:
    from uvctypes import *
except:
    pass

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

# from pynput import keyboard
import os

try:
    from failing import *
except:
    pass

from text import printme

def py_frame_callback(frame, userptr):

    array_pointer = cast(
        frame.contents.data,
        POINTER(c_uint16 * (frame.contents.width * frame.contents.height)),
    )
    data = np.frombuffer(array_pointer.contents, dtype=np.dtype(np.uint16)).reshape(
        frame.contents.height, frame.contents.width
    )

    if frame.contents.data_bytes != (2 * frame.contents.width * frame.contents.height):
        return

    if not q.full():
        q.put(data)


BUF_SIZE = 2
q = Queue(BUF_SIZE)
PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(py_frame_callback)
tiff_frame = 1
colorMapType = 0


class TherCam(object):
    def __init__(self, vminT=30, vmaxT=34):
        self.vminT = int(vminT)
        self.vmaxT = int(vmaxT)

        print(f"\nObject thermal camera initiliased\n")

    def startStream(self):

        """
        Method to start streaming. This method needs to be called always
        before you can extract the data from the camera.
        """
        global devh
        global dev
        ctx = POINTER(uvc_context)()
        dev = POINTER(uvc_device)()
        devh = POINTER(uvc_device_handle)()
        ctrl = uvc_stream_ctrl()
        print(ctrl.__dict__)

        res = libuvc.uvc_init(byref(ctx), 0)
        if res < 0:
            print("uvc_init error")
            # exit(1)

        try:
            res = libuvc.uvc_find_device(ctx, byref(dev), PT_USB_VID, PT_USB_PID, 0)
            print(res)
            if res < 0:
                print("uvc_find_device error")
                exit(1)

            try:
                res = libuvc.uvc_open(dev, byref(devh))
                print(res)
                if res < 0:
                    print("uvc_open error")
                    exit(1)

                print("device opened!")

                # print(devh)
                # print_device_info(devh)
                # print_device_formats(devh)

                frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16)
                if len(frame_formats) == 0:
                    print("device does not support Y16")
                    exit(1)

                libuvc.uvc_get_stream_ctrl_format_size(
                    devh,
                    byref(ctrl),
                    UVC_FRAME_FORMAT_Y16,
                    frame_formats[0].wWidth,
                    frame_formats[0].wHeight,
                    int(1e7 / frame_formats[0].dwDefaultFrameInterval),
                )

                res = libuvc.uvc_start_streaming(
                    devh, byref(ctrl), PTR_PY_FRAME_CALLBACK, None, 0
                )
                if res < 0:
                    print("uvc_start_streaming failed: {0}".format(res))
                    exit(1)

                print("done starting stream, displaying settings")
                print_shutter_info(devh)
                print("resetting settings to default")
                set_auto_ffc(devh)
                set_gain_high(devh)
                print("current settings")
                print_shutter_info(devh)

            except:
                libuvc.uvc_unref_device(dev)
                print("Failed to Open Device")
                exit(1)
        except:
            libuvc.uvc_exit(ctx)
            print("Failed to Find Device")
            exit(1)

    def setShutterManual(self):
        global devh
        print("Shutter is now manual.")
        set_manual_ffc(devh)

    def killStreaming(self):
        print("Terminating video streaming")
        global devh
        libuvc.uvc_stop_streaming(devh)

    def performManualff(self):
        print("Manual FFC")
        perform_manual_ffc(devh)
        print_shutter_info(devh)

    def saveRawData(self, output):
        global dev
        global devh

        tiff_frameLOCAL = 0

        f = h5py.File("./{}.hdf5".format(output), "w")

        import matplotlib as mpl

        mpl.rc("image", cmap="hot")

        fig = plt.figure()
        ax = plt.axes()

        fig.tight_layout()

        dummy = np.zeros([120, 160])

        img = ax.imshow(
            dummy,
            interpolation="nearest",
            vmin=self.vminT,
            vmax=self.vmaxT,
            animated=True,
        )
        fig.colorbar(img)

        # current_cmap = plt.cm.get_cmap()
        # current_cmap.set_bad(color='black')

        try:
            while True:
                data = q.get(True, 500)
                if data is None:
                    print("Data is none")
                    exit(1)
                data = (data - 27315) / 100

                f.create_dataset(("image" + str(tiff_frameLOCAL)), data=data)
                tiff_frameLOCAL += 1

                ax.clear()
                ax.set_xticks([])
                ax.set_yticks([])

                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_visible(False)
                ax.spines["bottom"].set_visible(False)
                ax.imshow(data, vmin=self.vminT, vmax=self.vmaxT)

                plt.pause(0.0005)

                if keyboard.is_pressed("e"):
                    print("We are done")
                    f.close()
                    exit(1)

        finally:
            libuvc.uvc_stop_streaming(devh)

    def plotLive(self):
        """
        Method to plot the thermal camera as a 2-D raster (imshow, heatmap).
        The min and max values of the heatmap are specified.
        You can take a pic too.
        """
        print('Press "r" to refresh the shutter.')
        print('Press "t" to take a thermal pic.')

        import matplotlib as mpl
        from mpl_toolkits.axes_grid1 import make_axes_locatable

        mpl.rc("image", cmap="coolwarm")

        global dev
        global devh
        global tiff_frame
        pressed = False

        fig = plt.figure()
        ax = plt.axes()
        div = make_axes_locatable(ax)
        cax = div.append_axes('right', '5%', '5%')

        # fig.tight_layout()

        dummy = np.zeros([120, 160])

        img = ax.imshow(
            dummy,
            interpolation="nearest",
            vmin=self.vminT,
            vmax=self.vmaxT,
            animated=True,
        )
        fig.colorbar(img, cax=cax)

        try:
            while True:
                # time.sleep(0.01)
                data = q.get(True, 500)
                if data is None:
                    print("Data is none")
                    exit(1)

                data = (data - 27315) / 100

                ax.clear()
                ax.set_xticks([])
                ax.set_yticks([])

                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["left"].set_visible(False)
                ax.spines["bottom"].set_visible(False)

                img = ax.imshow(data, vmin=self.vminT, vmax=self.vmaxT)
                fig.colorbar(img, cax=cax)

                plt.pause(0.0005)

                if keyboard.is_pressed("r"):
                    if not pressed:
                        print("Manual FFC")
                        perform_manual_ffc(devh)
                        print_shutter_info(devh)
                        pressed = True

                elif keyboard.is_pressed("t"):
                    if not pressed:
                        try:
                            now = datetime.now()
                            dt_string = now.strftime("day_%d_%m_%Y_time_%H_%M_%S")
                            printme(dt_string)
                            f = h5py.File(f"{self.pathset}/{dt_string}.hdf5", "w")
                            f.create_dataset("image", data=data)
                            f = None
                            printme('Thermal pic saved as hdf5')
                            if self.png:
                                plt.imsave(f'{self.pathset}/{dt_string}.png', data, vmin=self.vminT, vmax=self.vmaxT)

                        except Exception as e:
                            print(e)
                            print("There isn't a set path!")

                    pressed = True

                elif keyboard.is_pressed("e"):
                    if not pressed:
                        cv2.destroyAllWindows()
                        print("We are done")
                        break

                else:
                    pressed = False

        except Exception as e:
            print(e)
            libuvc.uvc_stop_streaming(devh)

    def setPathName(self, path, png=False):
        self.pathset = path
        self.png = png

    def StopStream(self):
        global devh
        print("Stop streaming")
        libuvc.uvc_stop_streaming(devh)

###############################################################
###################### FUNCTIONS ##############################
###############################################################

def circularMask(xs, ys, y, x, radius):
    mask = (xs[np.newaxis, :] - y) ** 2 + (
        ys[:, np.newaxis] - x
    ) ** 2 < radius ** 2
    return mask

def parallelogramMask(xs, ys, y, x, side_x, side_y):
    mask = np.full([len(ys), len(xs)], False)

    mask_x1 = int((y+1) - side_y/2)
    mask_x2 = int((y+1) + side_y/2)

    mask_y1 = int((x+1) - side_x/2)
    mask_y2 = int((x+1) + side_x/2)
    
    mask[mask_x1:mask_x2, mask_y1:mask_y2] = True

    return mask

def saveh5py(names, datas, frame, file):
    if len(names) != len(datas):
        print("Names and datas have to be the same length")

    for n, d in zip(names, datas):
        # print(n, d)
        # print('{}'.format(n)+str(frame))
        file.create_dataset(("{}".format(n) + str(frame)), data=d)

def refreshShutter(cam, timeout=True):
    cam.performManualff()
    printme(
        "Performing shutter refresh and taking a 10-second break\nto let the thermal image stabilise"
    )
    if timeout:
        time.sleep(10)


###############################################################
###################### Live plotting ##########################
###############################################################

# function to change the value of a variable with arrowkeys up and down with library keyboard
def changeValueVminT(cam):
    was_pressed_min = False
    while True:
        if keyboard.is_pressed('up'):
            if not was_pressed_min and (cam.vminT + 1) < cam.vmaxT:
                cam.vminT += 1
                printme(f'Vmin: {cam.vminT}, Vmax: {cam.vmaxT}')
                was_pressed_min = True
        elif keyboard.is_pressed('down'):
            if not was_pressed_min:
                cam.vminT -= 1
                printme(f'Vmin: {cam.vminT}, Vmax: {cam.vmaxT}')
                was_pressed_min = True
        elif keyboard.is_pressed('e'):
            break
        else:
            was_pressed_min = False

def changeValueVmaxT(cam):
    was_pressed_max = False
    while True:
        if keyboard.is_pressed('u'):
            if not was_pressed_max:
                cam.vmaxT += 1
                printme(f'Vmin: {cam.vminT}, Vmax: {cam.vmaxT}')
                was_pressed_max = True
        elif keyboard.is_pressed('d'):
            if not was_pressed_max and cam.vmaxT > (cam.vminT + 1):
                cam.vmaxT -= 1
                printme(f'Vmin: {cam.vminT}, Vmax: {cam.vmaxT}')
                was_pressed_max = True
        elif keyboard.is_pressed('e'):
            break
        else:
            was_pressed_max = False

def changeValuesColorBar(cam):
    manual_vminT = threading.Thread(
    target=changeValueVminT,
    args=[
        cam
        ],
        daemon=True,
    )
    manual_vmaxT = threading.Thread(
    target=changeValueVmaxT,
    args=[
        cam
        ],
        daemon=True,
    )

    manual_vminT.start()
    manual_vmaxT.start()

def ktoc(val):
    return (val - 27315) / 100.0

def raw_to_8bit(data):
    cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
    np.right_shift(data, 8, data)
    return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2BGR)


def rawToC(kel):
    celsius = round(((kel - 27315) / 100.0), 2)
    return celsius


def CToRaw(cel):
    kel = cel * 100 + 27315
    return kel


def moments(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution by calculating its
    moments"""
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X * data).sum() / total
    y = (Y * data).sum() / total
    col = data[:, int(y)]
    width_x = np.sqrt(np.abs((np.arange(col.size) - y) ** 2 * col).sum() / col.sum())
    row = data[int(x), :]
    width_y = np.sqrt(np.abs((np.arange(row.size) - x) ** 2 * row).sum() / row.sum())
    height = data.max()
    return height, x, y, width_x, width_y


def fitgaussian(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(data)
    errorfunction = lambda p: np.ravel(gaussian(*p)(*np.indices(data.shape)) - data)
    p, success = optimize.leastsq(errorfunction, params)
    return p


def gaussian(height, center_x, center_y, width_x, width_y):
    """Returns a gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x, y: height * np.exp(
        -(((center_x - x) / width_x) ** 2 + ((center_y - y) / width_y) ** 2) / 2
    )


######### Useuful links ###############

## Image analysis
# https://www.youtube.com/watch?v=-ZrDjwXZGxI

## https://lepton.flir.com/application-notes/people-finding-with-a-lepton/
## https://github.com/groupgets/pylepton/blob/master/pylepton/Lepton.py

##Windows
# https://lepton.flir.com/wp-content/uploads/2015/06/PureThermal-2-Basic-Lepton-Features.pdf
# https://lepton.flir.com/getting-started/quick-start-guide-getting-started-programing-with-python-sdk/
# https://lepton.flir.com/wp-content/uploads/2015/06/Advanced-Lepton-Usage-on-Windows.pdf

##Raspberr pi
# https://github.com/Kheirlb/purethermal1-uvc-capture
# https://lepton.flir.com/forums/topic/recording-and-viewing-raw-data/
#

## Video communication
# https://github.com/groupgets/purethermal1-uvc-capture