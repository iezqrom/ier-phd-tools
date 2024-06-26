# imports

from scipy import ndimage
import clr
import sys
import os
import platform
import numpy as np
import pythoncom  # Add this import
import signal

# Initialize COM
pythoncom.CoInitialize()

folder = "x64" if platform.architecture()[0] == "64bit" else "x86"
path = os.path.sep.join(__file__.split(os.path.sep)[:-1])
sys.path.append(os.path.sep.join([path, folder]))
clr.AddReference("LeptonUVC")
clr.AddReference("ManagedIR16Filters")

from Lepton import CCI
from IR16Filters import IR16Capture, NewBytesFrameEvent

def handle_exit(sig, frame):
    print("Exiting and cleaning up...")
    pythoncom.CoUninitialize()

# Register signal handlers for clean exit
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


class CameraWindows:
    def __init__(self):
        self.latest_frame = None
        self.CCI = CCI
        self.IR16Capture = IR16Capture
        self.NewBytesFrameEvent = NewBytesFrameEvent
        self.device = None
        self.reader = None

    def add_frame(self, array, width, height):
        """
          Add a new frame to the buffer of read data.
        """
        img = np.fromiter(array, dtype="uint16").reshape(height, width)  # parse
        img = ndimage.rotate(img, angle=0, reshape=True)  # rotation
        self.latest_frame = img.astype(np.float16)  # update the last reading

    def initialise_camera(self):
        """
           Initialize the camera and start capturing frames.
        """
        devices = []
        for i in self.CCI.GetDevices():
            if i.Name.startswith("PureThermal"):
                devices.append(i)

        if len(devices) > 1:
            print("Multiple Pure Thermal devices have been found.\n")
            for i, d in enumerate(devices):
                print("{}. {}".format(i, d))
            while True:
                idx = input("Select the index of the required device: ")
                try:
                    idx = int(idx)
                    if idx in range(len(devices)):
                        self.device = devices[idx]
                        break
                except ValueError:
                    print("Unrecognized input value.\n")

        elif len(devices) == 1:
            self.device = devices[0]

        else:
            self.device = None

        txt = "No devices called 'PureThermal' have been found."
        assert self.device is not None, txt
        self.device = self.device.Open()
        self.device.sys.RunFFCNormalization()

        self.device.sys.SetGainMode(self.CCI.Sys.GainMode.HIGH)


        self.reader = self.IR16Capture()
        callback = self.NewBytesFrameEvent(self.add_frame)
        self.reader.SetupGraphWithBytesCallback(callback)

    def start_streaming(self):
        """
            Start capturing frames.
        """
        self.reader.RunGraph()

    def set_shutter_manual(self):
        """
            Set the shutter mode to manual.
        """
        new_shutter_mode_obj = self.device.sys.GetFfcShutterModeObj()
        new_shutter_mode_obj.shutterMode = self.CCI.Sys.FfcShutterMode.AUTO

        self.device.sys.SetFfcShutterModeObj(new_shutter_mode_obj)

    def perform_manualff(self):
        """
            Perform a manual flat field correction.
        """
        self.device.sys.RunFFCNormalization()

    def stop_streaming(self):
        """
            Stop capturing frames.
        """
        self.reader.StopGraph()
        pythoncom.CoUninitialize()
        handle_exit(None, None)

    def get_frame(self):
        """
        Retrieve the latest frame captured by the camera.
        """
        return self.latest_frame