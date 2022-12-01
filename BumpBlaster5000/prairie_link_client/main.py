import itertools
import queue
import threading
import sys
import time
import warnings
import ctypes
import os

import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg
import serial


import plugin_viewer
import BumpBlaster5000
from BumpBlaster5000.utils import pol2cart, cart2pol, threaded
from BumpBlaster5000 import params


if params.hostname:
    import win32com.client
    
class PLUI(QtWidgets.QMainWindow, plugin_viewer.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PLUI, self).__init__(parent)
        self.setupUi(self)
        self._params = params.PL_PC_PARAMS

        pg.setConfigOptions(imageAxisOrder='row-major', antialias=True)

        # connect number of slices input, set default to 1
        self.numSlicesInput.editingFinished.connect(self.set_num_slices)
        self.num_slices = 1
        self._zstack_frames = 1
        self.numSlicesInput.setText('1')

        # connect to prairie link
        self.pl = None
        self._pl_active = threading.Event()
        self.open_prairie_link()
        self._get_frame_period(reset_timer=False)
        self._zstack_period = self._frame_period * self._zstack_frames
        self._dummy_img = None

        # wait for prairie link to connect
        # TODO: set max timeout and throw an error if prairie link doesn't connect
        print("Waiting for PriaireLink to connect")
        while not self._pl_active.is_set():
            time.sleep(.01)
        print("PrairieLink connected")
        # connect to teensy serial port to read PL commands
        self.teensy_srl_handle = self.continuous_read_teensy_pl_commands()
        self._pid = os.getpid() # prairie link process id for reading raw data stream

        # connect channel view buttons
        self.ch1ViewButton.stateChanged.connect(self.set_ch1_active)
        self.ch1_active = False
        self._ch1_data = None
        self.ch2ViewButton.stateChanged.connect(self.set_ch2_active)
        self.ch2_active = False
        # channel viewer data placeholders
        self._zbuffers = {1: None,
                          2: None}
        self._zproj = {1: None,
                       2: None}

        # make channel views into pyqtgraph images
        self.ch1_plot = self.ch1Viewer.getPlotItem()
        self.ch1_plot.setMouseEnabled(x=False, y=False)
        self.ch1_curr_image = pg.ImageItem()
        self.ch1_plot.addItem(self.ch1_curr_image)
        self.ch1_plot.showAxis('left', False)
        self.ch1_plot.showAxis('bottom', False)
        # self.ch1_plot.setAspectLocked(lock=True, ratio=1)
        self.ch1_plot.invertY(True)
        # self.set_ch1_image()

        self.ch2_plot = self.ch2Viewer.getPlotItem()
        self.ch2_plot.setMouseEnabled(x=False, y=False)
        self.ch2_curr_image = pg.ImageItem()
        self.ch2_plot.addItem(self.ch2_curr_image)
        self.ch2_plot.showAxis('left', False)
        self.ch2_plot.showAxis('bottom', False)
        # self.ch2_plot.setAspectLocked(lock=True, ratio=1)
        self.ch2_plot.invertY(True)
        # self.set_ch2_image()

        # initialize rois
        self.rois = None
        self.wedge_resolution = self._params['wedge_resolution']  # number of rois for EB
        # connect roi control buttons
        self.loadEBROIsButton.clicked.connect(self.load_EB_rois)
        self.wedge_masks = None
        self.wedge_centers = None
        self.loadPBROIsButton.clicked.connect(self.load_PB_rois)
        self.clearROIsButton.clicked.connect(self.clear_rois)
        self.roiLockCheckBox.stateChanged.connect(self.lock_rois)
        self._rois_locked = False


        # connect df/f(r) buttons
        self._func_ch = None
        self._func_data_buffer = None
        self.ch1FuncChanButton.toggled.connect(self.set_func_ch)

        self.ch2FuncChanButton.toggled.connect(self.set_func_ch)
        self.ch2FuncChanButton.setChecked(True)

        self._baseline_ch = None
        self._baseline_data_buffer = None
        self.ch1StaticChanButton.toggled.connect(self.set_baseline_ch)

        self.ch2StaticChanButton.toggled.connect(self.set_baseline_ch)
        self.ch2StaticChanButton.setChecked(True)


        self.streamDataCheckBox.stateChanged.connect(self.set_streaming)
        self.streamDataCheckBox.setCheckable(False)
        self._stream_bump = False
        self._bump_signal = None
        self._bump_mag = None
        self._bump_phase = None
        self._bump_queue = queue.Queue()

        # start serial port to send bump data to VR computer
        # self.bump_srl_handle = self.write_bump_data_serial()

        # bump viewer
        self.bump_viewer = self.bumpViewer.getPlotItem()
        self.bump_heatmap = pg.ImageItem()
        self.bump_viewer.addItem(self.bump_heatmap)
        self.bump_plot = pg.PlotDataItem(pen=pg.mkPen(color='r', width=3))
        self.bump_viewer.addItem(self.bump_plot)
        # self.bump_.showAxis('left', False)
        # self.bump_plot.showAxis('bottom', False)
        # self.bump_plot.setAspectLocked(lock=True, ratio=1)
        # self.bump_plot.invertY(True)

        self.frame_timer = QtCore.QTimer()
        self.frame_timer.timeout.connect(self.frame_update)
        self.frame_timer.start() #self._frame_period)

    @threaded
    def continuous_read_teensy_pl_commands(self):
        '''
        open serial port from teensy and send commands straight to prairie link,
        undesired behavior if strings are not valid prairie link commands
        :param teensy_com: com port for UART serial port from Teensy
        :param baudrate:
        :return:
        '''

        with serial.Serial(self._params['teensy_com'], baudrate=self._params['baudrate']) as srl:
            while self._pl_active.is_set():
                # read serial and send as commands to Prairie Link
                # note this will block forever if commands aren't sent
                # ToDo: set a timeout, if string is not empty, send to prairie link
                self.pl.SendScriptCommands(srl.readline().decode('UTF-8').rstrip())

    @threaded
    def read_heading_data_serial(self):
        '''
        reading heading data from VR computer over dedicated serial port
        :param vr_com: com port to VR computer
        :param baudrate: baudrate
        :return:
        '''

        # with serial.Serial(self._params['vr_com'], baudrate=self._params['baudrate']) as srl:
        #     while self._pl_active.is_set():  # while prairie link is active
        #         try:
        #             srl.write(self._bump_queue.get().encode('utf-8'))
        #         except queue.Queue.Empty:
        #             pass

    def open_prairie_link(self):
        '''
        opens prairie link and sets a dummy image to match current frame size
        :return:
        '''

        # make connection
        self.pl = win32com.client.Dispatch("PrairieLink64.Application")
        self.pl.Connect('127.0.0.1')

        # set thread safe event
        self._pl_active.set()

        # set dummy image
        self._set_dummy_img()

    def _set_dummy_img(self):
        '''
        make a dummy image of ones to help with mask creation and array allocation
        :return:
        '''
        if self._pl_active.is_set():  # if connected to prairie link
            self._dummy_img = np.ones((self.pl.LinesPerFrame(), self.pl.PixelsPerLine()))

    def _get_frame_period(self, reset_timer=True):
        '''
        Read frame period from prairie link and convert from string.

        :param reset_timer: If true, reset QTimer to new frame period. This is usually the desired behavior but flag
        exists to avoid errors during initialization
        :return:
        '''
        # TODO: check this output, change to ms if necessary and round to int
        self._frame_period = float(self.pl.GetState("framePeriod"))
        if reset_timer:
            self.frame_timer.stop()
            self.frame_timer.start() #self._frame_period)

    def set_ch1_active(self):
        '''
        If ch1 viewer is set to active, update flags, reset prairie link parameters to match current scan settings
        and allocate a buffer for the z stack
        :return:
        '''
        if self.ch1ViewButton.isChecked():
            self.ch1_active = True
            self._reinit_zbuffer(1)

        else:
            self.ch1_active = False
            self._zbuffers[1] = None

    def set_ch2_active(self):
        '''
        If ch2 viewer is set to active, update flags, reset prairie link parameters to match current scan settings
        and allocate a buffer for the z stack
        :return:
        '''
        if self.ch2ViewButton.isChecked():
            self.ch2_active = True
            self._reinit_zbuffer(2)
        else:
            self.ch2_active = False
            self._zbuffers[2] = None

    def _reinit_zbuffer(self,ch):
        '''
        Initialize z buffers for plotting
        :param ch: channel to initialize
        :return:
        '''
        self._set_dummy_img()
        self._get_frame_period()
        self._zstack_period = self._frame_period * self._zstack_frames
        self._zbuffers[ch]=np.zeros((*self._dummy_img.shape, self._zstack_frames))

    def set_num_slices(self):
        '''
        read text box for number of slices in z stack and update dependent parameters

        :return:
        '''

        num_slices_txt = self.numSlicesInput.text()
        try:
            self.num_slices = int(num_slices_txt)
            # deal with edge cases
            if self.num_slices == 1:
                self._zstack_frames = 1
            elif self.num_slices > 1:
                self._zstack_frames = self.num_slices + 1
            else:  # e.g. negative number or 0 accidentally input
                self.num_slices = 1
                self._zstack_frames = 1
                self.numSlicesInput.setText('1')
        except ValueError:  # accidentally entered something that's not a number
            self.numSlicesInput.setText('1')  # default to a single slince
            self.num_slices = 1
            self._zstack_frames = 1

        # update the timing information
        if self.ch1_active:
            self._reinit_zbuffer(1)

        if self.ch2_active:
            self._reinit_zbuffer(2)

        self._get_frame_period()
        self._zstack_period = self._frame_period * self._zstack_frames


    def frame_update(self):
        '''
        main function for updating data on each new imaging frame
        :return:
        '''

        try:
            # if ch1 data is needed
            if (self.ch1_active) or (self._stream_bump and (self._func_ch == 1 or self._baseline_ch == 1)):
                self._zbuffers[1][:, :, :-1] = self._zbuffers[1][:, :, 1:]
                self._zbuffers[1][:, :, -1] = self._get_channel_image(1)
                # ToDo: mean vs max proj toggle in designer
                self._zproj[1] = np.mean(self._zbuffers[1], axis=-1)

            # if ch2 data is needed
            if (self.ch2_active) or (self._stream_bump and (self._func_ch == 2 or self._baseline_ch == 2)):
                self._zbuffers[2][:, :, :-1] = self._zbuffers[2][:, :, 1:]
                self._zbuffers[2][:, :, -1] = self._get_channel_image(2)
                # ToDo: mean vs max proj toggle in designer
                self._zproj[2] = np.mean(self._zbuffers[2], axis=-1)

        except ValueError:
            # unexpected change in image shape
            print("Unexpected change in image shape. Resetting all buttons and clearing ROIs")
            self.streamDataCheckBox.setChecked(False)
            self.roiLockCheckBox.setChecked(False)
            self.clear_rois()
            self.ch1ViewButton.setChecked(False)
            self.ch2ViewButton.setChecked(False)
            self._set_dummy_img()
            self._get_frame_period()


        # set channel images
        self._set_channel_images()

        # stream data
        self._update_bump()

    def _set_channel_images(self):
        '''
        update data in pyqtgraph objects
        :return:
        '''
        if self.ch1_active:
            # set image
            self.ch1_curr_image.setImage(self._zproj[1])
            self.ch1_plot.autoRange()

        if self.ch2_active:
            # set image
            self.ch2_curr_image.setImage(self._zproj[2])
            self.ch2_plot.autoRange()

    def _get_channel_image(self, channel):
        '''
        Read image data over prairie link
        This will be the data that is currently displayed on the viewer from prairie link. It is not the data that is
        being saved to disk. Any averaging or other parameters that affect the data display will also affect this data.
        :return:
        '''
        return np.array(self.pl.GetImage_2(channel, self.pl.LinesPerFrame(), self.pl.PixelsPerLine()))  # .T

    def load_EB_rois(self):
        '''
        Load two ellipse rois and add objects to each plot item. The smaller one is assumed to stay the smaller one.


        :return:
        '''
        self.rois = {'type': 'EB',
                     'inner ellipse ch2': pg.EllipseROI([70, 70], [10, 10], pen=(3, 9),
                                                        rotatable=False, scaleSnap=True, translateSnap=True),
                     'outer ellipse ch1': pg.EllipseROI([50, 50], [50, 50], pen=(3, 9),
                                                        rotatable=False, scaleSnap=True, translateSnap=True),
                     'inner ellipse ch1': pg.EllipseROI([70, 70], [10, 10], pen=(3, 9),
                                                        rotatable=False, scaleSnap=True, translateSnap=True),
                     'outer ellipse ch2': pg.EllipseROI([50, 50], [50, 50], pen=(3, 9),
                                                        rotatable=False, scaleSnap=True, translateSnap=True),

                     }

        # make sure roi locations and sizes are matched across channels
        for k, v in self.rois.items():
            if k != 'type':
                print(k,v)
                v.sigRegionChangeFinished.connect(lambda v: self._EB_match_roi_pos(list(self.rois.keys())[list(self.rois.values()).index(v)]))


        self.ch1_plot.addItem(self.rois['outer ellipse ch1'])
        self.ch1_plot.addItem(self.rois['inner ellipse ch1'])

        self.ch2_plot.addItem(self.rois['outer ellipse ch2'])
        self.ch2_plot.addItem(self.rois['inner ellipse ch2'])

        self.loadEBROIsButton.setEnabled(False)
        self.loadPBROIsButton.setEnabled(False)

    def _EB_match_roi_pos(self, name):
        '''
        Ensure ROI locations mirror each other across channel views
        :return:
        '''

        if name == 'outer ellipse ch1':
            mirror_name = 'outer ellipse ch2'
        elif name == 'outer ellipse ch2':
            mirror_name = 'outer ellipse ch1'
        elif name == 'inner ellipse ch1':
            mirror_name = 'inner ellipse ch2'
        elif name == 'inner ellipse ch2':
            mirror_name = 'inner ellipse ch1'
        else:
            raise Exception("wrong roi name")

        print(name,mirror_name)
        roi = self.rois[name]
        mirror_roi = self.rois[mirror_name]

        if roi.pos() != mirror_roi.pos():
            mirror_roi.setPos(roi.pos(), finish=False)

        if roi.size() != mirror_roi.size():
            mirror_roi.setSize(roi.size(), finish=False)

        # mirror_roi.stateChanged()

    def load_PB_rois(self):
        raise NotImplementedError

    def clear_rois(self):
        '''
        remove rois
        :return:
        '''
        if self.rois is not None:
            if self.rois['type'] == 'EB':
                self.ch1_plot.removeItem(self.rois['outer ellipse ch1'])
                self.ch1_plot.removeItem(self.rois['inner ellipse ch1'])

                self.ch2_plot.removeItem(self.rois['outer ellipse ch2'])
                self.ch2_plot.removeItem(self.rois['inner ellipse ch2'])


            elif self.rois['type'] == 'PB':
                raise NotImplementedError

            self.rois = None
            self.loadEBROIsButton.setEnabled(True)
            self.loadPBROIsButton.setEnabled(True)
        else:
            pass

    def lock_rois(self):
        '''
        lock the roi position and size and initialize masks for streaming data
        :return:
        '''

        if self.rois is not None:
            if self.roiLockCheckBox.isChecked():
                for key, val in self.rois.items():

                    if key != 'type':
                        # get parameters of roi
                        pos, size = val.pos(), val.size()

                        # remove all rois from plot
                        if key[-3:] == 'ch1':
                            self.ch1_plot.removeItem(self.rois[key])
                        elif key[-3:] == 'ch2':
                            self.ch2_plot.removeItem(self.rois[key])

                        # remake rois with same parameters but make them immutable
                        if self.rois['type'] == "EB":
                            self.rois[key] = pg.EllipseROI(pos, size, pen=(3, 9), movable=False, rotatable=False,
                                                           resizable=False, scaleSnap=True, translateSnap=True)
                            if key[-3:] == 'ch1':
                                self.ch1_plot.addItem(self.rois[key])
                            elif key[-3:] == 'ch2':
                                self.ch2_plot.addItem(self.rois[key])

                        elif self.rois['type'] == "PB":
                            raise NotImplementedError

                self._rois_locked = True
                self._finalize_masks()

                # Inactivate other buttons
                self.loadEBROIsButton.setEnabled(False)
                self.loadPBROIsButton.setEnabled(False)
                self.clearROIsButton.setEnabled(False)
                self.streamDataCheckBox.setCheckable(True)
            else:
                self._rois_locked = False

                for key, val in self.rois.items():
                    if key != 'type':
                        pos, size = val.pos(), val.size()
                        # remove all rois from plot
                        if key[-3:] == 'ch1':
                            self.ch1_plot.removeItem(self.rois[key])
                        elif key[-3:] == 'ch2':
                            self.ch2_plot.removeItem(self.rois[key])

                        if self.rois['type'] == "EB":
                            self.rois[key] = pg.EllipseROI(pos, size, pen=(3, 9), scaleSnap=True, translateSnap=True)
                            if key[-3:] == 'ch1':
                                self.ch1_plot.addItem(self.rois[key])
                            elif key[-3:] == 'ch2':
                                self.ch2_plot.addItem(self.rois[key])

                        elif self.rois['type'] == "PB":
                            raise NotImplementedError

                # reactivate other buttons
                self.loadEBROIsButton.setEnabled(True)
                self.loadPBROIsButton.setEnabled(True)
                self.clearROIsButton.setEnabled(True)
                self.streamDataCheckBox.setCheckable(False)

                self._stop_streaming()

    def _finalize_masks(self):
        '''
        make masks for fast calculation of bump phase and magnitude
        :return:
        '''

        self._set_dummy_img()  # make sure dummy image is the right shape
        if self.rois['type'] == 'EB':
            # active pixel mask
            bounding_slices, _donut_mask = self._make_donut_mask()

            # get circular phase of each pixel, assuming origin in center of larger roi
            _phase_mask = self.phase_calc(_donut_mask.shape[0], _donut_mask.shape[1])
            _phase_mask *= _donut_mask

            # embed masks in img shape extracted from PrairieView
            donut_mask = 0. * self._dummy_img
            donut_mask[bounding_slices[0], bounding_slices[1]] = _donut_mask

            phase_mask = 0 * self._dummy_img
            phase_mask[bounding_slices[0], bounding_slices[1]] = _phase_mask

            # bin wedges
            self.wedge_masks = np.zeros((*self._dummy_img.shape, self.wedge_resolution))
            bin_edges = np.linspace(1E-5, 2 * np.pi, num=self.wedge_resolution + 1)

            # make a mask for each wedge
            self.wedge_centers = []
            self.wedge_sizes = []
            for itr, (ledge, redge) in enumerate(zip(bin_edges[:-1].tolist(), bin_edges[1:])):
                tmp_mask = (donut_mask > 0) * (phase_mask >= ledge) * (phase_mask < redge)
                self.wedge_masks[:, :, itr] = tmp_mask
                # get average phase of mask
                self.wedge_centers.append((ledge + redge) / 2.)
                # number of active pixels in each mask
                self.wedge_sizes.append(tmp_mask.ravel().sum())

            self.wedge_centers = np.array(self.wedge_centers)
            self.wedge_sizes = np.array(self.wedge_sizes)
        elif self.rois['type'] == 'PB':
            raise NotImplementedError
        else:
            raise NotImplementedError

    def _make_donut_mask(self):
        '''
        make intermediate mask for EB rois
        :return:
        '''

        # indices of bounding box for outer ellipse roi


        if self.ch1_active:
            outer_key, inner_key = 'outer ellipse ch1', 'inner ellipse ch1'
            curr_image = self.ch1_curr_image

        elif self.ch2_active:
            outer_key, inner_key = 'outer ellipse ch2', 'inner ellipse ch2'
            curr_image = self.ch2_curr_image

        else:
            warnings.warn("At least one channel must be set active to finalize ROIS. Assuming Ch2")
            outer_key, inner_key = 'outer ellipse ch2', 'inner ellipse ch2'
            curr_image = self.ch2_curr_image

        bounding_slices = self.rois[outer_key].getArraySlice(self._dummy_img, curr_image)[0]
        # _dummy_img is an array of ones
        outer_mask = (0.*self._dummy_img)[bounding_slices[0], bounding_slices[1]]
        # fix the occasional 1 pixel error
        _outer_mask = 1. * (self.rois[outer_key].getArrayRegion(self._dummy_img, curr_image) > 0)
        outer_mask[:_outer_mask.shape[0], :_outer_mask.shape[1]] = _outer_mask

        _inner_mask = 1. * (self.rois[inner_key].getArrayRegion(self._dummy_img, curr_image) > 0)
        # get where inner mask starts relative to outer one
        inner_mask_rel_pos = (int(self.rois[inner_key].pos()[1] - self.rois[outer_key].pos()[1]),
                              int(self.rois[inner_key].pos()[0] - self.rois[outer_key].pos()[0]))

        inner_mask = np.zeros(outer_mask.shape)
        inner_mask[inner_mask_rel_pos[0]:inner_mask_rel_pos[0] + _inner_mask.shape[0],
        inner_mask_rel_pos[1]:inner_mask_rel_pos[1] + _inner_mask.shape[1]] = _inner_mask

        donut_mask = 1. * ((outer_mask - inner_mask) > 1E-5)
        return bounding_slices, donut_mask


    def phase_calc(self, nrows, ncols, center=None):
        '''
        Calculate phase of each pixel relative to center
        :param nrows: number of rows in output matrix
        :param ncols: number of columns in output matrix
        :param center: center used to calculate phase. If None, assume it's the center of the output array
        :return: phase_mat: [nrows, ncols] matrix of phase values (0,2*pi]
        '''
        phase_mat = np.zeros([nrows, ncols])

        if center is None:
            center = (int(nrows / 2), int(ncols / 2))

        for row, col in itertools.product(range(nrows), range(ncols)):
            # convert to phase (0-2*pi)
            phase_mat[row, col] = np.arctan2(col - center[1], row - center[0]) + np.pi + 1E-5

        return phase_mat

    def set_func_ch(self):
        '''
        set which signal is the calcium indicator, allocate buffers
        :return:
        '''

        if self.ch1FuncChanButton.isChecked():
            self._func_ch = 1
        elif self.ch2FuncChanButton.isChecked():
            self._func_ch = 2
        else:
            self._func_ch = None

        if self._func_ch is not None:
            if self._zbuffers[self._func_ch] is None:
                self._set_dummy_img() # update prairie link parameters
                self._zbuffers[self._func_ch] = np.zeros((*self._dummy_img.shape, self._zstack_frames))

    def set_baseline_ch(self):
        '''
        set which signal is used for baseline calculation, allocate buffers
        :return:
        '''

        if self.ch1StaticChanButton.isChecked():
            self._baseline_ch = 1
        elif self.ch2StaticChanButton.isChecked():
            self._baseline_ch = 2
        else:
            self._baseline_ch = None

        if self._baseline_ch is not None:
            if self._zbuffers[self._baseline_ch] is None:
                self._set_dummy_img() # update prairie link parameters
                self._zbuffers[self._baseline_ch] = np.zeros((*self._dummy_img.shape, self._zstack_frames))

    def set_streaming(self):
        '''
        update streaming bool and start or stop streaming
        :return:
        '''

        if self.streamDataCheckBox.isChecked():
            self._stream_bump = True
            self._start_streaming()
        else:
            self._stream_bump = False
            self._stop_streaming()

    def _start_streaming(self):
        '''
        begin streaming data
        :param baseline_time: buffer size in seconds
        :param func_time: buffer size for numerator in seconds (check)
        :param: bump_signal_time: size of bump data buffer in seconds
        :return:
        '''

        # get size of buffers in samples based on parameters
        num_func_samples = int(np.maximum(self._params['func_time'] / self._zstack_period, 1))
        if self._baseline_ch == self._func_ch:
            num_baseline_samples = int(self._params['baseline_time'] / self._zstack_period)
        else:
            num_baseline_samples = num_func_samples
        num_bump_samples = int(self._params['bump_signal_time'] / self._zstack_period)



        if self.rois['type'] == 'EB':
            # start buffers
            # num rois x baseline_time
            self._baseline_data_buffer = np.nan * np.zeros([self.wedge_resolution, num_baseline_samples])
            self._func_data_buffer = np.nan * np.zeros([self.wedge_resolution, num_func_samples])
            self._bump_signal = np.zeros((self.wedge_resolution, num_bump_samples))
            self._bump_phase = np.zeros((num_bump_samples,))
            self._bump_mag = np.zeros((num_bump_samples,))

        elif self.rois['type'] == 'PB':
            raise NotImplementedError

    def _update_bump(self):
        '''
        update bump calculation for each frame
        :return:
        '''

        if self._stream_bump:
            self._apply_roi_masks()
            self._calc_bump_phase()
            self._plot_bump()
        else:
            return

    def _apply_roi_masks(self):
        '''
        apply roi masks and update data buffers
        :return:
        '''

        if self.rois['type'] == "EB":
            self._update_fluor_buffers(self._apply_EB_masks())
        elif self.rois['type'] == 'PB':
            raise NotImplementedError
        else:
            raise NotImplementedError


    def _apply_EB_masks(self):
        '''
        extract data from each wedge mask for EB rois
        :return: mask_data: [dict] with key, value pair for each PMT. Value is a numpy array with mean for each mask
        '''

        # allocate
        mask_data = {1: None, 2: None}
        # for each channel
        for ch, zproj in self._zproj.items():
            if zproj is not None:
                # wedge_masks: pixels x pixels x num of masks
                # zproj: pixels x pixels
                num = np.squeeze(
                    (zproj[:, :, np.newaxis] * self.wedge_masks).sum(axis=0, keepdims=True).sum(axis=1, keepdims=True))
                mask_data[ch] = num / self.wedge_sizes
        return mask_data

    def _update_fluor_buffers(self, mask_data):
        '''
        update data buffers (first in last out)
        :param mask_data:
        :return:
        '''

        self._baseline_data_buffer[:, :-1] = self._baseline_data_buffer[:, 1:]
        self._baseline_data_buffer[:, -1] = mask_data[self._baseline_ch]

        self._func_data_buffer[:, :-1] = self._func_data_buffer[:, 1:]
        self._func_data_buffer[:, -1] = mask_data[self._func_ch]

    @staticmethod
    def _signal(func_data, baseline_data):
        '''
        delta F/F
        :param func_data:  [nrois x buffer size]
        :param baseline_data:  [nrois x buffer size]
        :return: df/f
        '''

        return np.nanmean(func_data, axis=1) / np.nanpercentile(baseline_data + 1E-5, 5, axis=1)

    def _calc_bump_phase(self):
        '''
        calculate phase and magnitude of bump
        :return:
        '''
        signal = self._signal(self._func_data_buffer, self._baseline_data_buffer)

        if self.rois['type'] == 'EB':
            x, y = pol2cart(signal, self.wedge_centers) # polar to cartesian
            mag, phase = cart2pol(x.mean(), y.mean()) # mean and then convert back to polar
            phase = (phase + 2 * np.pi) % (2. * np.pi) # shift phase to agree with plot
        elif self.rois['type'] == 'PB':
            mag, phase = None, None
            raise NotImplementedError
        else:
            mag, phase = None, None

        # update bump buffers
        self._update_bump_buffers(signal, mag, phase)

        # send magnitude and phase to com port queue to be sent to VR computer
        self._bump_queue.put(f"{mag}, {phase}\n")

    def _update_bump_buffers(self, signal, mag, phase):
        '''
        update plotting buffers for bump plotting
        :param signal: df/f
        :param mag: bump magnitude
        :param phase:bump phase
        :return:
        '''

        self._bump_signal[:, :-1] = self._bump_signal[:, 1:]
        self._bump_signal[:, -1] = signal
        self._bump_mag[:-1] = self._bump_mag[1:]
        self._bump_mag[-1] = mag
        self._bump_phase[:-1] = self._bump_phase[1:]
        self._bump_phase[-1] = phase


    def _plot_bump(self):
        '''
        update pyqtgraph objects for current data
        :return:
        '''

        self.bump_heatmap.setImage(self._bump_signal)
        self.bump_plot.setData(np.arange(0, self._bump_signal.shape[1]),
                               self._bump_phase / 2. / np.pi * self.wedge_resolution)

    def _stop_streaming(self):
        '''
        reset data buffers
        :return:
        '''
        self._func_data_buffer = None
        self._baseline_data_buffer = None

        self._bump_signal = None
        self._bump_mag = None
        self._bump_phase = None

    def closeEvent(self, event: QtGui.QCloseEvent):
        '''
        override QWidget method to kill other threads and disconnect from prairie link on closure
        :param event: required input from QtWidget
        :return:
        '''
        # close serial ports
        # ToDo: check that serial ports are actually clearing

        # disconnect from prairie link
        self.pl.Disconnect()
        print(self.pl.Connected())
        self._pl_active.clear()
        print(self._pl_active.is_set())

        # join threads
        self.teensy_srl_handle.join()
        self.bump_srl_handle.join()

        # close
        event.accept()


def main():
    app = QApplication(sys.argv)
    widget = PLUI()
    widget.show()
    r = app.exec_()
    sys.exit(r)


if __name__ == '__main__':
    main()
