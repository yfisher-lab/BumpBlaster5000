import os
import pathlib
import threading
import queue
import numpy as np
import win32com.client
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
import sys


import plugin_viewer_2
import serial

# from utils import threaded



class PLUI(QtWidgets.QMainWindow, plugin_viewer_2.Ui_MainWindow):
    def __init__(self, parent=None, pl_connect = True):
        super(PLUI, self).__init__(parent)
        self.setupUi(self)

        self._dummy_img = None
        if pl_connect:
            self.open_prairie_link()


        self.ch1Button.clicked.connect(self.set_ch1_active)
        self.ch2Button.clicked.connect(self.set_ch2_active)
        self.ch1_active = False
        self.ch2_active = False

        self.numSlicesInput.editingFinished.connect(self.set_num_slices)
        self.num_slices = 1
        self.numSlicesInput.setText('1')

        self.ch1_plot = self.ch1Viewer.getPlotItem()
        self.ch1_curr_image = pg.ImageItem()
        self.ch1_plot.addItem(self.plugin_curr_image)
        self.ch1_plot.showAxis('left', False)
        self.ch1_plot.showAxis('bottom', False)
        self.ch1_plot.setAspectLocked(lock=True, ratio=1)
        self.ch1_plot.invertY(True)

        # add placeholder for EB or PB ROIs
        self.set_ch1_image()
        self.ch1_EB_rois = None
        self.ch1_PB_rois = None

        self.ch2_plot = self.ch2Viewer.getPlotItem()
        self.ch2_curr_image = pg.ImageItem()
        self.ch2_plot.addItem(self.plugin_curr_image)
        self.ch2_plot.showAxis('left', False)
        self.ch2_plot.showAxis('bottom', False)
        self.ch2_plot.setAspectLocked(lock=True, ratio=1)
        self.ch2_plot.invertY(True)

        # add placeholder for EB or PB ROIs
        self.set_ch2_image()
        self.ch2_EB_rois = None
        self.ch2_PB_rois = None



        self.plugin_timer = QtCore.QTimer()
        self.plugin_timer.timeout.connect(self.set_channel_image)
        #TODO: set timeout based on number of lines in frame
        self.plugin_timer.start()

        #TODO: add serial port to listen to commands from Teensy



        #TODO: add 2nd plot for ch1 vs ch2 and update appropriately

        #TODO: add roi drawing, segmenting, df/f, sending data over serial port



    def open_prairie_link(self):

        self.pl = win32com.client.Dispatch("PrairieLink.Application")
        self.pl.Connect()

        self._pl_active = threading.Event()
        self._pl_active.set()

        self._dummy_img = np.zeros((self.pl.LinesPerFrame(), self.pl.PixelsPerLine(), 3))




    def set_ch1_active(self):
        '''

        :return:
        '''
        self.ch1_active = True

    def set_ch2_active(self):
        '''

        :return:
        '''
        self.ch2_active = True

    def set_num_slices(self):
        '''

        :return:
        '''
        num_slices_txt = self.numSlicesInput.text()
        try:
            self.num_slices = int(num_slices_txt)
        except ValueError:
            self.numSlicesInput.setText('1')
            self.num_slices = 1




    def set_channel_image(self):
        '''

        :return:
        '''

        #TODO: set channel to average slices
        # print(self.channel_image())
        if not (self.ch1_active and self.ch2_active):
            self.plugin_curr_image.setImage(self.channel_image())
        else: # fuse channels
            (r, g) = self.channel_image
            self._dummy_img[:,:,0], self._dummy_img[:,:,1], self._dummy_img[:,:,2] = r, g, g
            self.plugin_curr_image.setImage(self._dummy_img)


    # @property
    def channel_image(self):
        '''

        :return:
        '''

        if self.ch1_active and not self.ch2_active:
            return np.array(self.pl.GetImage_2(1, self.pl.PixelsPerLine(), self.pl.LinesPerFrame())).T
        elif not self.ch1_active and self.ch2_active:
            return np.array(self.pl.GetImage_2(2, self.pl.PixelsPerLine(), self.pl.LinesPerFrame())).T
        elif self.ch1_active and self.ch2_active:
            return (np.array(self.pl.GetImage_2(1, self.pl.PixelsPerLine(), self.pl.LinesPerFrame())),
                    np.array(self.pl.GetImage_2(2, self.pl.PixelsPerLine(), self.pl.LinesPerFrame())))

    def start_PB_roi(self):

        daisychain = pg.MultiRectROI()

    def get_PB_phase(self):
        return

    def start_EB_roi(self):

        outerEllipse = pg.EllipseROI([50, 50], [50, 50], pen=(3, 9))
        innerEllipse = pg.EllipseROI([50, 50], [10, 10], pen=(3, 9))

        # get center of inner ellipse
        # either innerEllipse.pos() or calculate from masked image

    def _divide_EB_roi(self, resolution = 16):

        # pass
        # x0, y0 = center of inner ellipse

        # make masks

        if resolution == 8:
            self._8eb_rois()
        elif resolution == 16:
            self._16eb_rois()

    def _8eb_rois(self):

        masks = []

    def _16eb_rois(self):

        masks = []

    def get_EB_phase(self):

        #TODO: add toggle button that says which channel is numerator and which is denominator


        # if numerator and denominator are same channel
            # read baseline from a v low pass buffer

        # if numerator and denom are different channels
            # low pass denom

        # calculate df/f for each wedge

        # calculate mean resultant vector







def main():
    app = QApplication(sys.argv)
    form = PLUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()

