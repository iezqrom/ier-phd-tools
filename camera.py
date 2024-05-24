#!/usr/bin/env python3
### Data structure
import numpy as np
import threading
import h5py
import platform

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
import matplotlib as mpl
from mpl_toolkits.axes_grid1 import make_axes_locatable


try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from failing import errorloc
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

# check whether we are in windows
if platform.system() == "Windows":
    from camera_windows import CameraWindows

else:
    from uvctypes import *
    BUF_SIZE = 2
    q = Queue(BUF_SIZE)
    PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(py_frame_callback)
    tiff_frame = 1
    colorMapType = 0


class TherCam(object):
    def __init__(self, vminT=30, vmaxT=34):
        self.vminT = int(vminT)
        self.vmaxT = int(vmaxT)

        # check whether we are in windows
        if platform.system() == "Windows":
            self.windows = True
            self.windows_camera = CameraWindows()

        printme(f"Object thermal camera initiliased")
        printme(f"vminT = {self.vminT} and vmaxT = {self.vmaxT}")

    def startStream(self):
        global devh
        global dev
        """
        Method to start streaming. This method needs to be called always
        before you can extract the data from the camera.
        """
        if self.windows:
            self.windows_camera.initialiseCamera()
            time.sleep(1)
            self.windows_camera.startStream()
        else:
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

    def setPathName(self, path, png=False):
        self.pathset = path
        self.png = png

    def setShutterManual(self):
        global devh
        
        print("Shutter is now manual.")
        if self.windows:
            self.windows_camera.setShutterManual()
        else:
            set_manual_ffc(devh)

    def performManualff(self):
        global devh

        print("Manual FFC")
        if self.windows:
            self.windows_camera.performManualff()
        else:
            perform_manual_ffc(devh)
            print_shutter_info(devh)

    def stopStream(self):
        global devh
        print("Stop streaming")
        if self.windows:
            self.windows_camera.stopStream()
        else:
            libuvc.uvc_stop_streaming(devh)

    def grabDataFunc(self, func, **kwargs):
        frame_number = 1
        end = False
        if "file_name" not in kwargs:
            file_name = None
            hpy_file = None
        else:
            file_name = kwargs["file_name"]
            hpy_file = h5py.File(f"{self.pathset}/{file_name}.hdf5", "w")

        print('Starting to grab data')
        try:
            while True:
                thermal_image_kelvin_data = q.get(True, 500)
                if thermal_image_kelvin_data is None:
                    print("Data is none")
                    exit(1)
                thermal_image_celsius_data = (thermal_image_kelvin_data - 27315) / 100
                
                end = func(thermal_image_data = thermal_image_celsius_data, hpy_file = hpy_file, frame_number = frame_number, cam=self, **kwargs)

                frame_number += 1

                if end:
                    if hpy_file is not None:
                        print("Closing file")
                        hpy_file.close()
                    break

        except Exception as e:
            errorloc(e)
            self.stopStream()

    def plotLive(self):
        """
            Method to plot the thermal camera as a 2-D raster (imshow, heatmap).
            The min and max values of the heatmap are specified.
            You can take a pic too.
        """
        print('Press "r" to refresh the shutter.')
        print('Press "t" to take a thermal pic.')


        mpl.rc("image", cmap="coolwarm")

        pressed = False

        if platform.system() == "Windows":
            plt.ion()  # Enable interactive mode

        fig = plt.figure()
        ax = plt.axes()
        div = make_axes_locatable(ax)
        cax = div.append_axes('right', '5%', '5%')


        dummy = np.zeros([120, 160])

        img = ax.imshow(
            dummy,
            interpolation="nearest",
            vmin=self.vminT,
            vmax=self.vmaxT,
            animated=True,
        )
        ax.set_xticks([])
        ax.set_yticks([])

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)

        fig.colorbar(img, cax=cax)

        try:
            while True:
                if platform.system() == "Windows":
                    data = self.windows_camera.getFrame()
                else:
                    data = q.get(True, 500)
                if data is None:
                    print("Data is none")
                    exit(1)

                data = (data - 27315) / 100

                if platform.system() == "Windows":
                    img.set_data(data)  # Update image data
                    fig.canvas.draw()  # Redraw the figure
                    fig.canvas.flush_events()  # Flush the GUI events for real-time updates
                else:
                    ax.clear()
                    img = ax.imshow(data, vmin=self.vminT, vmax=self.vmaxT)
                    fig.colorbar(img, cax=cax)

                plt.pause(0.0005)

                if keyboard.is_pressed("r"):
                    if not pressed:
                        print("Manual FFC")
                        self.performManualff()
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
                        print("We are done")
                        
                        break

                else:
                    pressed = False

        except Exception as e:
            print(e)
            if platform.system() == "Windows":
                plt.ioff()
                plt.close(fig)

            self.stopStream()
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

def saveh5py(data, frame, file):
    for key in list(data.keys()):
        file.create_dataset(f"{key}{str(frame)}", data=data[key])

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

def saveRawData(**kargs):
    # check whether kwargs data, frame_number and hpy_file are given
    if "data" in kargs and "frame_number" in kargs and "hpy_file" in kargs:
        data = kargs["data"]
        frame_number = kargs["frame_number"]
        hpy_file = kargs["hpy_file"]

    hpy_file.create_dataset(("frame" + str(frame_number)), data=data)


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
# https://github.com/zof1985/flirpy

##Raspberr pi
# https://github.com/Kheirlb/purethermal1-uvc-capture
# https://lepton.flir.com/forums/topic/recording-and-viewing-raw-data/
#

## Video communication
# https://github.com/groupgets/purethermal1-uvc-capture