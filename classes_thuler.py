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
        """
            Here we count how many pixels between the given thermal ranges are in each row and column
        """
        hor_y_pixels = []
        ver_x_pixels = []

        for i in self.img:
            hori = np.count_nonzero(i)
            hor_y_pixels.append(hori)

        for j in self.img.T:
            veri = np.count_nonzero(j)
            ver_x_pixels.append(veri)

        self.hor_y_pixels_raw = np.asarray(hor_y_pixels, dtype = 'float')
        self.ver_x_pixels_raw = np.asarray(ver_x_pixels, dtype = 'float')

        self.ar_hor_y_pixels = self.hor_y_pixels_raw.copy() 
        self.ar_ver_x_pixels = self.ver_x_pixels_raw.copy() 

    def interpolation(self, hor_threshold, ver_threshold):
        """
            Here we threshold rows and columns to remove arms of the ruler. 
            Then we extrapolate to obtain two straight 2D rulers (horizontal and vertical)
        """
        self.ar_hor_y_pixels[self.ar_hor_y_pixels > hor_threshold] = np.nan
        self.ar_ver_x_pixels[self.ar_ver_x_pixels > ver_threshold] = np.nan

        # THIS SECTION IS NOT DONE
        y_nans, Yx = nan_helper(self.ar_hor_y_pixels)
        x_nans, Xx = nan_helper(self.ar_ver_x_pixels)

        self.ar_hor_y_pixels[y_nans] = np.interp(Yx(y_nans), Yx(~y_nans), self.ar_hor_y_pixels[~y_nans])
        self.ar_ver_x_pixels[x_nans] = np.interp(Xx(x_nans), Xx(~x_nans), self.ar_ver_x_pixels[~x_nans])

        coef_Y = np.polyfit(np.arange(len(self.ar_hor_y_pixels)), self.ar_hor_y_pixels,1)
        self.fn_hor_y = np.poly1d(coef_Y)

        coef_X = np.polyfit(np.arange(len(self.ar_ver_x_pixels)), self.ar_ver_x_pixels,1)
        self.fn_ver_x = np.poly1d(coef_X)

        # poly1d_fn is now a function which takes in x and returns an estimate for y
        self.fitted_hor_pixels_y = self.fn_hor_y(np.arange(len(self.ar_hor_y_pixels)))
        self.fitted_ver_pixels_x = self.fn_ver_x(np.arange(len(self.ar_ver_x_pixels)))

    def calibrate(self, mm = 4):
        """
        We calculate the width and length of each pixel and we create a grid
        """
        self.h_colum_y = mm/np.asarray(self.fitted_hor_pixels_y)
        self.v_colum_x = mm/np.asarray(self.fitted_ver_pixels_x)

        self.y_hor_count = np.tile(self.h_colum_y, (len(self.v_colum_x),1))
        self.x_ver_count = np.tile(self.v_colum_x, (len(self.h_colum_y),1))

    def measure(self, r, inds):
        """
        We measure the size of each pixel in the ROI  
        """
        indx, indy = inds
        xs = np.arange(0, 160)
        ys = np.arange(0, 120)
        roi = (xs[np.newaxis,:]-indy)**2 + (ys[:,np.newaxis]-indx)**2 < r**2

        self.masked_hor_count_y = np.where(roi.T == False, 0, self.y_hor_count)
        self.masked_ver_count_x = np.where(roi == False, 0, self.x_ver_count)

        self.spot_heights = np.sum(self.masked_hor_count_y, axis = 1)
        self.spot_widths = np.sum(self.masked_ver_count_x, axis = 1)
    

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

