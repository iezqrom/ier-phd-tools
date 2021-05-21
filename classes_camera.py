#!/usr/bin/env python3

### Data structure
from __future__ import print_function
import numpy as np
import ctypes
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
from uvctypes import *

try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform
# from pynput import keyboard
import os
import argparse
try:
    import imutils
except:
    pass


try:
    import globals
    # print(globals.shutter_state)
except:
    pass

try:
    from failing import *
except:
    pass

import struct

def py_frame_callback(frame, userptr):

  array_pointer = cast(frame.contents.data, POINTER(c_uint16 * (frame.contents.width * frame.contents.height)))
  data = np.frombuffer(
    array_pointer.contents, dtype=np.dtype(np.uint16)
  ).reshape(
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

    def __init__(self, vminT = 30, vmaxT = 34):
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

        res = libuvc.uvc_init(byref(ctx), 0)
        if res < 0:
            print("uvc_init error")
            #exit(1)

        try:
            res = libuvc.uvc_find_device(ctx, byref(dev), PT_USB_VID, PT_USB_PID, 0)
            if res < 0:
                print("uvc_find_device error")
                exit(1)

            try:
                res = libuvc.uvc_open(dev, byref(devh))
                if res < 0:
                    print("uvc_open error")
                    exit(1)

                print("device opened!")

        #   print_device_info(devh)
        #   print_device_formats(devh)

                frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16)
                if len(frame_formats) == 0:
                    print("device does not support Y16")
                    exit(1)

                libuvc.uvc_get_stream_ctrl_format_size(devh, byref(ctrl), UVC_FRAME_FORMAT_Y16,
                    frame_formats[0].wWidth, frame_formats[0].wHeight, int(1e7 / frame_formats[0].dwDefaultFrameInterval))

                res = libuvc.uvc_start_streaming(devh, byref(ctrl), PTR_PY_FRAME_CALLBACK, None, 0)
                print('RES')
                print(res)
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
                print('Failed to Open Device')
                exit(1)
        except:
            libuvc.uvc_exit(ctx)
            print('Failed to Find Device')
            exit(1)

    def saveThermalFilm(self, output):
        global dev
        global devh
        frame_width = 640
        frame_height = 480
        fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
        writer = cv2.VideoWriter('{}.avi'.format(output), fourcc, 9, (frame_width, frame_height), True)

        try:
            while True:
                data = q.get(True, 500)
                if data is None:
                    break
                data = cv2.resize(data[:,:], (640, 480))

                # img = raw_to_8bit(data)
                img = cv2.LUT(raw_to_8bit(data), generate_colour_map())
               # img = cv2.LUT(raw_to_8bit(data), generate_colour_map())

                writer.write(img)
                cv2.imshow('Lepton Radiometry', img)
                # Press Q on keyboard to stop recording
                if cv2.waitKey(1) & 0xFF == ord('q'):
                  # When everything done, release the video capture and video write objects

                    writer.release()
                    # Closes all the frames
                    cv2.destroyAllWindows()
                    exit(1)

        finally:
            libuvc.uvc_stop_streaming(devh)

    def setShutterManual(self):
        global devh
        print('Shutter is now manual.')
        set_manual_ffc(devh)

    def killStreaming(self):
        print('Terminating video streaming')
        global devh
        libuvc.uvc_stop_streaming(devh)
        
    def performManualff(self):
        print('Manual FFC')
        perform_manual_ffc(devh)
        print_shutter_info(devh)

    def saveRawData(self, output):
        global dev
        global devh

        tiff_frameLOCAL = 0

        f = h5py.File("./{}.hdf5".format(output), "w")

        import matplotlib as mpl
        mpl.rc('image', cmap='hot')

        fig = plt.figure()
        ax = plt.axes()

        fig.tight_layout()

        dummy = np.zeros([120, 160])

        img = ax.imshow(dummy, interpolation='nearest', vmin = self.vminT, vmax = self.vmaxT, animated = True)
        fig.colorbar(img)

        # current_cmap = plt.cm.get_cmap()
        # current_cmap.set_bad(color='black')

        try:
            while True:
                data = q.get(True, 500)
                if data is None:
                    print('Data is none')
                    exit(1)
                data = (data - 27315) / 100

                f.create_dataset(('image'+str(tiff_frameLOCAL)), data=data)
                tiff_frameLOCAL += 1

                ax.clear()
                ax.set_xticks([])
                ax.set_yticks([])

                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.imshow(data, vmin = self.vminT, vmax = self.vmaxT)

                plt.pause(0.0005)

                if keyboard.is_pressed('e'):
                    print('We are done')
                    f.close()
                    exit(1)

        finally:
            libuvc.uvc_stop_streaming(devh)

    def justStream(self):
        global dev
        global devh
        frame_width = 640
        frame_height = 480

        try:
            while True:
                # print('hola')
                data = q.get(True, 500)
                # print('adios')
                if data is None:
                    break
                data = cv2.resize(data[:,:], (640, 480))

                # img = raw_to_8bit(data)
                img = cv2.LUT(raw_to_8bit(data), generate_colour_map())
                # print(img)
               # img = cv2.LUT(raw_to_8bit(data), generate_colour_map())


                cv2.imshow('Just streaming thermal video...', img)
                # Press Q on keyboard to stop recording
                if cv2.waitKey(1) & 0xFF == ord('q'):
                  # When everything done, release the video capture and video write objects

                    # Closes all the frames
                    cv2.destroyAllWindows()
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
        mpl.rc('image', cmap='hot')

        global dev
        global devh
        global tiff_frame

        fig = plt.figure()
        ax = plt.axes()

        fig.tight_layout()

        dummy = np.zeros([120, 160])

        img = ax.imshow(dummy, interpolation='nearest', vmin = self.vminT, vmax = self.vmaxT, animated = True)
        fig.colorbar(img)
 
        try:
            while True:
                # time.sleep(0.01)
                data = q.get(True, 500)
                if data is None:
                    print('Data is none')
                    exit(1)

                data = (data - 27315) / 100

                ax.clear()
                ax.set_xticks([])
                ax.set_yticks([])

                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.imshow(data, vmin = self.vminT, vmax = self.vmaxT)

                plt.pause(0.0005)

                if keyboard.is_pressed('r'):
                    print('Manual FFC')
                    perform_manual_ffc(devh)
                    print_shutter_info(devh)
                
                if keyboard.is_pressed('t'):
                    try:
                        now = datetime.now()
                        dt_string = now.strftime("day_%d_%m_%Y_time_%H_%M_%S")
                        print(dt_string)
                        f = h5py.File("{}/{}.hdf5".format(self.pathset, dt_string), "w")
                        f.create_dataset('image', data=data)
                        f = None

                    except Exception as e:
                        print(e)
                        print("There isn't a set path!")


                if keyboard.is_pressed('e'):
                    cv2.destroyAllWindows()
                    frame = 1
                    print('We are done')
                    break

        except Exception as e:
            print(e)
            libuvc.uvc_stop_streaming(devh)

    def setPathName(self, path):
        self.pathset = path

    def PIDROI(self, output, event1, r = 20, arduino = None):
        """
            Method function to perform PID on a given ROI with the camera.
            The required parameters are output.
            It doesn't save the dynamic ROI.
            Globals: stimulus, timeout, pid_var, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print('File to save initialised')
        start = time.time()

        try:
            while True:
                
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # We save the data

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                dataC = (dataK - 27315) / 100

                indx, indy = globals.centreROI
                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]
                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(globals.temp))

                event1.set()

                momen = time.time() - start

                names = ['image', 'pid_out', 'shutter_pos', 'fixed_ROI', 'time_now']
                datas = [dataC, [globals.pid_out], [globals.stimulus], [indx, indy], [momen]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

                if keyboard.is_pressed('e'):
                    break

                if momen > globals.timeout and globals.stimulus == 1:
                    print('Time out')
                    globals.stimulus = 0
                    print('Close shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    break
                    

            event1.set()
            print('Camera off')
            f.close()

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def targetTempMan(self, output, target_temp, r = 20, arduino = None):
        """
            Method function to open the shutter and then close when target temperature is reached.
            The required parameters are output and target temperature
            It doesn't save the dynamic ROI.
            Globals: stimulus, timeout, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print('File to save initialised')
        start = time.time()

        try:
            while True:
                
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # We save the data

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                dataC = (dataK - 27315) / 100

                indx, indy = globals.centreROI
                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]
                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(globals.temp))
                # if globals.stimulus == 1:

                momen = time.time() - start

                names = ['image', 'shutter_pos', 'fixed_ROI', 'time_now']
                datas = [dataC, [globals.stimulus], [indx, indy], [momen]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1
                print('Time:  ' + str(momen))

                if keyboard.is_pressed('e'):
                    break

                if keyboard.is_pressed('o'):
                    globals.stimulus = 1
                    print('Open shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))

                if globals.temp < target_temp:
                    globals.stimulus = 0
                    print('Close shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))

            print('Camera off')
            f.close()

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def targetTempAuto(self, output, target_temp, centreROI, r = 20, arduino = None, stimulus = 1, total_time_out = 15, event_camera = None, event_touch = None):
        """
            Method function to measure temperature of ROI and trigger action when a given temperature is reached.
            The required parameters are output and target temperature.
            Globals: stimulus, timeout, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print(f'\nFile to save video initialised\n')
        start = time.time()
        close_shutter = None
        shutter_closed = None
        end = False
        shutter_opened = False
        touched = False

        post_shutter_time_out = 2
        pre_shutter_time_in = 2
        touch_time_out = 1
        touch_time_in = 1
        self.shutter_open_time = None

        xs = np.arange(0, 160)
        ys = np.arange(0, 120)
        edge = 0

        try:
            while True:
                
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # Dynamic ROI
                subdataK = dataK[edge:edge + (120 - edge*2), edge:edge + (160 - edge*2)]
                subdataC = (subdataK - 27315)/100
                subdataC[subdataC <= (target_temp - 0.1)] = 100
                minimoC = np.min(subdataC)

                indxD, indyD = np.where(subdataC == minimoC)
                indxD, indyD = indxD + edge, indyD + edge


                dataC = (dataK - 27315) / 100

                indx, indy = centreROI

                try:
                    x_diff = (indxD[0] - indx)**2
                    y_diff = (indyD[0] - indy)**2
                except:
                    continue

                eud = np.sqrt(x_diff + y_diff)
                eud = round(eud, 2)

                if stimulus == 2:
                    print(f'Euclidean distance between ROIs {eud}')
                else:
                    eud = 100

                if eud < 20:
                    mask = (xs[np.newaxis,:]- indyD[0])**2 + (ys[:,np.newaxis] - indxD[0])**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)
                    sROI = 1
                    print('DYNAMIC')
                    
                else:
                    mask = (xs[np.newaxis,:]- indy)**2 + (ys[:,np.newaxis] - indx)**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)
                    sROI = 0
                    print('STATIC')

                print('Mean: ' + str(globals.temp))

                momen = time.time() - start

                names = ['image', 'shutter_pos', 'fixed_ROI', 'time_now', 'dynamic_ROI', 'eud', 'sROI']
                datas = [dataC, [globals.stimulus], [indx, indy], [momen], [indxD, indyD], [eud], [sROI]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

                if end:
                    shutter_closed = time.time() - close_shutter

                if momen > (total_time_out + pre_shutter_time_in):
                    if not end and shutter_opened:
                        self.shutter_open_time = time.time() - self.shutter_open_time
                        globals.stimulus = 4
                        print('Close shutter (camera)')
                        arduino.arduino.write(struct.pack('>B', globals.stimulus))
                        event_camera.set()
                        close_shutter = time.time()
                        if event_touch:
                            event_touch.set()
                        end = True

                    if event_touch:
                        event_touch.set()
                        touched = True
                        
                    break

                if self.shutter_open_time and touched and end and shutter_closed:
                    if shutter_closed > touch_time_out and shutter_closed < (touch_time_out + 0.2):
                        print('UNTOUCH CAMERA')
                        if event_touch:
                            event_touch.set()
                            touched = False

                if momen > touch_time_in and not touched:
                    if event_touch:
                        event_touch.set()
                        touched = True

                if globals.temp > target_temp and momen > pre_shutter_time_in and momen < (pre_shutter_time_in + 0.2) and not shutter_opened:
                    globals.stimulus = stimulus
                    print('Open shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    event_camera.set()
                    shutter_opened = True
                    self.shutter_open_time = time.time()
                    # time.sleep(0.1)

                if globals.temp < target_temp and not end and shutter_opened:
                    self.shutter_open_time = time.time() - self.shutter_open_time
                    print(f'\nTIME SHUTTER WAS OPEN {self.shutter_open_time}\n')
                    globals.stimulus = 4
                    print('Close shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    event_camera.set()
                    close_shutter = time.time()
                    end = True
                    shutter_opened = False

                print(f"Time since shutter closed: {shutter_closed}")

                if globals.temp < target_temp and momen > pre_shutter_time_in and momen < (pre_shutter_time_in + 0.2) and not shutter_opened:
                    print('UNTOUCH CAMERA')
                    if event_touch:
                        event_touch.set()
                        touched = False
                    break

                if end and shutter_closed:  
                    if shutter_closed > post_shutter_time_out:
                        break

                event_camera.clear()

            print('Camera off')
            f.close()

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def targetTempAutoDiff(self, output, target_temp, centreROI, r = 20, arduino = None, stimulus = 1, total_time_out = 15, event_camera = None, event_touch = None):
        """
            Method function to measure temperature of ROI and trigger action when a given temperature is reached.
            The required parameters are output and target temperature.
            Globals: stimulus, timeout, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print(f'\nFile to save video initialised\n')
        start = time.time()
        close_shutter = None
        shutter_closed = None
        end = False
        shutter_opened = False
        touched = False

        post_shutter_time_out = 2
        pre_shutter_time_in = 2
        touch_time_out = 1
        touch_time_in = 1
        self.shutter_open_time = None
        diff_buffer = []
        xs = np.arange(0, 160)
        ys = np.arange(0, 120)

        try:
            while True:
                
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                momen = time.time() - start

                dataC = (dataK - 27315) / 100

                indx, indy = centreROI

                if momen > 1.6 and momen < 2.0:
                    diff_buffer.append(dataC)

                if globals.stimulus == 2:
                    dif = mean_diff_buffer - dataC
                    dif[dataC <= (target_temp - 0.1)] = 0
                    maxdif = np.max(dif)
                    indxdf, indydf = np.where(dif == maxdif)
                    mask = (xs[np.newaxis,:]-indydf[0])**2 + (ys[:,np.newaxis]-indxdf[0])**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)
                    
                    print('Mean: ' + str(globals.temp))
                    sROI = 1
                else:
                    mask = (xs[np.newaxis,:]- indy)**2 + (ys[:,np.newaxis] - indx)**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)
                    
                    print('Mean: ' + str(globals.temp))
                    sROI = 0
                    indxdf, indydf = -1, -1

                names = ['image', 'shutter_pos', 'fixed_ROI', 'time_now', 'diff_ROI', 'sROI']
                datas = [dataC, [globals.stimulus], [indx, indy], [momen], [indxdf, indydf], [sROI]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

                if end:
                    shutter_closed = time.time() - close_shutter

                if momen > (total_time_out + pre_shutter_time_in):
                    if not end and shutter_opened:
                        self.shutter_open_time = time.time() - self.shutter_open_time
                        globals.stimulus = 4
                        print('Close shutter (camera)')
                        arduino.arduino.write(struct.pack('>B', globals.stimulus))
                        event_camera.set()
                        close_shutter = time.time()
                        if event_touch:
                            event_touch.set()
                        end = True

                    if event_touch:
                        event_touch.set()
                        touched = True
                        
                    break

                if self.shutter_open_time and touched and end and shutter_closed:
                    if shutter_closed > touch_time_out and shutter_closed < (touch_time_out + 0.2):
                        print('UNTOUCH CAMERA')
                        if event_touch:
                            event_touch.set()
                            touched = False

                if momen > touch_time_in and not touched:
                    if event_touch:
                        event_touch.set()
                        touched = True

                if globals.temp > target_temp and momen > pre_shutter_time_in and momen < (pre_shutter_time_in + 0.2) and not shutter_opened:
                    globals.stimulus = stimulus
                    print('Open shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    event_camera.set()
                    shutter_opened = True
                    self.shutter_open_time = time.time()
                    mean_diff_buffer = np.mean(diff_buffer, axis=0)
                    # time.sleep(0.1)

                if globals.temp < target_temp and not end and shutter_opened:
                    self.shutter_open_time = time.time() - self.shutter_open_time
                    print(f'\nTIME SHUTTER WAS OPEN {self.shutter_open_time}\n')
                    globals.stimulus = 4
                    print('Close shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    event_camera.set()
                    close_shutter = time.time()
                    end = True
                    shutter_opened = False

                if globals.temp < target_temp and momen > pre_shutter_time_in and momen < (pre_shutter_time_in + 0.2) and not shutter_opened:
                    print('UNTOUCH CAMERA')
                    if event_touch:
                        event_touch.set()
                        touched = False
                    break

                print(f"Time since shutter closed: {shutter_closed}")

                if end and shutter_closed:  
                    if shutter_closed > post_shutter_time_out:
                        break


                event_camera.clear()

            print('Camera off')
            f.close()

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def targetTempAutoDiffDelta(self, output, target_delta, centreROI, r = 20, arduino = None, stimulus = 1, total_time_out = 12, event_camera = None, event_touch = None):
        """
            Method function to measure temperature of ROI and trigger action when a given temperature is reached.
            The required parameters are output and target temperature.
            Globals: stimulus, timeout, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print(f'\nFile to save video initialised\n')
        start = time.time()
        close_shutter_stamp = None
        shutter_closed_time = None
        end = False
        shutter_opened = False
        touched = False
        globals.stimulus = 4

        self.failed_trial = False

        post_shutter_time_out = 2
        pre_shutter_time_in = 2
        touch_time_out = 1
        touch_time_in = 1
        self.shutter_open_time = None
        xs = np.arange(0, 160)
        ys = np.arange(0, 120)

        diff_buffer = []
        baseline_buffer = []

        try:
            while True:
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                momen = time.time() - start

                dataC = (dataK - 27315) / 100

                indx, indy = centreROI
                indxdf, indydf = np.ones((2, 1))

                if end:
                    shutter_closed_time = time.time() - close_shutter_stamp

                if momen > (total_time_out + pre_shutter_time_in):
                    if not end and shutter_opened:
                        self.shutter_open_time = time.time() - self.shutter_open_time
                        if stimulus == 2:
                            self.failed_trial = True
                            print('FAILED stimulation')
                        globals.stimulus = 4
                        print('Close shutter (camera)')
                        arduino.arduino.write(struct.pack('>B', globals.stimulus))
                        event_camera.set()
                        close_shutter_stamp = time.time()
                        if event_touch:
                            event_touch.set()
                        end = True

                    if event_touch:
                        event_touch.set()
                        touched = True

                if self.shutter_open_time and touched and end and shutter_closed_time:
                    if shutter_closed_time > touch_time_out and shutter_closed_time < (touch_time_out + 0.2):
                        print('UNTOUCH CAMERA')
                        if event_touch:
                            event_touch.set()
                            touched = False

                if momen > touch_time_in and not touched:
                    if event_touch:
                        event_touch.set()
                        touched = True

                if momen > pre_shutter_time_in and not end and not shutter_opened:
                    globals.stimulus = stimulus
                    print('Open shutter (camera)')
                    try:
                        arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    except:
                        print('ARDUINO FAILED!')
                    event_camera.set()
                    shutter_opened = True
                    self.shutter_open_time = time.time()
                    meand_baseline_buffer = np.mean(baseline_buffer)
                    print(f'Meaned baseline {meand_baseline_buffer}')

                if globals.stimulus == 2:
                    buffering_time = time.time() - self.shutter_open_time

                    if buffering_time < 0.3:
                        diff_buffer.append(dataC)
                        print('buffering...')
                        print(round(buffering_time, 4))
                        mean_diff_buffer = np.mean(diff_buffer, axis=0)
                        indxdf, indydf = np.ones((2, 1))

                    elif buffering_time >= 0.3:
                        dif = mean_diff_buffer - dataC

                        dif[dataC <= 28] = 0
                        dif[dif <= (0.3)] = 0

                        maxdif = np.max(dif)
                        indxdf, indydf = np.where(dif == maxdif)
                        print(indxdf[0], indydf[0])

                        mask = (xs[np.newaxis,:]-indydf[0])**2 + (ys[:,np.newaxis]-indxdf[0])**2 < r**2
                        roiC = dataC[mask]
                        globals.temp = round(np.mean(roiC), 2)

                        globals.delta = meand_baseline_buffer - globals.temp
                        print('Delta: ' + str(round(globals.delta, 2)))

                    sROI = 1

                elif globals.stimulus == 4 and not end:
                    mask = (xs[np.newaxis,:]- indy)**2 + (ys[:,np.newaxis] - indx)**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)

                    baseline_buffer.append(globals.temp)
                    
                    print('Baseline: ' + str(globals.temp))
                    sROI = 0
                    
                    indxdf, indydf = -1, -1

                if globals.delta > target_delta and not end and shutter_opened and globals.delta < (target_delta + 0.6):
                    self.shutter_open_time = time.time() - self.shutter_open_time
                    
                    print(f'\nTIME SHUTTER WAS OPEN {self.shutter_open_time}\n')
                    print(f'\nClose shutter (camera)\n')

                    globals.stimulus = 4
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    close_shutter_stamp = time.time()

                    event_camera.set()
                    end = True
                    shutter_opened = False

                # print(f"Time since shutter closed: {shutter_closed}")

                if end and shutter_closed_time:  
                    if shutter_closed_time > post_shutter_time_out:
                        break

                names = ['image', 'shutter_pos', 'fixed_ROI', 'time_now', 'diff_ROI', 'sROI', 'delta']
                datas = [dataC, [globals.stimulus], [indx, indy], [momen], [indxdf, indydf], [sROI], [globals.delta]]
                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

                event_camera.clear()

            print('Camera off')
            f.close()

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def openTimer(self, output, centreROI, stimulus= 1, r = 20, arduino = None, total_time_out = 10):
        """
            Method function to measure temperature of ROI and trigger action when a given temperature is reached.
            The required parameters are output and target temperature.
            Globals: stimulus, timeout, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print(f'\nFile to save video initialised\n')
        start = time.time()
        close_shutter_stamp = None
        shutter_closed_time = None
        end = False
        shutter_opened = False

        globals.stimulus = 4

        post_shutter_time_out = 2
        pre_shutter_time_in = 2

        self.shutter_open_time = None
        xs = np.arange(0, 160)
        ys = np.arange(0, 120)

        diff_buffer = []
        baseline_buffer = []

        try:
            while True:
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                momen = time.time() - start

                dataC = (dataK - 27315) / 100

                indx, indy = centreROI
                indxdf, indydf = np.ones((2, 1))

                if end:
                    shutter_closed_time = time.time() - close_shutter_stamp

                if momen > (total_time_out):
                    globals.stimulus = 0
                    print('Close shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    end = True
                    shutter_opened = False

                if momen > pre_shutter_time_in and not end and not shutter_opened:
                    globals.stimulus = stimulus
                    print('Open shutter (camera)')
                    try:
                        arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    except:
                        print('ARDUINO FAILED!')

                    shutter_opened = True
                    self.shutter_open_time = time.time()
                    meand_baseline_buffer = np.mean(baseline_buffer)
                    print(f'Meaned baseline {meand_baseline_buffer}')

                if globals.stimulus == 1:
                    buffering_time = time.time() - self.shutter_open_time

                    if buffering_time < 0.3:
                        diff_buffer.append(dataC)
                        print('buffering...')
                        print(round(buffering_time, 4))
                        mean_diff_buffer = np.mean(diff_buffer, axis=0)
                        indxdf, indydf = np.ones((2, 1))

                    elif buffering_time >= 0.3:
                        dif = mean_diff_buffer - dataC

                        dif[dataC <= 28] = 0
                        dif[dif <= (0.3)] = 0

                        maxdif = np.max(dif)
                        indxdf, indydf = np.where(dif == maxdif)
                        print(indxdf[0], indydf[0])

                        mask = (xs[np.newaxis,:]-indydf[0])**2 + (ys[:,np.newaxis]-indxdf[0])**2 < r**2
                        roiC = dataC[mask]
                        globals.temp = round(np.mean(roiC), 2)

                        globals.delta = meand_baseline_buffer - globals.temp
                        print('Delta: ' + str(round(globals.delta, 2)))

                    sROI = 1

                elif globals.stimulus == 0 and not end:
                    mask = (xs[np.newaxis,:]- indy)**2 + (ys[:,np.newaxis] - indx)**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)

                    baseline_buffer.append(globals.temp)

                    print('Baseline: ' + str(globals.temp))
                    sROI = 0

                    indxdf, indydf = -1, -1

                if end and shutter_closed_time:
                    if shutter_closed_time > post_shutter_time_out:
                        break

                names = ['image', 'shutter_pos', 'fixed_ROI', 'time_now', 'diff_ROI', 'sROI']
                datas = [dataC, [globals.stimulus], [indx, indy], [momen], [indxdf, indydf], [sROI]]
                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

            print('Camera off')
            f.close()

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass



    def readShutterOnOff(self, output, range, r = 20, arduino = None):
        """
            Method function to read passively on a given ROI with the camera.
            The required parameters are output.
            It doesn't save the dynamic ROI.
            Globals: stimulus, timeout, pid_var, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print('File to save initialised')
        start = time.time()
        start_countdown = start * 2
        momen = 0
        cd = 0

        try:
            while True:
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # We save the data
                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                dataC = (dataK - 27315) / 100

                indx, indy = globals.centreROI
                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]
                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(globals.temp))

                names = ['image', 'shutter_pos', 'fixed_ROI', 'time_now']
                datas = [dataC, [globals.stimulus], [indx, indy], [momen]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

                if globals.temp < range[1] and cd == 0:
                    start_countdown = time.time()
                    print('START COUNTDOWN')
                    print(globals.momen)
                    cd += 1

                globals.momen = time.time() - start_countdown

                if globals.momen > globals.timeout:
                    print('Time out')
                    globals.stimulus = 0
                    print('Close shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    break

            print('Camera off')
            f.close()

        except Exception as e:
            errorloc(e)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def readShutterOff(self, output, target_temp, duration, r = 20, arduino = None):
        """
            Method function to read passively on a given ROI with the camera. 
            A timer starts when the temperature reaches the range temperature, 
            then it closes the shutter after the indicated time has passed.
            The required parameters are output, range and duration.
            It doesn't save the dynamic ROI.
            Globals: stimulus, timeout, pid_var, centreROI
        """
        global dev
        global devh
        import matplotlib as mpl

        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        print('File to save initialised')
        start = time.time()
        start_countdown = start * 2
        cd = 0

        time.sleep(1)

        globals.stimulus = 1
        print('Open shutter (camera)')
        arduino.arduino.write(struct.pack('>B', globals.stimulus))

        try:
            while True:
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # We save the data
                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                dataC = (dataK - 27315) / 100

                indx, indy = globals.centreROI
                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]
                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(globals.temp))

                names = ['image', 'shutter_pos', 'fixed_ROI', 'time_now']
                datas = [dataC, [globals.stimulus], [indx, indy], [globals.momen]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

                if globals.temp < target_temp and cd == 0:
                    start_countdown = time.time()
                    print('START COUNTDOWN')
                    print(globals.momen)
                    cd += 1

                globals.momen = time.time() - start_countdown

                if globals.momen > globals.timeout:
                    print('Time out')
                    globals.stimulus = 0
                    print('Close shutter (camera)')
                    arduino.arduino.write(struct.pack('>B', globals.stimulus))
                    break

            print('Camera off')
            f.close()

        except Exception as e:
            errorloc(e)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

################################### Developing phase


    def PIDSavePosMeanShuFixROI(self, output, r, cond, duration, dim = 'c', event1 = None):
        global dev
        global devh

        tiff_frameLOCAL = 1
        import matplotlib as mpl
        f = h5py.File("./{}.hdf5".format(output), "w")

        # print('camera pid on')
        try:

            while True:
                # time.sleep(0.01)
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                if globals.stimulus == 1:
                    # globals.frames['fixation_cross'][1] = 'on'
                    event1.set()

                # We save the data

                # dataC = (dataK - 27315) / 100

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                dataC = (dataK - 27315) / 100

                if dim == 'c':
                    threshold = (28*100) + 27315
                    indxT, indyT = np.where(dataK < threshold)

                    dataKT = dataK
                    dataKT[indxT, indyT] = dataKT[indxT, indyT] + 30000
                    dataCT = (dataKT - 27315) / 100
                    peakC = np.min(dataCT)
                    indxD, indyD = np.where(dataCT == peakC)

                elif dim == 'w':
                    peakC = np.max(dataC)
                    indxD, indyD = np.where(dataC == peakC)


                indx, indy = globals.centreROI
                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]
                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(round(np.mean(globals.temp), 2)))

                posss = np.repeat(globals.pid_var, len(dataC[0]))
                data_p = np.append(dataC, [posss], axis = 0)

                stimulus = np.repeat(globals.stimulus, len(dataC[0]))
                data_pp = np.append(data_p, [stimulus], axis = 0)

                coorF = np.repeat([indx, indy], len(dataC[0])/2)
                data_ppp = np.append(data_pp, [coorF], axis = 0)

                coorD = np.repeat([indxD[0], indyD[0]], len(dataC[0])/2)
                data_pppp = np.append(data_ppp, [coorD], axis = 0)

                # coorD = np.repeat([indxD, indyD], len(dataC[0])/2)
                # data_ppp = np.append(data_pp, [coorD], axis = 0)

                f.create_dataset(('image'+str(tiff_frameLOCAL)), data = data_pppp)
                tiff_frameLOCAL += 1

                # if keyboard.is_pressed('e'):
                #     break

                if time.time() > globals.timeout and globals.stimulus == 1:
                    print('Time out')
                    break

            event1.set()
            globals.stimulus = 0
            print('Camera off')
            f.close()

        finally:
            # print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def saveShutterCam(self, output, cam):
        global dev
        global devh
        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        v = h5py.File("./{}_video.hdf5".format(output), "w")

        camera = cv2.VideoCapture(cam)

        try:
            counter = 0
            while True:
                # time.sleep(0.01)
                data = q.get(True, 500)
                success, frame = camera.read()
                if data is None:
                    print('Data is none')
                    break

                # We save the data
                # print(type(data))

                dataC = (data - 27315) / 100
                peakC = np.min(dataC)

                globals.indx0, globals.indy0 = np.where(dataC == peakC)

                stimulus = np.repeat(globals.stimulus, len(data[0]))
                # print(globals.stimulus)
                data_p = np.append(data, [stimulus], axis = 0)

                coorF = np.repeat([globals.indx_saved, globals.indy_saved], len(data[0])/2)
                data_pp = np.append(data_p, [coorF], axis = 0)


                f.create_dataset(('image'+str(tiff_frameLOCAL)), data = data_pp)
                v.create_dataset(('image'+str(tiff_frameLOCAL)), data = frame)
                tiff_frameLOCAL += 1


                if globals.counter == 3:
                    print('We are done')
                    f.close()
                    v.close()
                    break
                # if keyboard.is_pressed('e'):  # globals.counter > globals.limit_counter:
                #     #Close file in which we are saving the stuff
                #     print('We are done')
                #     f.close()
                #     break

        finally:
            # print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)

    def saveShutter(self, output):
        global dev
        global devh
        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")

        edge = 30

        try:
            counter = 0
            while True:
                # time.sleep(0.01)
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # Get data
                subdataK = dataK[edge:edge + (120 - edge*2), edge:edge + (160 - edge*2)]
                minimoK = np.min(subdataK)

                # We get the min temp and shape to draw the ROI
                dataC = (dataK - 27315) / 100
                minimoC = (minimoK - 27315) / 100
                subdataC = (subdataK - 27315) / 100

                self.data = dataC

                r = 20

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                indx, indy = np.where(subdataC == minimoC)
                indx, indy = indx + edge, indy + edge

                stimulus = np.repeat(globals.stimulus, len(dataC[0]))

                data_p = np.append(dataC, [stimulus], axis = 0)

                coorF = np.repeat([globals.centreROI['control'][0], globals.centreROI['control'][1]], len(dataC[0])/2)
                data_pp = np.append(data_p, [coorF], axis = 0)

                mask = (xs[np.newaxis,:]-globals.centreROI['control'][1])**2 + (ys[:,np.newaxis]-globals.centreROI['control'][0])**2 < r**2
                roiC = dataC[mask]
                temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(round(np.mean(temp), 2)))

                momen = time.time()

                elapsed = np.repeat(momen, len(dataC[0]))
                data_ppp = np.append(data_pp, [elapsed], axis = 0)

                coorD = np.repeat([indx[0], indy[0]], len(dataC[0])/2)
                data_pppp = np.append(data_ppp, [coorD], axis = 0)

                f.create_dataset(('image'+str(tiff_frameLOCAL)), data = data_pppp)
                tiff_frameLOCAL += 1


                # if globals.counter == 3:
                #     print('We are done')
                #     f.close()
                #     break
                if keyboard.is_pressed('e'):  # globals.counter > globals.limit_counter:
                    #Close file in which we are saving the stuff
                    print('We are done')
                    f.close()
                    break

        finally:
            # print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)

    def saveShutterPos(self, output):
        global dev
        global devh
        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")

        edge = 30

        time_shutter = time.time()

        try:
            while True:
                # time.sleep(0.01)
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # Get data
                subdataK = dataK[edge:edge + (120 - edge*2), edge:edge + (160 - edge*2)]
                minimoK = np.min(subdataK)

                # We get the min temp and shape to draw the ROI
                dataC = (dataK - 27315) / 100
                minimoC = (minimoK - 27315) / 100
                subdataC = (subdataK - 27315) / 100

                self.data = dataC

                r = 20

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                indx, indy = np.where(subdataC == minimoC)
                indx, indy = indx + edge, indy + edge

                mask = (xs[np.newaxis,:] - globals.centreROI[1])**2 + (ys[:,np.newaxis] - globals.centreROI[0])**2 < r**2
                roiC = dataC[mask]
                temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(round(np.mean(temp), 2)))

                momen = time.time()

                f.create_dataset(('image'+str(tiff_frameLOCAL)), data = dataC)
                f.create_dataset(('pos'+str(tiff_frameLOCAL)), data = [globals.pos])
                f.create_dataset(('stimulus'+str(tiff_frameLOCAL)), data = [globals.stimulus])
                f.create_dataset(('fixed_coor'+str(tiff_frameLOCAL)), data = [globals.centreROI[0], globals.centreROI[1]])
                f.create_dataset(('dynamic_coor'+str(tiff_frameLOCAL)), data = [indx[0], indy[0]])
                f.create_dataset(('time'+str(tiff_frameLOCAL)), data = [momen])

                tiff_frameLOCAL += 1

                time_loop = time.time()
                time_elapsed = time_loop - time_shutter

                if time_elapsed > 20:
                    set_auto_ffc(devh)
                    time_shutter = time.time()

                if keyboard.is_pressed('e'):  # globals.counter > globals.limit_counter:
                    #Close file in which we are saving the stuff
                    print('We are done')
                    f.close()
                    break

        except:
            # print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass

    def rtMoL(self, output, event = None, cROI = globals.centreROI):
        """
            Method to perform method of limits with the thermal camera.
        """
        global dev
        global devh
        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        edge = 0
        shutter_opened = False

        start = time.time()

        try:
            counter = 0
            while True:
                print('start script')
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break
                # print(dataK)
                # Get data
                subdataK = dataK[edge:edge + (120 - edge*2), edge:edge + (160 - edge*2)]
                minimoK = np.min(subdataK)

                # We get the min temp and shape to draw the ROI
                dataC = (dataK - 27315) / 100
                minimoC = (minimoK - 27315) / 100
                subdataC = (subdataK - 27315) / 100

                momen = time.time() - start

                self.data = dataC

                r = 20

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                indxD, indyD = np.where(subdataC == minimoC)
                indxD, indyD = indxD + edge, indyD + edge

                x_diff = (indxD[0] - cROI[0])**2
                y_diff = (indyD[0] - cROI[1])**2

                eud = np.sqrt(x_diff + y_diff)
                eud = round(eud, 2)

                print(f'Euclidean distance between ROIs {eud}')

                if eud < 20:
                    mask = (xs[np.newaxis,:]- indyD[0])**2 + (ys[:,np.newaxis] - indxD[0])**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)
                    sROI = 1
                    print('Switched to DYNAMIC')
                else:
                    mask = (xs[np.newaxis,:]- cROI[1])**2 + (ys[:,np.newaxis] - cROI[0])**2 < r**2
                    roiC = dataC[mask]
                    globals.temp = round(np.mean(roiC), 2)
                    sROI = 0
                    print('Reading from FIXED')
                    
                names = ['image', 'stimulus', 'fixed_coor', 'dynamic_coor', 'time', 'eu', 'sROI']
                datas = [dataC, [globals.stimulus], [cROI[0], cROI[1]], [indxD[0], indyD[0]], [momen], [eud], [sROI]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1
                
                if momen > 2 and not shutter_opened:
                    if event != None:
                        event.set()
                    shutter_opened = True

                if keyboard.is_pressed('l') and shutter_opened:  # globals.counter > globals.limit_counter:
                    #Close file in which we are saving the stuff
                    if event != None:
                        event.set()
                    print('\nThermal recording finished\n')
                    globals.thres_temp = globals.temp
                    globals.stimulus = 0
                    f.close()
                    break

        except Exception as e:
            errorloc(e)

        finally:
            # print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass


    def rtMoLDiff(self, output, event = None, cROI = globals.centreROI):
        """
            Method to perform method of limits with the thermal camera.
        """
        global dev
        global devh
        tiff_frameLOCAL = 1
        f = h5py.File("./{}.hdf5".format(output), "w")
        shutter_opened = False
        diff_buffer = []
        start = time.time()
        r = 20
        xs = np.arange(0, 160)
        ys = np.arange(0, 120)

        try:
            while True:
                # print('start script')
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break
                # print(dataK)
                # Get data
                momen = time.time() - start
                
                dataC = (dataK - 27315) / 100

                if momen > 2 and not shutter_opened:
                    if event != None:
                        event.set()
                    shutter_opened = True
                    mean_diff_buffer = np.mean(diff_buffer, axis=0)
                    # print(np.shape(mean_diff_buffer))

                if momen > 1.5 and momen < 1.9:
                    diff_buffer.append(dataC)
                    # print(diff_buffer)

                if globals.stimulus == 2:
                    dif = mean_diff_buffer - dataC
                    maxdif = np.max(dif)
                    indxdf, indydf = np.where(dif == maxdif)
                    mask = (xs[np.newaxis,:]-indydf[0])**2 + (ys[:,np.newaxis]-indxdf[0])**2 < r**2
                    roiC = dataC[mask]
                    print(f'Temp: {round(np.mean(roiC), 2)}')
                    sROI = 1
                else:
                    indxdf, indydf = [-1], [-1]
                    sROI = 0

                # We get the min temp and shape to draw the ROI

                self.data = dataC

                names = ['image', 'stimulus', 'fixed_coor', 'diff_coor', 'time', 'sROI']
                datas = [dataC, [globals.stimulus], [cROI[0], cROI[1]], [indxdf[0], indydf[0]], [momen], [sROI]]

                saveh5py(names, datas, tiff_frameLOCAL, f)
                tiff_frameLOCAL += 1

                if keyboard.is_pressed('l') and shutter_opened:  # globals.counter > globals.limit_counter:
                    #Close file in which we are saving the stuff
                    if event != None:
                        event.set()
                    print('\nThermal recording finished\n')
                    globals.thres_temp = globals.temp
                    globals.stimulus = 4
                    f.close()
                    break

                if momen > 10:
                    print('\nTime out!\n')
                    if event != None:
                        event.set()
                    print('\nThermal recording finished\n')
                    globals.thres_temp = globals.temp
                    globals.stimulus = 4
                    f.close()
                    break

        except Exception as e:
            errorloc(e)

        finally:
            # print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            pass



    def savePosMinShu(self, output, event1 = None):
        global dev
        global devh
        global tiff_frame
        import matplotlib as mpl
        f = h5py.File("./{}.hdf5".format(output), "w")

        # mpl.rc('image', cmap='hot')
        # fig = plt.figure()
        # ax1 = fig.add_subplot(111)
        # fig.tight_layout()
        # dummy = np.zeros([120, 160])
        # img1 = ax1.imshow(dummy, interpolation='nearest', vmin = 5, vmax = 40, animated = True)
        # fig.colorbar(img1)
        # current_cmap = plt.cm.get_cmap()

        try:
            # start = time.time()
            print('start')
            while True:
                # time.sleep(0.01)
                data = q.get(True, 500)
                if data is None:
                    print('Data is none')
                    break

                # We save the data
                minimoK = np.min(data)
                minimo = (minimoK - 27315) / 100
                print('Minimo: ' + str(minimo))
                globals.temp = minimo
                # print(globals.shutter_state)

                if globals.shutter_state == 'open':
                    # print(event1)
                    event1.set()

                posss = np.repeat(globals.posZ, len(data[0]))
                data_p = np.append(data, [posss], axis = 0)

                if globals.shutter_state == 'open':
                    shutter = np.repeat(1, len(data[0]))
                    data_pp = np.append(data_p, [shutter], axis = 0)

                elif globals.shutter_state == 'close':
                    shutter = np.repeat(0, len(data[0]))
                    data_pp = np.append(data_p, [shutter], axis = 0)


                f.create_dataset(('image'+str(tiff_frame)), data = data_pp)
                tiff_frame += 1

                # ax1.clear()
                #
                # ax1.imshow(data)
                # plt.pause(0.0005)


                if keyboard.is_pressed('e'):  # globals.counter > globals.limit_counter:
                    #Close file in which we are saving the stuff
                    print('We are done')
                    end = time.time()
                    print(end - start)
                    # globals.counter = globals.limit_counter
                    f.close()
                    break

        finally:
            print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)

    def savePosMeanShu(self, output, r, event1 = None):
        global dev
        global devh
        global tiff_frame
        import matplotlib as mpl
        f = h5py.File("./{}.hdf5".format(output), "w")

        try:
            # start = time.time()
            print('start')
            while True:
                # time.sleep(0.01)
                data = q.get(True, 500)
                if data is None:
                    print('Data is none')
                    break

                # We save the data
                minimoK = np.min(data)
                minimoC = (minimoK - 27315) / 100
                dataC = (data - 27315) / 100

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                indx, indy = np.where(dataC == minimoC)

                mask = (xs[np.newaxis,:]-indy[0])**2 + (ys[:,np.newaxis]-indx[0])**2 < r**2
                roiC = dataC[mask]
                globals.temp = round(np.mean(roiC), 2)
                print('Mean:' + str(round(np.mean(globals.temp), 2)))

                if globals.shutter_state == 'open':
                    event1.set()

                posss = np.repeat(globals.posZ, len(data[0]))
                data_p = np.append(data, [posss], axis = 0)

                if globals.shutter_state == 'open':
                    shutter = np.repeat(1, len(data[0]))
                    data_pp = np.append(data_p, [shutter], axis = 0)

                elif globals.shutter_state == 'close':
                    shutter = np.repeat(0, len(data[0]))
                    data_pp = np.append(data_p, [shutter], axis = 0)


                f.create_dataset(('image'+str(tiff_frame)), data = data_pp)
                tiff_frame += 1

                if keyboard.is_pressed('e'):  # globals.counter > globals.limit_counter:
                    #Close file in which we are saving the stuff
                    print('We are done')

                    f.close()
                    break

        finally:
            print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)


################################### Developing phase

    def savePosMeanShuFixCam(self, output, r, cam, event1 = None):
        global dev
        global devh
        tiff_frameLOCAl = 1
        import matplotlib as mpl
        f = h5py.File("./{}.hdf5".format(output), "w")
        v = h5py.File("./{}_video.hdf5".format(output), "w")

        camera = cv2.VideoCapture(cam)

        try:
            # start = time.time()
            print('Start')
            print(globals.indx_saved, globals.indy_saved)
            while True:
                # time.sleep(0.01)
                dataK = q.get(True, 500)
                success, frame = camera.read()
                # print(frame)
                if dataK is None:
                    print('Data is none')
                    break

                # We save the data

                threshold = (28*100) + 27315
                indxT, indyT = np.where(dataK < threshold)
                dataC = (dataK - 27315) / 100
                dataKT = dataK

                dataKT[indxT, indyT] = dataKT[indxT, indyT] + 30000

                minimoK = np.min(dataKT)

                minimoC = (minimoK - 27315) / 100

                globals.temp = minimoC

                dataCT = (dataKT - 27315) / 100
                indxD, indyD = np.where(dataCT == minimoC)
                # print([indxD, indyD])

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                indx, indy = globals.indx_saved, globals.indy_saved

                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]
                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(round(np.mean(globals.temp), 2)))

                if globals.stimulus == 1:
                    # print('event set')

                    event1.set()

                posss = np.repeat(globals.posZ, len(dataC[0]))
                data_p = np.append(dataC, [posss], axis = 0)

                shutter = np.repeat(globals.stimulus, len(dataC[0]))
                data_pp = np.append(data_p, [shutter], axis = 0)

                coorF = np.repeat([indx, indy], len(dataC[0])/2)
                data_ppp = np.append(data_pp, [coorF], axis = 0)

                coorD = np.repeat([indxD[0], indyD[0]], len(dataC[0])/2)
                data_pppp = np.append(data_ppp, [coorD], axis = 0)

                f.create_dataset(('image'+str(tiff_frameLOCAl)), data = data_pppp)
                v.create_dataset(('image'+str(tiff_frameLOCAl)), data = frame)
                tiff_frameLOCAl += 1

                if keyboard.is_pressed('e'):
                    #Close file in which we are saving the stuff
                    print('We are done')

                    f.close()
                    v.close()
                    break

        finally:
            print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)

    def savePosMeanShuFix(self, output, r, event1 = None):
        global dev
        global devh
        tiff_frameLOCAl = 1
        import matplotlib as mpl
        f = h5py.File("./{}.hdf5".format(output), "w")

        edge = 30

        try:
            # start = time.time()
            print('Start')
            print(globals.indx_saved, globals.indy_saved)
            while True:
                # time.sleep(0.01)
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # We save the data

                # Get data
                subdataK = dataK[edge:edge + (120 - edge*2), edge:edge + (160 - edge*2)]
                minimoK = np.min(subdataK)

                # We get the min temp and shape to draw the ROI
                dataC = (dataK - 27315) / 100
                minimoC = (minimoK - 27315) / 100
                subdataC = (subdataK - 27315) / 100

                self.data = dataC

                r = 20

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                indxD, indyD = np.where(subdataC == minimoC)
                indxD, indyD = indxD + edge, indyD + edge

                indx, indy = globals.indx_saved, globals.indy_saved

                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]

                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(round(np.mean(globals.temp), 2)))

                if globals.stimulus == 1:
                    event1.set()

                posss = np.repeat(globals.posZ, len(dataC[0]))
                data_p = np.append(dataC, [posss], axis = 0)

                shutter = np.repeat(globals.stimulus, len(dataC[0]))
                data_pp = np.append(data_p, [shutter], axis = 0)

                coorF = np.repeat([indx, indy], len(dataC[0])/2)
                data_ppp = np.append(data_pp, [coorF], axis = 0)

                coorD = np.repeat([indxD[0], indyD[0]], len(dataC[0])/2)
                data_pppp = np.append(data_ppp, [coorD], axis = 0)

                f.create_dataset(('image'+str(tiff_frameLOCAl)), data = data_pppp)
                tiff_frameLOCAl += 1

                if keyboard.is_pressed('e'):
                    #Close file in which we are saving the stuff
                    print('We are done')

                    f.close()
                    break

        finally:
            print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)

    def savePosMeanfixShuGains(self, output, r, event1 = None):
        global dev
        global devh
        tiff_frameLOCAl = 1
        import matplotlib as mpl
        f = h5py.File("./{}.hdf5".format(output), "w")

        edge = 30

        try:
            print('Start')
            print(globals.centreROI)
            while True:
                # time.sleep(0.01)
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    break

                # We save the data

                # Get data
                subdataK = dataK[edge:edge + (120 - edge*2), edge:edge + (160 - edge*2)]
                minimoK = np.min(subdataK)

                # We get the min temp and shape to draw the ROI
                dataC = (dataK - 27315) / 100
                minimoC = (minimoK - 27315) / 100
                subdataC = (subdataK - 27315) / 100

                self.data = dataC

                r = 20

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                indxD, indyD = np.where(subdataC == minimoC)
                indxD, indyD = indxD + edge, indyD + edge

                indx, indy = globals.centreROI

                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]

                globals.temp = round(np.mean(roiC), 2)
                print('Mean: ' + str(round(np.mean(globals.temp), 2)))

                if globals.stimulus == 1:
                    event1.set()
                    
                f.create_dataset(('image'+str(tiff_frameLOCAl)), data = dataC)
                f.create_dataset(('pos'+str(tiff_frameLOCAl)), data = [globals.posZ])
                f.create_dataset(('stimulus'+str(tiff_frameLOCAl)), data = [globals.stimulus])
                f.create_dataset(('fixed_coor'+str(tiff_frameLOCAl)), data = [indx, indy])
                f.create_dataset(('dynamic_coor'+str(tiff_frameLOCAl)), data = [indxD[0], indyD[0]])
                f.create_dataset(('gains'+str(tiff_frameLOCAl)), data = [globals.Kp, globals.Ki, globals.Kd])
                f.create_dataset(('gain_outputs'+str(tiff_frameLOCAl)), data = [globals.proportional, globals.integral, globals.derivative])

                tiff_frameLOCAl += 1

                if keyboard.is_pressed('e'):
                    #Close file in which we are saving the stuff
                    print('We are done')

                    f.close()
                    break

        finally:
            print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)

    def outputData(self):
        import matplotlib as mpl
        mpl.rc('image', cmap='hot')

        edge = 30

        try:
            # print('in camera thread')
            dataK = q.get(True, 500)
            if dataK is None:
                print('Data is none')
                exit(1)

            # Get data
            subdataK = dataK[edge:edge + (120 - edge*2), edge:edge + (160 - edge*2)]
            minimoK = np.min(subdataK)

            # threshold = (28*100) + 27315
            # indxT, indyT = np.where(dataK < threshold)
            # dataK[indxT, indyT] = dataK[indxT, indyT] + 30000

            # We get the min temp and shape to draw the ROI
            dataC = (dataK - 27315) / 100
            minimoC = (minimoK - 27315) / 100
            subdataC = (subdataK - 27315) / 100

            self.data = dataC

            r = 20

            xs = np.arange(0, 160)
            ys = np.arange(0, 120)

            indx, indy = np.where(subdataC == minimoC)
            indx, indy = indx + edge, indy + edge

            mask = (xs[np.newaxis,:]-indy[0])**2 + (ys[:,np.newaxis]-indx[0])**2 < r**2
            roiC = dataC[mask]
            self.mean = round(np.mean(roiC), 2)

            self.circles = []

            for a, j in zip(indx, indy):
                cirD = plt.Circle((j, a), r, color='b', fill = False)
                self.circles.append(cirD)

            globals.indx0, globals.indy0  = indx[0], indy[0]
            print([indx0, indy0])

        except:
            pass


    def plotLiveROI(self, c_w = 'c', cut = 30, r = 20):
        import matplotlib as mpl
        mpl.rc('image', cmap='hot')

        global dev
        global devh
        global tiff_frame

        # plt.ion()

        fig = plt.figure()
        ax = plt.axes()

        fig.tight_layout()

        dummy = np.zeros([120, 160])

        img = ax.imshow(dummy, interpolation='nearest', vmin = self.vminT, vmax = self.vmaxT, animated = True)
        fig.colorbar(img)

        try:
            while True:
                # time.sleep(0.01)
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    exit(1)

                # We get the min temp and draw a circle
                if c_w == 'c':
                    threshold = (cut*100) + 27315
                    # print(threshold)
                    indxT, indyT = np.where(dataK < threshold)
                    dataK[indxT, indyT] = dataK[indxT, indyT] + 30000

                    minimoK = np.min(dataK)

                elif c_w == 'w':
                    threshold = (threshold*100) + 27315
                    indxT, indyT = np.where(dataK > threshold)
                    dataK[indxT, indyT] = dataK[indxT, indyT] - 30000

                    minimoK = np.max(dataK)

                dataC = (dataK - 27315) / 100

                r = r

                xs = np.arange(0, 160)
                ys = np.arange(0, 120)

                minimoC = (minimoK - 27315) / 100

                globals.temp = minimoC

                indx, indy = np.where(dataC == minimoC)

                mask = (xs[np.newaxis,:]-indy[0])**2 + (ys[:,np.newaxis]-indx[0])**2 < r**2
                roiC = dataC[mask]
                mean = round(np.mean(roiC), 2)
                # print(mean)

                circles = []

                for a, j in zip(indx, indy):
                    cirD = plt.Circle((j, a), r, color='b', fill = False)
                    circles.append(cirD)

                globals.indx0, globals.indy0  = indx[0], indy[0]

                ax.clear()
                ax.set_xticks([])
                ax.set_yticks([])

                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.imshow(dataC, vmin = self.vminT, vmax = self.vmaxT)
                ax.add_artist(circles[0])
                # print(globals.temp)
                plt.pause(0.0005)

                if keyboard.is_pressed('e'):
                    # cv2.destroyAllWindows()
                    frame = 1
                    plt.close(1)
                    print('Camera off')
                    break

        except Exception as e:
            print(e)
            # pass


    def plotLiveROINE(self, c_w = 'c', r = 20, record='n', output= None):

        mpl.rc('image', cmap='hot')

        print('Press "r" to refresh the shutter.')

        if record == 'y':
            print('Initialising file to save')
            tiff_frameLOCAL = 1
            f = h5py.File("./{}.hdf5".format(output), "w")
            start = time.time()

        else:
            print("Not recording")
    
        global dev
        global devh
        global tiff_frame

        fig = plt.figure(1)
        ax = plt.axes()

        fig.tight_layout()

        dummy = np.zeros([120, 160])

        img = ax.imshow(dummy, interpolation='nearest', vmin = self.vminT, vmax = self.vmaxT, animated = True)
        fig.colorbar(img)
        # fig.canvas.mpl_connect('close_event', lambda _: fig.canvas.manager.window.destroy()) 
        # plt.show(block=False)

        try:
            while True:
                    dataK = q.get(True, 500)
                    if dataK is None:
                        print('Data is none')
                        exit(1)

                    # We get the min temp and draw a circle
                    edgexl = 15
                    edgexr = 15
                    edgey = 0
                    if c_w == 'c':
                        subdataK = dataK[edgey:edgey + (120 - edgey*2), edgexl:(160 - edgexr)]
                        subdataC = (subdataK - 27315)/100
                        # print([subdataC <= 28.5])
                        # subdataC[subdataC <= 28.5] = 100
                        minimoC = np.min(subdataC)
                        # print(minimoK)
                        
                    elif c_w == 'w':
                        subdataK = dataK[edgey:edgey + (120 - edgey*2), edgexl:(160 - edgexr)]

                    dataC = (dataK - 27315) / 100
                    
                    # print(f'min: {minimoC}')
                    
                    xs = np.arange(0, 160)
                    ys = np.arange(0, 120)

                    globals.temp = minimoC

                    # print(indx, ind)

                    try:
                        # print('HERE')
                        indy, indx = np.where(subdataC == minimoC)
                        # print(indy[0], indx[0])
                        indx, indy = indy + edgey, indx + edgexl
                        mask = (xs[np.newaxis,:]-indy[0])**2 + (ys[:,np.newaxis]-indx[0])**2 < r**2
                    except:
                        continue
                    
                    roiC = dataC[mask]
                    mean = round(np.mean(roiC), 2)
                    print(f'Mean: {mean}')

                    circles = []

                    # print(indx, indy)
                    for a, j in zip(indx, indy):
                        cirD = plt.Circle((j, a), r, color='b', fill = False)
                        circles.append(cirD)

                    globals.indx0, globals.indy0  = indx[0], indy[0]

                    ax.clear()
                    ax.set_xticks([])
                    ax.set_yticks([])

                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_visible(False)
                    ax.spines['bottom'].set_visible(False)
                    ax.imshow(dataC, vmin = self.vminT, vmax = self.vmaxT)
                    ax.add_artist(circles[0])
                    # time.sleep(0.0005)
                    plt.pause(0.0005)
                    

                    if record == 'y':
                        print('Saving info to file')
                        momen = time.time() - start
                        
                        names = ['image', 'shutter_pos', 'fixed_ROI', 'dynamic_ROI', 'time_now']
                        datas = [dataC, [globals.stimulus], [globals.centreROI], [indx[0], indy[0]], [momen]]

                        saveh5py(names, datas, tiff_frameLOCAL, f)
                        tiff_frameLOCAL += 1
                        # print(tiff_frameLOCAL)

                    if keyboard.is_pressed('r'):
                        print('Manual FFC')
                        perform_manual_ffc(devh)
                        print_shutter_info(devh)

                    if keyboard.is_pressed('e'):
                        print('We are done')
                        plt.close('all')
                        plt.clf()
                        # fig.gcf()
                        # print(plt.get_fignums())
                        break

        except Exception as e:
            errorloc(e)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            # sys.exit()
            pass


    def plotLiveROINEcheck(self, c_w = 'c', r = 20, record='n', output= None):

        mpl.rc('image', cmap='hot')

        print('Press "r" to refresh the shutter.')

        if record == 'y':
            print('Initialising file to save')
            tiff_frameLOCAL = 1
            f = h5py.File("./{}.hdf5".format(output), "w")
            start = time.time()

        else:
            print("Not recording")

        global dev
        global devh
        global tiff_frame

        fig = plt.figure(1)
        ax = plt.axes()

        fig.tight_layout()

        dummy = np.zeros([120, 160])

        img = ax.imshow(dummy, interpolation='nearest', vmin = self.vminT, vmax = self.vmaxT, animated = True)
        fig.colorbar(img)
        # fig.canvas.mpl_connect('close_event', lambda _: fig.canvas.manager.window.destroy()) 
        # plt.show(block=False)

        try:
            while True:
                    dataK = q.get(True, 500)
                    if dataK is None:
                        print('Data is none')
                        exit(1)

                    # We get the min temp and draw a circle
                    edgexl = 15
                    edgexr = 15
                    edgey = 0
                    if c_w == 'c':
                        subdataK = dataK[edgey:edgey + (120 - edgey*2), edgexl:(160 - edgexr)]
                        subdataC = (subdataK - 27315)/100
                        # print([subdataC <= 28.5])
                        # subdataC[subdataC <= 28.5] = 100
                        minimoC = np.min(subdataC)
                        # print(minimoK)
                        
                    elif c_w == 'w':
                        subdataK = dataK[edgey:edgey + (120 - edgey*2), edgexl:(160 - edgexr)]

                    dataC = (dataK - 27315) / 100
                    
                    # print(f'min: {minimoC}')
                    
                    xs = np.arange(0, 160)
                    ys = np.arange(0, 120)

                    globals.temp = minimoC

                    # print(indx, ind)

                    try:
                        # print('HERE')
                        indy, indx = np.where(subdataC == minimoC)
                        # print(indy[0], indx[0])
                        indx, indy = indy + edgey, indx + edgexl
                        mask = (xs[np.newaxis,:]-indy[0])**2 + (ys[:,np.newaxis]-indx[0])**2 < r**2
                    except:
                        continue
                    
                    roiC = dataC[mask]
                    mean = round(np.mean(roiC), 2)
                    print(f'Mean: {mean}')

                    circles = []

                    # print(indx, indy)
                    for a, j in zip(indx, indy):
                        cirD = plt.Circle((j, a), r, color='b', fill = False)
                        circles.append(cirD)

                    globals.indx0, globals.indy0  = indx[0], indy[0]

                    ax.clear()
                    ax.set_xticks([])
                    ax.set_yticks([])

                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.spines['left'].set_visible(False)
                    ax.spines['bottom'].set_visible(False)
                    ax.imshow(dataC, vmin = self.vminT, vmax = self.vmaxT)
                    ax.add_artist(circles[0])
                    # time.sleep(0.0005)
                    plt.pause(0.0005)
                    

                    if record == 'y':
                        print('Saving info to file')
                        momen = time.time() - start
                        
                        names = ['image', 'shutter_pos', 'fixed_ROI', 'dynamic_ROI', 'time_now']
                        datas = [dataC, [globals.stimulus], [globals.centreROI], [indx[0], indy[0]], [momen]]

                        saveh5py(names, datas, tiff_frameLOCAL, f)
                        tiff_frameLOCAL += 1
                        # print(tiff_frameLOCAL)

                    if keyboard.is_pressed('r'):
                        print('Manual FFC')
                        perform_manual_ffc(devh)
                        print_shutter_info(devh)

                    if keyboard.is_pressed('e'):
                        # print(weDone)
                        if globals.weDone:
                            print('We are done')
                            plt.close('all')
                            plt.clf()
                            # fig.gcf()
                            # print(plt.get_fignums())
                            break

        except Exception as e:
            errorloc(e)

        finally:
            print('Stop streaming')
            # libuvc.uvc_stop_streaming(devh)
            # sys.exit()
            pass


    def LivePlotKernel(self, event1):

        global dev
        global devh
        global tiff_frame

        import matplotlib as mpl
        mpl.rc('image', cmap='hot')

        fig = plt.figure()

        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)

        fig.tight_layout()

        dummy = np.zeros([120, 160])

        img1 = ax1.imshow(dummy, interpolation='nearest', vmin = 5, vmax = 40, animated = True)
        img2 = ax1.imshow(dummy, interpolation='nearest', vmin = 5, vmax = 40, animated = True)

        fig.colorbar(img1)
        fig.colorbar(img2)

        current_cmap = plt.cm.get_cmap()
        current_cmap.set_bad(color='black')
        counter = 0

        try:
            while True:
                # time.sleep(0.01)
                data = q.get(True, 500)
                if data is None:
                    print('Data is none')
                    exit(1)

                data = (data - 27315) / 100

                under_threshold_indices = data < 18
                super_threshold_indices = data > 60

                maxC = 35
                data_absed = abs(data - maxC)

                data_absed[under_threshold_indices] = 0
                data_absed[super_threshold_indices] = 0

                Xin, Yin = np.mgrid[0:120, 0:160]
                paramsGau = moments(data_absed)
                dataGau = gaussian(*paramsGau)(Xin, Yin)
                event1.set()

                peak = paramsGau[0]
                peak =  maxC + 0 - peak
                globals.temp = peak
                print('Peak:  ' + str(round(peak)))
                # print('rolling')
                #
                ax1.clear()
                ax2.clear()

                # Raw Data

                ax1.set_xticks([])
                ax1.set_yticks([])

                ax1.spines['top'].set_visible(False)
                ax1.spines['right'].set_visible(False)
                ax1.spines['left'].set_visible(False)
                ax1.spines['bottom'].set_visible(False)
                ax1.imshow(data)
                plt.pause(0.0005)

                # Gaussian Kernel

                ax2.set_xticks([])
                ax2.set_yticks([])

                ax2.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
                ax2.spines['left'].set_visible(False)
                ax2.spines['bottom'].set_visible(False)
                ax2.imshow(dataGau)
                ### ax2.text(50, 10, 24, peak, color='black', fontsize = 12, weight = 'bold')
                plt.pause(0.0005)
                counter += 1
                event1.clear()

                if keyboard.is_pressed('e'):

                    print('We are done')
                    exit(1)

        finally:
            print('Stop streaming')
            libuvc.uvc_stop_streaming(devh)

    def StopStream(self):
        global devh
        print('Stop streaming')
        libuvc.uvc_stop_streaming(devh)

    def testSkinWarm(self, output, r):
        global tiff_frame

        f = h5py.File("./{}.hdf5".format(output), "w")

        mpl.rc('image', cmap='hot')

        fig = plt.figure()
        ax = plt.axes()

        fig.tight_layout()

        xs = np.arange(0, 160)
        ys = np.arange(0, 120)

        dummy = np.zeros([120, 160])

        img = ax.imshow(dummy, interpolation='nearest', vmin = self.vminT, vmax = self.vmaxT, animated = True)
        fig.colorbar(img)

        try:
            while True:
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    exit(1)

                dataC = (dataK - 27315) / 100

                maxC = np.max(dataC)
                indx, indy = np.where(dataC == maxC)

                mask = (xs[np.newaxis,:]-indy[0])**2 + (ys[:,np.newaxis]-indx[0])**2 < r**2
                roiC = dataC[mask]
                meanC = round(np.mean(roiC), 2)
                # print(meanC)

                f.create_dataset(('image'+str(tiff_frame)), data=dataC)
                tiff_frame += 1

                ax.clear()
                ax.set_xticks([])
                ax.set_yticks([])

                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.imshow(dataC, vmin = self.vminT, vmax = self.vmaxT)

                plt.pause(0.0005)

                # print(int(meanC * 100))

                globals.meanStr = str(int(meanC*100)) + '\n'
                # print(globals.meanStr)

                if keyboard.is_pressed('e'):
                    print('We are done')
                    f.close()
                    exit(1)

        finally:
            libuvc.uvc_stop_streaming(devh)

    def testSkinCold(self, output, r):
        global dev
        global devh
        global tiff_frame
        import matplotlib as mpl
        mpl.rc('image', cmap='hot')

        f = h5py.File("./{}.hdf5".format(output), "w")

        # fig = plt.figure()
        # ax = plt.axes()
        #
        # fig.tight_layout()
        #
        xs = np.arange(0, 160)
        ys = np.arange(0, 120)
        #
        # dummy = np.zeros([120, 160])
        #
        # img = ax.imshow(dummy, interpolation='nearest', vmin = vminT, vmax = vmaxT, animated = True)
        # fig.colorbar(img)

        try:
            print(globals.indx_saved, globals.indy_saved)
            while True:
                dataK = q.get(True, 500)
                if dataK is None:
                    print('Data is none')
                    exit(1)

                dataC = (dataK - 27315) / 100

                # maxC = np.max(dataC)
                indx, indy = globals.indx_saved, globals.indy_saved

                mask = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2
                roiC = dataC[mask]
                meanC = round(np.mean(roiC), 2)
                # print(meanC)

                f.create_dataset(('image'+str(tiff_frame)), data=dataC)
                tiff_frame += 1

                # ax.clear()
                # ax.set_xticks([])
                # ax.set_yticks([])
                #
                # ax.spines['top'].set_visible(False)
                # ax.spines['right'].set_visible(False)
                # ax.spines['left'].set_visible(False)
                # ax.spines['bottom'].set_visible(False)
                # ax.imshow(dataC, vmin = vminT, vmax = vmaxT)

                # plt.pause(0.0005)

                # print(int(meanC * 100))

                if meanC > 29.00:
                    globals.meanStr = "open"
                elif meanC < 27.00:
                    globals.meanStr = "close"

                # print(globals.meanStr)
                print(meanC)

                if keyboard.is_pressed('e'):
                    print('We are done')
                    f.close()
                    exit(1)

        finally:
            libuvc.uvc_stop_streaming(devh)


###############################################################
###################### FUNCTIONS ##############################
###############################################################

def saveh5py(names, datas, frame, file):
    if len(names) != len(datas):
        print('Names and datas have to be the same length')
        
    for n, d in zip(names, datas):
        # print(n, d)
        # print('{}'.format(n)+str(frame))
        file.create_dataset(('{}'.format(n)+str(frame)), data = d)

def generate_colour_map():
    """
    Conversion of the colour map from GetThermal to a numpy LUT:
        https://github.com/groupgets/GetThermal/blob/bb467924750a686cc3930f7e3a253818b755a2c0/src/dataformatter.cpp#L6
    """

    lut = np.zeros((256, 1, 3), dtype=np.uint8)

    #colorMaps
    colormap_grayscale = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12, 13, 13, 13, 14, 14, 14, 15, 15, 15, 16, 16, 16, 17, 17, 17, 18, 18, 18, 19, 19, 19, 20, 20, 20, 21, 21, 21, 22, 22, 22, 23, 23, 23, 24, 24, 24, 25, 25, 25, 26, 26, 26, 27, 27, 27, 28, 28, 28, 29, 29, 29, 30, 30, 30, 31, 31, 31, 32, 32, 32, 33, 33, 33, 34, 34, 34, 35, 35, 35, 36, 36, 36, 37, 37, 37, 38, 38, 38, 39, 39, 39, 40, 40, 40, 41, 41, 41, 42, 42, 42, 43, 43, 43, 44, 44, 44, 45, 45, 45, 46, 46, 46, 47, 47, 47, 48, 48, 48, 49, 49, 49, 50, 50, 50, 51, 51, 51, 52, 52, 52, 53, 53, 53, 54, 54, 54, 55, 55, 55, 56, 56, 56, 57, 57, 57, 58, 58, 58, 59, 59, 59, 60, 60, 60, 61, 61, 61, 62, 62, 62, 63, 63, 63, 64, 64, 64, 65, 65, 65, 66, 66, 66, 67, 67, 67, 68, 68, 68, 69, 69, 69, 70, 70, 70, 71, 71, 71, 72, 72, 72, 73, 73, 73, 74, 74, 74, 75, 75, 75, 76, 76, 76, 77, 77, 77, 78, 78, 78, 79, 79, 79, 80, 80, 80, 81, 81, 81, 82, 82, 82, 83, 83, 83, 84, 84, 84, 85, 85, 85, 86, 86, 86, 87, 87, 87, 88, 88, 88, 89, 89, 89, 90, 90, 90, 91, 91, 91, 92, 92, 92, 93, 93, 93, 94, 94, 94, 95, 95, 95, 96, 96, 96, 97, 97, 97, 98, 98, 98, 99, 99, 99, 100, 100, 100, 101, 101, 101, 102, 102, 102, 103, 103, 103, 104, 104, 104, 105, 105, 105, 106, 106, 106, 107, 107, 107, 108, 108, 108, 109, 109, 109, 110, 110, 110, 111, 111, 111, 112, 112, 112, 113, 113, 113, 114, 114, 114, 115, 115, 115, 116, 116, 116, 117, 117, 117, 118, 118, 118, 119, 119, 119, 120, 120, 120, 121, 121, 121, 122, 122, 122, 123, 123, 123, 124, 124, 124, 125, 125, 125, 126, 126, 126, 127, 127, 127, 128, 128, 128, 129, 129, 129, 130, 130, 130, 131, 131, 131, 132, 132, 132, 133, 133, 133, 134, 134, 134, 135, 135, 135, 136, 136, 136, 137, 137, 137, 138, 138, 138, 139, 139, 139, 140, 140, 140, 141, 141, 141, 142, 142, 142, 143, 143, 143, 144, 144, 144, 145, 145, 145, 146, 146, 146, 147, 147, 147, 148, 148, 148, 149, 149, 149, 150, 150, 150, 151, 151, 151, 152, 152, 152, 153, 153, 153, 154, 154, 154, 155, 155, 155, 156, 156, 156, 157, 157, 157, 158, 158, 158, 159, 159, 159, 160, 160, 160, 161, 161, 161, 162, 162, 162, 163, 163, 163, 164, 164, 164, 165, 165, 165, 166, 166, 166, 167, 167, 167, 168, 168, 168, 169, 169, 169, 170, 170, 170, 171, 171, 171, 172, 172, 172, 173, 173, 173, 174, 174, 174, 175, 175, 175, 176, 176, 176, 177, 177, 177, 178, 178, 178, 179, 179, 179, 180, 180, 180, 181, 181, 181, 182, 182, 182, 183, 183, 183, 184, 184, 184, 185, 185, 185, 186, 186, 186, 187, 187, 187, 188, 188, 188, 189, 189, 189, 190, 190, 190, 191, 191, 191, 192, 192, 192, 193, 193, 193, 194, 194, 194, 195, 195, 195, 196, 196, 196, 197, 197, 197, 198, 198, 198, 199, 199, 199, 200, 200, 200, 201, 201, 201, 202, 202, 202, 203, 203, 203, 204, 204, 204, 205, 205, 205, 206, 206, 206, 207, 207, 207, 208, 208, 208, 209, 209, 209, 210, 210, 210, 211, 211, 211, 212, 212, 212, 213, 213, 213, 214, 214, 214, 215, 215, 215, 216, 216, 216, 217, 217, 217, 218, 218, 218, 219, 219, 219, 220, 220, 220, 221, 221, 221, 222, 222, 222, 223, 223, 223, 224, 224, 224, 225, 225, 225, 226, 226, 226, 227, 227, 227, 228, 228, 228, 229, 229, 229, 230, 230, 230, 231, 231, 231, 232, 232, 232, 233, 233, 233, 234, 234, 234, 235, 235, 235, 236, 236, 236, 237, 237, 237, 238, 238, 238, 239, 239, 239, 240, 240, 240, 241, 241, 241, 242, 242, 242, 243, 243, 243, 244, 244, 244, 245, 245, 245, 246, 246, 246, 247, 247, 247, 248, 248, 248, 249, 249, 249, 250, 250, 250, 251, 251, 251, 252, 252, 252, 253, 253, 253, 254, 254, 254, 255, 255, 255];

    colormap_rainbow = [1, 3, 74, 0, 3, 74, 0, 3, 75, 0, 3, 75, 0, 3, 76, 0, 3, 76, 0, 3, 77, 0, 3, 79, 0, 3, 82, 0, 5, 85, 0, 7, 88, 0, 10, 91, 0, 14, 94, 0, 19, 98, 0, 22, 100, 0, 25, 103, 0, 28, 106, 0, 32, 109, 0, 35, 112, 0, 38, 116, 0, 40, 119, 0, 42, 123, 0, 45, 128, 0, 49, 133, 0, 50, 134, 0, 51, 136, 0, 52, 137, 0, 53, 139, 0, 54, 142, 0, 55, 144, 0, 56, 145, 0, 58, 149, 0, 61, 154, 0, 63, 156, 0, 65, 159, 0, 66, 161, 0, 68, 164, 0, 69, 167, 0, 71, 170, 0, 73, 174, 0, 75, 179, 0, 76, 181, 0, 78, 184, 0, 79, 187, 0, 80, 188, 0, 81, 190, 0, 84, 194, 0, 87, 198, 0, 88, 200, 0, 90, 203, 0, 92, 205, 0, 94, 207, 0, 94, 208, 0, 95, 209, 0, 96, 210, 0, 97, 211, 0, 99, 214, 0, 102, 217, 0, 103, 218, 0, 104, 219, 0, 105, 220, 0, 107, 221, 0, 109, 223, 0, 111, 223, 0, 113, 223, 0, 115, 222, 0, 117, 221, 0, 118, 220, 1, 120, 219, 1, 122, 217, 2, 124, 216, 2, 126, 214, 3, 129, 212, 3, 131, 207, 4, 132, 205, 4, 133, 202, 4, 134, 197, 5, 136, 192, 6, 138, 185, 7, 141, 178, 8, 142, 172, 10, 144, 166, 10, 144, 162, 11, 145, 158, 12, 146, 153, 13, 147, 149, 15, 149, 140, 17, 151, 132, 22, 153, 120, 25, 154, 115, 28, 156, 109, 34, 158, 101, 40, 160, 94, 45, 162, 86, 51, 164, 79, 59, 167, 69, 67, 171, 60, 72, 173, 54, 78, 175, 48, 83, 177, 43, 89, 179, 39, 93, 181, 35, 98, 183, 31, 105, 185, 26, 109, 187, 23, 113, 188, 21, 118, 189, 19, 123, 191, 17, 128, 193, 14, 134, 195, 12, 138, 196, 10, 142, 197, 8, 146, 198, 6, 151, 200, 5, 155, 201, 4, 160, 203, 3, 164, 204, 2, 169, 205, 2, 173, 206, 1, 175, 207, 1, 178, 207, 1, 184, 208, 0, 190, 210, 0, 193, 211, 0, 196, 212, 0, 199, 212, 0, 202, 213, 1, 207, 214, 2, 212, 215, 3, 215, 214, 3, 218, 214, 3, 220, 213, 3, 222, 213, 4, 224, 212, 4, 225, 212, 5, 226, 212, 5, 229, 211, 5, 232, 211, 6, 232, 211, 6, 233, 211, 6, 234, 210, 6, 235, 210, 7, 236, 209, 7, 237, 208, 8, 239, 206, 8, 241, 204, 9, 242, 203, 9, 244, 202, 10, 244, 201, 10, 245, 200, 10, 245, 199, 11, 246, 198, 11, 247, 197, 12, 248, 194, 13, 249, 191, 14, 250, 189, 14, 251, 187, 15, 251, 185, 16, 252, 183, 17, 252, 178, 18, 253, 174, 19, 253, 171, 19, 254, 168, 20, 254, 165, 21, 254, 164, 21, 255, 163, 22, 255, 161, 22, 255, 159, 23, 255, 157, 23, 255, 155, 24, 255, 149, 25, 255, 143, 27, 255, 139, 28, 255, 135, 30, 255, 131, 31, 255, 127, 32, 255, 118, 34, 255, 110, 36, 255, 104, 37, 255, 101, 38, 255, 99, 39, 255, 93, 40, 255, 88, 42, 254, 82, 43, 254, 77, 45, 254, 69, 47, 254, 62, 49, 253, 57, 50, 253, 53, 52, 252, 49, 53, 252, 45, 55, 251, 39, 57, 251, 33, 59, 251, 32, 60, 251, 31, 60, 251, 30, 61, 251, 29, 61, 251, 28, 62, 250, 27, 63, 250, 27, 65, 249, 26, 66, 249, 26, 68, 248, 25, 70, 248, 24, 73, 247, 24, 75, 247, 25, 77, 247, 25, 79, 247, 26, 81, 247, 32, 83, 247, 35, 85, 247, 38, 86, 247, 42, 88, 247, 46, 90, 247, 50, 92, 248, 55, 94, 248, 59, 96, 248, 64, 98, 248, 72, 101, 249, 81, 104, 249, 87, 106, 250, 93, 108, 250, 95, 109, 250, 98, 110, 250, 100, 111, 251, 101, 112, 251, 102, 113, 251, 109, 117, 252, 116, 121, 252, 121, 123, 253, 126, 126, 253, 130, 128, 254, 135, 131, 254, 139, 133, 254, 144, 136, 254, 151, 140, 255, 158, 144, 255, 163, 146, 255, 168, 149, 255, 173, 152, 255, 176, 153, 255, 178, 155, 255, 184, 160, 255, 191, 165, 255, 195, 168, 255, 199, 172, 255, 203, 175, 255, 207, 179, 255, 211, 182, 255, 216, 185, 255, 218, 190, 255, 220, 196, 255, 222, 200, 255, 225, 202, 255, 227, 204, 255, 230, 206, 255, 233, 208]

    colourmap_ironblack = [
        255, 255, 255, 253, 253, 253, 251, 251, 251, 249, 249, 249, 247, 247,
        247, 245, 245, 245, 243, 243, 243, 241, 241, 241, 239, 239, 239, 237,
        237, 237, 235, 235, 235, 233, 233, 233, 231, 231, 231, 229, 229, 229,
        227, 227, 227, 225, 225, 225, 223, 223, 223, 221, 221, 221, 219, 219,
        219, 217, 217, 217, 215, 215, 215, 213, 213, 213, 211, 211, 211, 209,
        209, 209, 207, 207, 207, 205, 205, 205, 203, 203, 203, 201, 201, 201,
        199, 199, 199, 197, 197, 197, 195, 195, 195, 193, 193, 193, 191, 191,
        191, 189, 189, 189, 187, 187, 187, 185, 185, 185, 183, 183, 183, 181,
        181, 181, 179, 179, 179, 177, 177, 177, 175, 175, 175, 173, 173, 173,
        171, 171, 171, 169, 169, 169, 167, 167, 167, 165, 165, 165, 163, 163,
        163, 161, 161, 161, 159, 159, 159, 157, 157, 157, 155, 155, 155, 153,
        153, 153, 151, 151, 151, 149, 149, 149, 147, 147, 147, 145, 145, 145,
        143, 143, 143, 141, 141, 141, 139, 139, 139, 137, 137, 137, 135, 135,
        135, 133, 133, 133, 131, 131, 131, 129, 129, 129, 126, 126, 126, 124,
        124, 124, 122, 122, 122, 120, 120, 120, 118, 118, 118, 116, 116, 116,
        114, 114, 114, 112, 112, 112, 110, 110, 110, 108, 108, 108, 106, 106,
        106, 104, 104, 104, 102, 102, 102, 100, 100, 100, 98, 98, 98, 96, 96,
        96, 94, 94, 94, 92, 92, 92, 90, 90, 90, 88, 88, 88, 86, 86, 86, 84, 84,
        84, 82, 82, 82, 80, 80, 80, 78, 78, 78, 76, 76, 76, 74, 74, 74, 72, 72,
        72, 70, 70, 70, 68, 68, 68, 66, 66, 66, 64, 64, 64, 62, 62, 62, 60, 60,
        60, 58, 58, 58, 56, 56, 56, 54, 54, 54, 52, 52, 52, 50, 50, 50, 48, 48,
        48, 46, 46, 46, 44, 44, 44, 42, 42, 42, 40, 40, 40, 38, 38, 38, 36, 36,
        36, 34, 34, 34, 32, 32, 32, 30, 30, 30, 28, 28, 28, 26, 26, 26, 24, 24,
        24, 22, 22, 22, 20, 20, 20, 18, 18, 18, 16, 16, 16, 14, 14, 14, 12, 12,
        12, 10, 10, 10, 8, 8, 8, 6, 6, 6, 4, 4, 4, 2, 2, 2, 0, 0, 0, 0, 0, 9,
        2, 0, 16, 4, 0, 24, 6, 0, 31, 8, 0, 38, 10, 0, 45, 12, 0, 53, 14, 0,
        60, 17, 0, 67, 19, 0, 74, 21, 0, 82, 23, 0, 89, 25, 0, 96, 27, 0, 103,
        29, 0, 111, 31, 0, 118, 36, 0, 120, 41, 0, 121, 46, 0, 122, 51, 0, 123,
        56, 0, 124, 61, 0, 125, 66, 0, 126, 71, 0, 127, 76, 1, 128, 81, 1, 129,
        86, 1, 130, 91, 1, 131, 96, 1, 132, 101, 1, 133, 106, 1, 134, 111, 1,
        135, 116, 1, 136, 121, 1, 136, 125, 2, 137, 130, 2, 137, 135, 3, 137,
        139, 3, 138, 144, 3, 138, 149, 4, 138, 153, 4, 139, 158, 5, 139, 163,
        5, 139, 167, 5, 140, 172, 6, 140, 177, 6, 140, 181, 7, 141, 186, 7,
        141, 189, 10, 137, 191, 13, 132, 194, 16, 127, 196, 19, 121, 198, 22,
        116, 200, 25, 111, 203, 28, 106, 205, 31, 101, 207, 34, 95, 209, 37,
        90, 212, 40, 85, 214, 43, 80, 216, 46, 75, 218, 49, 69, 221, 52, 64,
        223, 55, 59, 224, 57, 49, 225, 60, 47, 226, 64, 44, 227, 67, 42, 228,
        71, 39, 229, 74, 37, 230, 78, 34, 231, 81, 32, 231, 85, 29, 232, 88,
        27, 233, 92, 24, 234, 95, 22, 235, 99, 19, 236, 102, 17, 237, 106, 14,
        238, 109, 12, 239, 112, 12, 240, 116, 12, 240, 119, 12, 241, 123, 12,
        241, 127, 12, 242, 130, 12, 242, 134, 12, 243, 138, 12, 243, 141, 13,
        244, 145, 13, 244, 149, 13, 245, 152, 13, 245, 156, 13, 246, 160, 13,
        246, 163, 13, 247, 167, 13, 247, 171, 13, 248, 175, 14, 248, 178, 15,
        249, 182, 16, 249, 185, 18, 250, 189, 19, 250, 192, 20, 251, 196, 21,
        251, 199, 22, 252, 203, 23, 252, 206, 24, 253, 210, 25, 253, 213, 27,
        254, 217, 28, 254, 220, 29, 255, 224, 30, 255, 227, 39, 255, 229, 53,
        255, 231, 67, 255, 233, 81, 255, 234, 95, 255, 236, 109, 255, 238, 123,
        255, 240, 137, 255, 242, 151, 255, 244, 165, 255, 246, 179, 255, 248,
        193, 255, 249, 207, 255, 251, 221, 255, 253, 235, 255, 255, 24]

    def chunk(
            ulist, step): return map(
        lambda i: ulist[i: i + step],
        range(0, len(ulist),
               step))
    if (colorMapType == 1):
        chunks = chunk(colormap_rainbow, 3)
    elif (colorMapType == 2):
        chunks = chunk(colormap_grayscale, 3)
    else:
        chunks = chunk(colourmap_ironblack, 3)

    red = []
    green = []
    blue = []

    for chunk in chunks:
        red.append(chunk[0])
        green.append(chunk[1])
        blue.append(chunk[2])

    lut[:, 0, 0] = blue

    lut[:, 0, 1] = green

    lut[:, 0, 2] = red

    return lut

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
    moments """
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X*data).sum()/total
    y = (Y*data).sum()/total
    col = data[:, int(y)]
    width_x = np.sqrt(np.abs((np.arange(col.size)-y)**2*col).sum()/col.sum())
    row = data[int(x), :]
    width_y = np.sqrt(np.abs((np.arange(row.size)-x)**2*row).sum()/row.sum())
    height = data.max()
    return height, x, y, width_x, width_y

def fitgaussian(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(data)
    errorfunction = lambda p: np.ravel(gaussian(*p)(*np.indices(data.shape)) -
                                 data)
    p, success = optimize.leastsq(errorfunction, params)
    return p

def gaussian(height, center_x, center_y, width_x, width_y):
    """Returns a gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x,y: height*np.exp(
                -(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)



######### Useuful links ###############

## Image analysis
# https://www.youtube.com/watch?v=-ZrDjwXZGxI

## https://lepton.flir.com/application-notes/people-finding-with-a-lepton/
## https://github.com/groupgets/pylepton/blob/master/pylepton/Lepton.py

##Windows
#https://lepton.flir.com/wp-content/uploads/2015/06/PureThermal-2-Basic-Lepton-Features.pdf
# https://lepton.flir.com/getting-started/quick-start-guide-getting-started-programing-with-python-sdk/
# https://lepton.flir.com/wp-content/uploads/2015/06/Advanced-Lepton-Usage-on-Windows.pdf

##Raspberr pi
# https://github.com/Kheirlb/purethermal1-uvc-capture
# https://lepton.flir.com/forums/topic/recording-and-viewing-raw-data/
#

## Video communication
# https://github.com/groupgets/purethermal1-uvc-capture


## MY TRASH
# def thresStream(self):
#     global dev
#     global devh
#     frame_width = 640
#     frame_height = 480
#
#     try:
#         while True:
#             data = q.get(True, 500)
#             if data is None:
#                 break
#
#
#             data = cv2.resize(data[:,:], (640, 480))
#
#             # img = raw_to_8bit(data)
#             img = cv2.LUT(raw_to_8bit(data), generate_colour_map())
#             print(img)
#            # img = cv2.LUT(raw_to_8bit(data), generate_colour_map())
#
#
#             cv2.imshow('Just streaming thermal video...', img)
#             # Press Q on keyboard to stop recording
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#               # When everything done, release the video capture and video write objects
#
#                 # Closes all the frames
#                 cv2.destroyAllWindows()
#                 exit(1)
#
#     finally:
#         libuvc.uvc_stop_streaming(devh)




### For easy & dirty python scripts
# from ioctl_numbers_camera import _IOR, _IOW
# from fcntl import ioctl
#
# ############### Dirty and easy objects to control thermal camera that don't work ###########
# SPI_IOC_MAGIC   = ord("k")
#
# SPI_IOC_RD_MODE          = _IOR(SPI_IOC_MAGIC, 1, "=B")
# SPI_IOC_WR_MODE          = _IOW(SPI_IOC_MAGIC, 1, "=B")
#
# SPI_IOC_RD_LSB_FIRST     = _IOR(SPI_IOC_MAGIC, 2, "=B")
# SPI_IOC_WR_LSB_FIRST     = _IOW(SPI_IOC_MAGIC, 2, "=B")
#
# SPI_IOC_RD_BITS_PER_WORD = _IOR(SPI_IOC_MAGIC, 3, "=B")
# SPI_IOC_WR_BITS_PER_WORD = _IOW(SPI_IOC_MAGIC, 3, "=B")
#
# SPI_IOC_RD_MAX_SPEED_HZ  = _IOR(SPI_IOC_MAGIC, 4, "=I")
# SPI_IOC_WR_MAX_SPEED_HZ  = _IOW(SPI_IOC_MAGIC, 4, "=I")
#
# class Lepton(object):
#   """Communication class for FLIR Lepton module on SPI
#
#   Args:
#     spi_dev (str): Location of SPI device node. Default '/dev/spidev0.0'.
#   """
#
#   ROWS = 60
#   COLS = 80
#   VOSPI_FRAME_SIZE = COLS + 2
#   VOSPI_FRAME_SIZE_BYTES = VOSPI_FRAME_SIZE * 2
#   MODE = 0
#   BITS = 8
#   SPEED = 18000000
#
#   def __init__(self, spi_dev = "/dev/spidev0.0"):
#     self.__spi_dev = spi_dev
#     self.__txbuf = np.zeros(Lepton.VOSPI_FRAME_SIZE, dtype=np.uint16)
#
#     # struct spi_ioc_transfer {
#     #   __u64     tx_buf;
#     #   __u64     rx_buf;
#     #   __u32     len;
#     #   __u32     speed_hz;
#     #   __u16     delay_usecs;
#     #   __u8      bits_per_word;
#     #   __u8      cs_change;
#     #   __u8      tx_nbits;
#     #   __u8      rx_nbits;
#     #   __u16     pad;
#     # };
#     self.__xmit_struct = struct.Struct("=QQIIHBBBBH")
#     self.__xmit_buf = ctypes.create_string_buffer(self.__xmit_struct.size)
#     self.__msg = _IOW(SPI_IOC_MAGIC, 0, self.__xmit_struct.format)
#     self.__capture_buf = np.zeros((60, 82, 1), dtype=np.uint16)
#
#   def __enter__(self):
#     self.__handle = open(self.__spi_dev, "w+")
#
#     ioctl(self.__handle, SPI_IOC_RD_MODE, struct.pack("=B", Lepton.MODE))
#     ioctl(self.__handle, SPI_IOC_WR_MODE, struct.pack("=B", Lepton.MODE))
#
#     ioctl(self.__handle, SPI_IOC_RD_BITS_PER_WORD, struct.pack("=B", Lepton.BITS))
#     ioctl(self.__handle, SPI_IOC_WR_BITS_PER_WORD, struct.pack("=B", Lepton.BITS))
#
#     ioctl(self.__handle, SPI_IOC_RD_MAX_SPEED_HZ, struct.pack("=I", Lepton.SPEED))
#     ioctl(self.__handle, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack("=I", Lepton.SPEED))
#
#     return self
#
#   def __exit__(self, type, value, tb):
#     self.__handle.close()
#
#   def capture(self, data_buffer = None):
#     """Capture a frame of data.
#
#     Captures 80x60 uint16 array of non-normalized (raw 12-bit) data. Returns that frame and a frame_id (which
#     is currently just the sum of all pixels). The Lepton will return multiple, identical frames at a rate of up
#     to ~27 Hz, with unique frames at only ~9 Hz, so the frame_id can help you from doing additional work
#     processing duplicate frames.
#
#     Args:
#       data_buffer (numpy.ndarray): Optional. If specified, should be ``(60,80,1)`` with `dtype`=``numpy.uint16``.
#
#     Returns:
#       tuple consisting of (data_buffer, frame_id)
#     """
#
#     if data_buffer is None:
#       data_buffer = np.ndarray((Lepton.ROWS, Lepton.COLS, 1), dtype=np.uint16)
#     elif data_buffer.ndim < 2 or data_buffer.shape[0] < Lepton.ROWS or data_buffer.shape[1] < Lepton.COLS or data_buffer.itemsize < 2:
#       raise Exception("Provided input array not large enough")
#
#     rxs = self.__capture_buf.ctypes.data
#     rxs_end = rxs + Lepton.ROWS * Lepton.VOSPI_FRAME_SIZE_BYTES
#     txs = self.__txbuf.ctypes.data
#     synced = False
#     while rxs < rxs_end:
#       self.__xmit_struct.pack_into(self.__xmit_buf, 0, txs, rxs, Lepton.VOSPI_FRAME_SIZE_BYTES, Lepton.SPEED, 0, Lepton.BITS, 0, Lepton.BITS, Lepton.BITS, 0)
#       ioctl(self.__handle, self.__msg, self.__xmit_buf)
#       if synced or self.__capture_buf[0,0] & 0x0f00 != 0x0f00:
#         synced = True
#         rxs += Lepton.VOSPI_FRAME_SIZE_BYTES
#
#     data_buffer[0:Lepton.ROWS,0:Lepton.COLS] = self.__capture_buf[0:Lepton.ROWS,2:Lepton.VOSPI_FRAME_SIZE]
#     data_buffer.byteswap(True)
#
#     # TODO: turn on telemetry to get real frame id, sum on this array is fast enough though (< 500us)
#     return data_buffer, data_buffer.sum()
