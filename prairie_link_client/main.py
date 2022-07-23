import os
import pathlib
import itertools
import threading
import queue
import sys

import numpy as np
import win32com.client
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
import serial


import plugin_viewer


# from utils import threaded



class PLUI(QtWidgets.QMainWindow, plugin_viewer.Ui_MainWindow):
    def __init__(self, parent=None, pl_connect = True):
        super(PLUI, self).__init__(parent)
        self.setupUi(self)

        #connect to prairie link
        self.pl = None
        if pl_connect:
            self.open_prairie_link()
            self._pl_active = threading.Event()
            self._dummy_img = None


        # connect channel view buttons
        self.ch1ViewButton.stateChanged.connect(self.set_ch1_active)
        self.ch1_active = False
        self._ch1_buffer = None
        self.ch2ViewButton.stateChanged.connect(self.set_ch2_active)
        self.ch2_active = False
        self._ch2_buffer = None

        # connect number of channels input, set default
        self.numSlicesInput.editingFinished.connect(self.set_num_slices)
        self.num_slices = 1
        self.numSlicesInput.setText('1')

        # make channel views into pyqtgraph images
        self.ch1_plot = self.ch1Viewer.getPlotItem()
        self.ch1_curr_image = pg.ImageItem()
        self.ch1_plot.addItem(self.plugin_curr_image)
        self.ch1_plot.showAxis('left', False)
        self.ch1_plot.showAxis('bottom', False)
        self.ch1_plot.setAspectLocked(lock=True, ratio=1)
        self.ch1_plot.invertY(True)
        self.set_ch1_image()


        self.ch2_plot = self.ch2Viewer.getPlotItem()
        self.ch2_curr_image = pg.ImageItem()
        self.ch2_plot.addItem(self.plugin_curr_image)
        self.ch2_plot.showAxis('left', False)
        self.ch2_plot.showAxis('bottom', False)
        self.ch2_plot.setAspectLocked(lock=True, ratio=1)
        self.ch2_plot.invertY(True)
        self.set_ch2_image()

        # initialize rois
        self.rois = None
        self.wedge_resolution = 16
        # connect roi control buttons
        self.loadEBROIsButton.clicked.connect(self.load_EB_rois)
        self.wedge_masks = None
        self.wedge_centers = None
        self.loadPBROIsButton.clicked.connect(self.load_PB_rois)
        self.clearROIsButton.clicked.connect(self.clear_rois)
        self.roiLockCheckBox.stateChanged(self.lock_rois)
        self._rois_locked = False


        #radio button .toggled.connect()
        # connect df/f(r) buttons
        self.ch1FuncChanButton.toggled.connect(self.set_func_ch)
        self.ch2FuncChanButton.toggled.connect(self.set_func_ch)
        self.functionalChReset.clicked.connect(self.reset_func_ch)

        self.ch1StaticChanButton.toggled.connect(self.set_static_ch1)
        self.ch2StaticChanButton.toggled.connect(self.set_static_ch2)

        self.plugin_timer = QtCore.QTimer()
        self.plugin_timer.timeout.connect(self.set_channel_images)
        #TODO: set timeout based on number of lines in frame
        self.plugin_timer.start()

        #TODO: add serial port to listen to commands from Teensy




        #TODO: df/f, sending data over serial port



    def open_prairie_link(self):

        self.pl = win32com.client.Dispatch("PrairieLink.Application")
        self.pl.Connect()

        self._pl_active.set()

        self._set_dummy_img()

    def _set_dummy_img(self):
        if self._pl_active.is_set():
            self._dummy_img = np.ones((self.pl.LinesPerFrame(), self.pl.PixelsPerLine(), 3))

    def set_ch1_active(self):
        '''

        :return:
        '''
        if self.ch1ViewButton.isChecked():
            self.ch1_active = True
            self._set_dummy_img()
            self._ch1_buffer = np.zeros((*self._dummy_img.shape, self.num_slices))
        else:
            self.ch1_active = False


    def set_ch2_active(self):
        '''

        :return:
        '''
        if self.ch2ViewButton.isChecked():
            self.ch2_active = True
            self._set_dummy_img()
            self._ch2_buffer = np.zeros((*self._dummy_img.shape, self.num_slices))
        else:
            self.ch2_active = False


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

    def set_channel_images(self):


        if self.ch1_active:
            # update buffer
            self._ch1_buffer[:,:,:-1] = self._ch1_buffer[:,:,1:]
            self._ch1_buffer[:,:,-1] = self.get_channel_image(1)
            #set image
            #TODO: add option in designer to do max or mean projection
            self.ch1_curr_image.setImage(np.amax(self._ch1_buffer,axis=-1))
            self.ch1_curr_image.autoRange()

        if self.ch2_active:
            # update buffer
            self._ch2_buffer[:,:,:-1] = self._ch2_buffer[:,:,1:]
            self._ch2_buffer[:,:,-1] = self.get_channel_image(2)
            # set image
            self.ch2_curr_image.setImage(np.amax(self._ch2_buffer,axis=-1))
            self.ch2_curr_image.autoRange()

    def get_channel_image(self, channel):
        '''

        :return:
        '''
        return np.array(self.pl.GetImage_2(channel, self.pl.PixelsPerLine(), self.pl.LinesPerFrame())).T

    def load_EB_rois(self):

        self.rois = {'type': 'EB',
                  'outer_ellipse': pg.EllipseROI([50, 50], [50, 50], pen=(3, 9), scaleSnap=True, translateSnap=True),
                  'inner_ellipse': pg.EllipseROI([70, 70], [10, 10], pen = (3,9), scaleSnap=True, translateSnap=True)}

        self.ch1_plot.addItem(self.rois['outer_ellipse'])
        self.ch1_plot.addItem(self.rois['inner_ellipse'])

        self.ch2_plot.addItem(self.rois['outer_ellipse'])
        self.ch2_plot.addItem(self.rois['inner_ellipse'])

    def load_PB_rois(self):
        raise NotImplementedError


    def clear_rois(self):

        if self.rois['type'] == 'EB':
            self.ch1_plot.removeItem(self.rois['outer_ellipse'])
            self.ch1_plot.removeItem(self.rois['inner_ellipse'])

            self.ch2_plot.removeItem(self.rois['outer_ellipse'])
            self.ch2_plot.removeItem(self.roise['inner_ellipse'])

        elif self.rois['type'] == 'PB':
            raise NotImplementedError

    def lock_rois(self):

        if self.roiLockCheckBox.isChecked():

            for key, val in self.rois.items():
                if key != 'type':
                    val.translatable = False

            self._rois_locked = True
            self._finalize_masks()

            #TODO: inactivate other buttons
        else:
            self._rois_locked = False
            # self._remove_masks()
            self._stop_streaming()

            #TODO: reactivate other buttons


    def _finalize_masks(self):
        # make masks
        if self.rois is None:
            pass
            #raise warning

        else:
            self._set_dummy_img() # make sure dummy image is the right shape
            if self.rois['type'] == 'EB':
                # active pixel mask
                donut_mask = self._make_donut_mask()

                # get circular phase of each pixel, assuming origin in center of larger roi
                phase_mask = self.phase_calc(self._dummy_img.shape[0],self._dummy_img.shape[1])
                phase_mask *= donut_mask

                # bin wedges
                self.wedge_masks = np.zeros((*donut_mask.shape, self.wedge_resolution))
                bin_edges = np.linspace(1E-5, 2*np.pi, num= self.wedge_resolution+1)

                self.wedge_centers = []
                for itr, (ledge, redge) in enumerate(zip(bin_edges[:-1].tolist(),bin_edges[1:])):
                    self.wedge_masks[:,:,itr] = (donut_mask>0) * (phase_mask>= ledge) * (phase_mask<redge)
                    self.wedge_centers.append((ledge+redge)/2.)

                self.wedge_centers = np.array(self.wedge_centers)


    def _make_donut_mask(self):

        outer_mask = 1.*(self.rois['outer ellipse'].getArrayRegion(self._dummy_img, self.ch1_curr_image)>0)
        _inner_mask = 1. * (self.rois['inner ellipse'].getArrayRegion(self._dummy_img,self.ch1_curr_image)>0)

        inner_mask_rel_pos = (int(self.rois['inner ellipse'].pos()[1]-self.rois['outer ellipse'].pose()[1]),
                              int(self.rois['inner ellipse'].pos()[0]-self.rois['outer ellipse'].pose()[0]))

        inner_mask = np.zeros(outer_mask.shape)
        inner_mask[inner_mask_rel_pos[0]:inner_mask_rel_pos[0] + _inner_mask.shape[0],
                   inner_mask_rel_pos[1]:inner_mask_rel_pos[1] + _inner_mask.shape[1]] = _inner_mask

        donut_mask = 1.*((outer_mask-inner_mask)>1E-5)
        return donut_mask

    @staticmethod
    def phase_calc(nrows,ncols, center = None):
        phase_mat = np.zeros([nrows, ncols])

        if center is None:
            center = (int(nrows / 2), int(ncols / 2))

        for row, col in itertools.product(range(nrows), range(ncols)):
            phase_mat[row, col] = np.arctan2(col - center[1], row - center[0])+np.pi +1E-5

        return phase_mat

    def _start_streaming(self):

        if self.rois['type'] == 'EB':
            # start buffer for baseline

            # start fluorescence buffer
            pass



        elif self.rois['type'] == 'PB':
            raise NotImplementedError










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

