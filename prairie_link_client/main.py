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


import plugin_viewer
import serial

# from utils import threaded



class PLUI(QtWidgets.QMainWindow, plugin_viewer.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PLUI, self).__init__(parent)
        self.setupUi(self)

        self._dummy_img = None
        self.open_prairie_link()


        self.ch1Button.clicked.connect(self.set_ch1_active)
        self.ch2Button.clicked.connect(self.set_ch2_active)
        self.ch1_active = False
        self.ch2_active = False

        self.numSlicesInput.editingFinished.connect(self.set_num_slices)
        self.num_slices = 1
        self.numSlicesInput.setText('1')

        self.plugin_plot = self.pluginViewer.getPlotItem()
        self.plugin_curr_image = pg.ImageItem()
        self.plugin_plot.addItem(self.plugin_curr_image)
        self.plugin_plot.showAxis('left', False)
        self.plugin_plot.showAxis('bottom', False)
        self.plugin_plot.setAspectLocked(lock=True, ratio=1)
        self.plugin_plot.invertY(True)
        # self.plugin_plot.invertX(True)
        self.set_channel_image()



        self.plugin_timer = QtCore.QTimer()
        self.plugin_timer.timeout.connect(self.set_channel_image)
        #TODO: set timeout based on number of lines in frame
        self.plugin_timer.start()


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




def main():
    app = QApplication(sys.argv)
    form = PLUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()

