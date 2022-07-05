import os
import pathlib
import threading
import queue
import numpy as np
import win32com.client
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
from PyQt5.QtGui import QPixmap, QImage
from functools import partial
import sys

import gui
import serial

from camera import Flea3Cam


import fictrac_utils as ft_utils
from utils import threaded



class PLUI(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PLUI, self).__init__(parent)
        self.setupUi(self)

        self.open_prairie_link()


        self.ch1Button.clicked.connect(self.set_ch1_active)
        self.ch2Button.clicked.connect(self.set_ch2_active)
        self.ch1_active = False
        self.ch2_active = False

        self.numSlicesInput.editingFinished.connect(self.set_num_slices)
        self.numSlicesInput.setText('1')

        self.plugin_plot = self.pluginViewer.getPlotItem()
        self.plugin_curr_image = pg.ImageItem()
        self.plugin_plot.addItem(self.plugin_curr_image)
        self.plugin_plot.showAxis('left',False)
        self.plugin_plot.showAxis('bottom', False)
        self.plugin_plot.setAspectLocked(lock=True, ratio=1)
        self.plugin_curr_image.setImage(self.set_channel_image)


        self.plugin_timer = QtCore.QTimer()
        self.plugin_timer.timeout.connect(self.set_channel_image)
        self.plugin_timer.start()


    def open_prairie_link(self):

        self.pl = win32com.client.Dispatch("PrairieLink.Application")
        self._pl_active = threading.Event()
        self._pl_active.set()




    def set_ch1_active(self):
        '''

        :return:
        '''
        pass

    def set_ch2_active(self):
        '''

        :return:
        '''
        pass

    def set_num_slices(self):
        '''

        :return:
        '''
        pass


    def set_channel_image(self):
        '''

        :return:
        '''
        pass

    @property
    def get_channel_image(self):
        '''

        :return:
        '''

        if self.ch1_active and not self.ch2_active:
            return self.pl.GetImage_2(1, self.pl.pxls_per_line, self.pl.lines_per_frame)
        elif not self.ch1_active and self.ch2_active:
            return self.pl.GetImage_2(1, self.pl.pxls_per_line, self.pl.lines_per_frame)
        elif self.ch1_active and self.ch2_active:
            return (self.pl.GetImage_2(1, self.pl.pxls_per_line, self.pl.lines_per_frame),
                    self.pl.GetImage_2(2, self.pl.pxls_per_line, self.pl.lines_per_frame))





