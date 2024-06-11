#!/usr/bin/env python3
import numpy as np
import h5py
import platform
import os
import time
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime
from mpl_toolkits.axes_grid1 import make_axes_locatable
try:
    import keyboard
except ImportError:
    pass
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from failing import error
from text import printme


def py_frame_callback(frame, userptr):
    """
    Callback function to handle frames from the camera.
    
    Args:
        frame: The frame data from the camera.
        userptr: User pointer.
    """
    array_pointer = cast(
        frame.contents.data,
        POINTER(c_uint16 * (frame.contents.width * frame.contents.height)),
    )
    data = np.frombuffer(array_pointer.contents, dtype=np.uint16).reshape(
        frame.contents.height, frame.contents.width
    )

    # Ensure frame size is correct
    if frame.contents.data_bytes != (2 * frame.contents.width * frame.contents.height):
        return

    # Add frame data to queue if not full
    if not q.full():
        q.put(data)


# Check whether we are in Windows
if platform.system() == "Windows":
    from camera_windows import CameraWindows
else:
    from uvctypes import *

    BUF_SIZE = 2
    q = Queue(BUF_SIZE)
    PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(py_frame_callback)
    tiff_frame = 1
    colorMapType = 0


class ThermalCamera:
    """
    A class to interact with a thermal camera.
    """

    def __init__(self, vminT=30, vmaxT=34):
        """
        Initializes the ThermalCamera object.

        Args:
            vminT (int, optional): Minimum temperature threshold. Defaults to 30.
            vmaxT (int, optional): Maximum temperature threshold. Defaults to 34.
        """
        self.vminT = int(vminT)
        self.vmaxT = int(vmaxT)
        self.frames_per_second = 8.7
        self.width = 160
        self.height = 120

        # Check whether we are in Windows
        if platform.system() == "Windows":
            self.windows = True
            self.windows_camera = CameraWindows()

        printme("Object thermal camera initialized")
        printme(f"vminT = {self.vminT} and vmaxT = {self.vmaxT}")


    def start_stream(self):
        global devh
        global dev
        """
        Method to start streaming. This method needs to be called always
        before you can extract the data from the camera.
        """
        if self.windows:
            self.windows_camera.initialise_camera()
            time.sleep(1)
            self.windows_camera.start_stream()
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

    def set_output_file(self, path, extra_name, base_file_name='thermal-camera', video_format='hdf5', png=False):
        """
        Sets the output file for recording the video.

        Args:
            path (str): The directory where the output file will be saved.
            extra_name (str): An additional name to be added to the base file name.
            base_file_name (str, optional): The base name of the output file. Defaults to 'thermal-camera'.
            video_format (str, optional): The format of the output video file. Defaults to 'hdf5'.
            png (bool, optional): Whether to save frames as PNG images. Defaults to False.
        """
        self.video_format = video_format
        self.output_file_name = f"{base_file_name}_{extra_name}.{video_format}"
        self.output_path = os.path.join(path, self.output_file_name)
        self.png = png


    def set_shutter_manual(self):
        """
        Sets the camera shutter to manual mode.
        """
        global devh

        print("Shutter is now manual.")
        if self.windows:
            self.windows_camera.set_shutter_manual()
        else:
            set_manual_ffc(devh)


    def perform_manual_ffc(self):
        """
        Performs a manual Flat Field Correction (FFC).
        """
        global devh

        print("Manual FFC")
        if self.windows:
            self.windows_camera.perform_manual_ffc()
        else:
            perform_manual_ffc(devh)
            print_shutter_info(devh)


    def stop_stream(self):
        """
        Stops the camera stream.
        """
        global devh

        # check if there's a file open
        if self.video_format == "hdf5" and self.create_hdf5_file:
            self.hpy_file.close()

        print("Stop streaming")
        if self.windows:
            self.windows_camera.stop_stream()
        else:
            libuvc.uvc_stop_streaming(devh)
    
    
    def create_hdf5_file(self):
        """
        Creates an HDF5 file to store the thermal image data.
        """
        self.frame_number = 1
        if self.video_format == "hdf5":
            self.hpy_file = h5py.File(self.output_path, "w")
        else:
            assert False, "Invalid video format. Please set the video format to 'hdf5'."


    def capture_frame(self):
        """
        Captures a single frame from the thermal camera, converts it to Celsius,
        and writes it to the output file.
        """

        #Warning if hdf5 file is not created
        if self.video_format != "hdf5":
            assert False, "Invalid video format. Please set the video format to 'hdf5'."
        
        if self.windows:
            thermal_image_kelvin_data = self.windows_camera.get_frame()
        else:
            thermal_image_kelvin_data = q.get(True, 500)

        if thermal_image_kelvin_data is None:
            print("Data is none")

        thermal_image_celsius_data = (thermal_image_kelvin_data - 27315) / 100

        self.hpy_file.create_dataset((f"frame{self.frame_number}"), data = thermal_image_celsius_data)

        # get current time
        time = datetime.now().strftime("%H:%M:%S")        
        self.hpy_file.create_dataset((f"time{self.frame_number}"), data = time)


    def grab_data_func(self, func, **kwargs):
        """
        Grabs data from the thermal camera and processes it using the provided function.

        Args:
            func (function): A function to process the thermal image data.
            **kwargs: Additional keyword arguments to pass to the processing function.

        Raises:
            AssertionError: If the output path is not set.
            Exception: If an error occurs during data capture and processing.
        """
        end = False

        #Warning if hdf5 file is not created
        if self.video_format != "hdf5":
            assert False, "Invalid video format. Please set the video format to 'hdf5'."

        print('Starting to grab data')
        try:
            while not end:
                if self.windows:
                    thermal_image_kelvin_data = self.windows_camera.get_frame()
                else:
                    thermal_image_kelvin_data = q.get(True, 500) 
                if thermal_image_kelvin_data is None:
                    print("Data is none")
                    exit(1)

                thermal_image_celsius_data = (thermal_image_kelvin_data - 27315) / 100

                end = func(
                    thermal_image_data=thermal_image_celsius_data,
                    hpy_file=self.hpy_file,
                    frame_number=self.frame_number,
                    cam=self,
                    **kwargs
                )

                self.frame_number += 1

        except Exception as e:
            error(e)
            self.stop_stream()


    def plot_live(self):
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

