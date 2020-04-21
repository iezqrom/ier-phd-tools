import time
import sys
import os

import cv2
import h5py
import matplotlib.pyplot as plt
import numpy as np
from numpy import inf

class Thuler(object):
    def __init__(self, name):
        """
        Class to apply spatial calibration on the thermal camera
        """
        self.read = h5py.File('./{}.hdf5'.format(name), 'r')    
        print(len(self.read.keys()))
    
    def plot_ruler(self, n_image, low_b, high_b):
        """
        This method plots the heatmap of the ruler
        """
        self.low_b = low_b
        self.high_b = high_b
        self.img = self.read['image{}'.format(n_image)][:]

        current_cmap = plt.cm.get_cmap()
        current_cmap.set_bad(color='black')

        under_threshold_indices = self.img < low_b
        super_threshold_indices = self.img > high_b

        self.img[under_threshold_indices] = 0
        self.img[super_threshold_indices] = 0

        plt.imshow(self.img, cmap = 'hot', vmin = low_b, vmax = high_b)
        plt.colorbar()

    def pixelCount(self):
        hor_row_pixels = []
        ver_column_pixels = []

        for i in self.img:
            hori = np.count_nonzero(i)
            hor_row_pixels.append(hori)

        for j in self.img.T:
            veri = np.count_nonzero(j)
            ver_column_pixels.append(veri)

        self.ar_hor_row_pixels = np.asarray(hor_row_pixels, dtype = 'float')
        self.ar_ver_column_pixels = np.asarray(ver_column_pixels, dtype = 'float')

    def interpolation(self, hor_threshold, ver_threshold):
        self.ar_hor_row_pixels[self.ar_hor_row_pixels > hor_threshold] = np.nan
        self.ar_ver_column_pixels[self.ar_ver_column_pixels > ver_threshold] = np.nan

        self.hor_non_nan = self.ar_hor_row_pixels[np.logical_not(np.isnan(self.ar_hor_row_pixels))]
        self.ver_non_nan = self.ar_ver_column_pixels[np.logical_not(np.isnan(self.ar_ver_column_pixels))]

        self.coef_hor = np.polyfit(np.arange(len(self.hor_non_nan)), self.hor_non_nan,1)
        self.fn_hor = np.poly1d(self.coef_hor)

        self.coef_ver = np.polyfit(np.arange(len(self.ver_non_nan)), self.ver_non_nan,1)
        self.fn_ver = np.poly1d(self.coef_ver)
        # poly1d_fn is now a function which takes in x and returns an estimate for y

        self.fitted_hor_pixels = self.fn_hor(np.arange(len(self.ar_hor_row_pixels)))
        self.fitted_ver_pixels = self.fn_ver(np.arange(len(self.ar_ver_column_pixels)))

    def calibrate(self, mm = 4):
        """
        We calculate the width and length of each pixel and we create a grid
        """
        self.h_colum = mm/np.asarray(self.fitted_hor_pixels)
        self.v_colum = mm/np.asarray(self.fitted_ver_pixels)

        self.x_hor_count = np.tile(self.h_colum, (len(self.v_colum),1))
        self.y_ver_count = np.tile(self.v_colum, (len(self.h_colum),1))

    def measure(self, roi):
        """
        We measure the size of the 
        """
        self.masked_hor_count = np.where(roi.T == False, 0, self.x_hor_count)
        self.masked_ver_count = np.where(roi == False, 0, self.y_ver_count)

        self.spot_widths = np.sum(self.masked_hor_count, axis = 1)
        self.spot_heights = np.sum(self.masked_ver_count, axis = 1)
    


def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    """

    return np.isnan(y), lambda z: z.nonzero()[0]

