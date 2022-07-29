import itertools
import queue
import threading
import sys
import time

import numpy as np
import win32com.client
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication
import pyqtgraph as pg
import serial
from numba import njit

import plugin_viewer
from BumpBlaster5000.utils import pol2cart, cart2pol, threaded


class PLUI(QtWidgets.QMainWindow, plugin_viewer.Ui_MainWindow):
    def __init__(self, parent=None, wedge_resolution=16):
        super(PLUI, self).__init__(parent)
        self.setupUi(self)

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
        #TODO: set max timeout and throw an error if prairie link doesn't connect
        print("Waiting for PriaireLink to connect")
        while not self._pl_active.is_set():
            time.sleep(.01)
        print("PrairieLink connected")
        # connect to teensy serial port to read PL commands
        self.teensy_srl_handle = self.continuous_read_teensy_pl_commands()



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
        # self.ch1_plot.invertY(True)
        # self.set_ch1_image()

        self.ch2_plot = self.ch2Viewer.getPlotItem()
        self.ch2_plot.setMouseEnabled(x=False, y=False)
        self.ch2_curr_image = pg.ImageItem()
        self.ch2_plot.addItem(self.ch2_curr_image)
        self.ch2_plot.showAxis('left', False)
        self.ch2_plot.showAxis('bottom', False)
        # self.ch2_plot.setAspectLocked(lock=True, ratio=1)
        # self.ch2_plot.invertY(True)
        # self.set_ch2_image()

        # initialize rois
        self.rois = None
        self.wedge_resolution = wedge_resolution # number of rois for EB
        # connect roi control buttons
        self.loadEBROIsButton.clicked.connect(self.load_EB_rois)
        self.wedge_masks = None
        self.wedge_centers = None
        self.loadPBROIsButton.clicked.connect(self.load_PB_rois)
        self.clearROIsButton.clicked.connect(self.clear_rois)
        self.roiLockCheckBox.stateChanged.connect(self.lock_rois)
        self._rois_locked = False

        # connect df/f(r) buttons
        self.ch1FuncChanButton.toggled.connect(self.set_func_ch)
        self.ch2FuncChanButton.toggled.connect(self.set_func_ch)
        self._func_ch = None
        self._func_data_buffer = None

        self.ch1StaticChanButton.toggled.connect(self.set_baseline_ch)
        self.ch2StaticChanButton.toggled.connect(self.set_baseline_ch)
        self._baseline_ch = None
        self._baseline_data_buffer = None

        self.streamDataCheckBox.stateChanged.connect(self.set_streaming)
        self._stream_bump = False
        self._bump_signal = None
        self._bump_mag = None
        self._bump_phase = None
        self._bump_queue = queue.Queue()

        # start serial port to send bump data to VR computer
        self.bump_srl_handle = self.write_bump_data_serial()

        # bump viewer
        self.bump_viewer = self.bumpViewer.getPlotItem()
        self.bump_heatmap = pg.ImageItem()
        self.bump_viewer.addItem(self.bump_heatmap)
        self.bump_plot = pg.PlotDataItem(pen=pg.mkPen(color='r',width=3))
        self.bump_viewer.addItem(self.bump_plot)
        # self.bump_.showAxis('left', False)
        # self.bump_plot.showAxis('bottom', False)
        # self.bump_plot.setAspectLocked(lock=True, ratio=1)
        # self.bump_plot.invertY(True)

        self.frame_timer = QtCore.QTimer()
        self.frame_timer.timeout.connect(self.frame_update)
        self.frame_timer.start(self._frame_period)

    @threaded
    def continuous_read_teensy_pl_commands(self, teensy_com='COM12', baudrate=115200):
        '''
        open serial port from teensy and send commands straight to prairie link,
        undesired behavior if strings are not valid prairie link commands
        :param teensy_com: com port for UART serial port from Teensy
        :param baudrate:
        :return:
        '''

        with serial.Serial(teensy_com, baudrate=baudrate) as srl:
            while self._pl_active.is_set():
                # read serial and send as commands to Prairie Link
                # note this will block forever if commands aren't sent
                # ToDo: set a timeout, if string is not empty, send to prairie link
                self.pl.SendScriptCommands(srl.readline().decode('UTF-8').rstrip())

    @threaded
    def write_bump_data_serial(self, vr_com='COM11', baudrate=115200):
        '''
        send bump phase and magnitude to VR computer over dedicated serial port
        :param vr_com: com port to VR computer
        :param baudrate: baudrate
        :return:
        '''
        #ToDo: make com port names and baudrates a parameter saved in a separate file


        with serial.Serial(vr_com, baudrate=baudrate) as srl:
            while self._pl_active.is_set(): # while prairie link is active
                try:
                    bump_data = self._bump_queue.get()
                    srl.write(bump_data.encode('utf-8'))
                except queue.Queue.Empty:
                    pass



    def open_prairie_link(self):
        '''
        opens prairie link and sets a dummy image to match current frame size
        :return:
        '''

        # make connection
        self.pl = win32com.client.Dispatch("PrairieLink.Application")
        self.pl.Connect()

        # set thread safe event
        self._pl_active.set()

        # set dummy image
        self._set_dummy_img()

    def _set_dummy_img(self):
        '''
        make a dummy image of ones to help with mask creation and array allocation
        :return:
        '''
        if self._pl_active.is_set(): # if connected to prairie link
            self._dummy_img = np.ones((self.pl.LinesPerFrame(), self.pl.PixelsPerLine()))

    def _get_frame_period(self, reset_timer=True):
        '''
        Read frame period from prairie link and convert from string.

        :param reset_timer: If true, reset QTimer to new frame period. This is usually the desired behavior but flag
        exists to avoid errors during initialization
        :return:
        '''
        # TODO: check this output, change to ms if necessary and round to int
        self._frame_period = np.float(self.pl.GetState("framePeriod"))
        if reset_timer:
            self.frame_timer.stop()
            self.frame_timer.start(self._frame_period)

    def set_ch1_active(self):
        '''
        If ch1 viewer is set to active, update flags, reset prairie link parameters to match current scan settings
        and allocate a buffer for the z stack
        :return:
        '''
        if self.ch1ViewButton.isChecked():
            self.ch1_active = True
            # update scan settings
            self._set_dummy_img()
            self._get_frame_period()
            # allocate zstack buffer
            self._zbuffers[1] = np.zeros((*self._dummy_img.shape, self._zstack_frames))
        else:
            self.ch1_active = False

    def set_ch2_active(self):
        '''

        :return:
        '''
        if self.ch2ViewButton.isChecked():
            self.ch2_active = True
            self._set_dummy_img()
            self._get_frame_period()
            self._zbuffers[2] = np.zeros((*self._dummy_img.shape, self._zstack_frames))
        else:
            self.ch2_active = False

    def set_num_slices(self):
        '''

        :return:
        '''
        num_slices_txt = self.numSlicesInput.text()
        try:
            self.num_slices = int(num_slices_txt)
            if self.num_slices == 1:
                self._zstack_frames = 1

            elif self.num_slices > 1:
                self._zstack_frames = self.num_slices + 1
            else:
                self.num_slices = 1
                self._zstack_frames = 1
                self.numSlicesInput.setText('1')


        except ValueError:
            self.numSlicesInput.setText('1')
            self.num_slices = 1
            self._zstack_frames = 1

        self._get_frame_period()
        self._zstack_period = self._frame_period * self._zstack_frames

    def frame_update(self):
        if self.ch1_active or self._func_ch == 1 or self._baseline_ch == 1:
            self._zbuffers[1][:, :, :-1] = self._zbuffers[1][:, :, 1:]
            self._zbuffers[1][:, :, -1] = self._get_channel_image(1)
            # ToDo: mean vs max proj toggle in designer
            self._zproj[1] = np.amax(self._zbuffers[1], axis=-1)

        if self.ch2_active or self._func_ch == 2 or self._baseline_ch == 2:
            self._zbuffers[2][:, :, :-1] = self._zbuffers[2][:, :, 1:]
            self._zbuffers[2][:, :, -1] = self._get_channel_image(2)
            # ToDo: mean vs max proj toggle in designer
            self._zproj[2] = np.amax(self._zbuffers[2], axis=-1)

        # set channel images
        self._set_channel_images()

        # stream data
        self._update_bump()

    def _set_channel_images(self):
        if self.ch1_active:
            # set image
            # TODO: add option in designer to do max or mean projection
            self.ch1_curr_image.setImage(self._zproj[1])
            self.ch1_plot.autoRange()

        if self.ch2_active:
            # set image
            self.ch2_curr_image.setImage(self._zproj[2])
            self.ch2_plot.autoRange()

    def _get_channel_image(self, channel):
        '''

        :return:
        '''
        return np.array(self.pl.GetImage_2(channel, self.pl.LinesPerFrame(), self.pl.PixelsPerLine()))#.T

    def load_EB_rois(self):

        self.rois = {'type': 'EB',
                     'outer ellipse': pg.EllipseROI([50, 50], [50, 50], pen=(3, 9),
                                                    rotatable=False, scaleSnap=True, translateSnap=True),
                     'inner ellipse': pg.EllipseROI([70, 70], [10, 10], pen=(3, 9),
                                                    rotatable=False, scaleSnap=True, translateSnap=True)}

        self.ch1_plot.addItem(self.rois['outer ellipse'])
        self.ch1_plot.addItem(self.rois['inner ellipse'])

        # self.ch2_plot.addItem(self.rois['outer ellipse'])
        # self.ch2_plot.addItem(self.rois['inner ellipse'])
        #ToDo: make roi copy for ch2_plot and a call back to make sure positions match

        self.loadEBROIsButton.setEnabled(False)
        self.loadPBROIsButton.setEnabled(False)


    def load_PB_rois(self):
        raise NotImplementedError

    def clear_rois(self):

        if self.rois['type'] == 'EB':
            self.ch1_plot.removeItem(self.rois['outer ellipse'])
            self.ch1_plot.removeItem(self.rois['inner ellipse'])

            self.ch2_plot.removeItem(self.rois['outer ellipse'])
            self.ch2_plot.removeItem(self.rois['inner ellipse'])

        elif self.rois['type'] == 'PB':
            raise NotImplementedError

        self.loadEBROIsButton.setEnabled(True)
        self.loadPBROIsButton.setEnabled(True)

    def lock_rois(self):

        if self.roiLockCheckBox.isChecked():

            for key, val in self.rois.items():
                if key != 'type':
                    pos, size = val.pos(), val.size()
                    self.ch1_plot.removeItem(self.rois[key])
                    # self.ch2_plot.removeItem(self.rois[key])

                    if self.rois['type'] == "EB":
                        self.rois[key] = pg.EllipseROI(pos, size, pen=(3, 9), movable=False, rotatable=False,
                                                       resizable=False, scaleSnap=True, translateSnap=True)
                        self.ch1_plot.addItem(self.rois[key])
                        # self.ch2_plot.addItem(self.rois[key])
                    elif self.rois['type'] == "PB":
                        raise NotImplementedError

            self._rois_locked = True
            self._finalize_masks()

            # Inactivate other buttons
            self.loadEBROIsButton.setEnabled(False)
            self.loadPBROIsButton.setEnabled(False)
            self.clearROIsButton.setEnabled(False)
        else:
            self._rois_locked = False

            for key, val in self.rois.items():
                if key != 'type':
                    pos, size = val.pos(), val.size()
                    self.ch1_plot.removeItem(self.rois[key])
                    # self.ch2_plot.removeItem(self.rois[key])

                    if self.rois['type'] == "EB":
                        self.rois[key] = pg.EllipseROI(pos, size, pen=(3, 9), scaleSnap=True, translateSnap=True)
                        self.ch1_plot.addItem(self.rois[key])
                        # self.ch2_plot.addItem(self.rois[key])
                    elif self.rois['type'] == "PB":
                        raise NotImplementedError

            # reactivate other buttons
            self.loadEBROIsButton.setEnabled(True)
            self.loadPBROIsButton.setEnabled(True)
            self.clearROIsButton.setEnabled(True)

            self._stop_streaming()

    def _finalize_masks(self):
        # make masks
        if self.rois is None:
            pass
            # raise warning

        else:
            self._set_dummy_img()  # make sure dummy image is the right shape
            if self.rois['type'] == 'EB':
                # active pixel mask
                bounding_slices, _donut_mask = self._make_donut_mask()
                print('bounding slices', bounding_slices)

                # get circular phase of each pixel, assuming origin in center of larger roi
                _phase_mask = self.phase_calc(_donut_mask.shape[0], _donut_mask.shape[1])
                _phase_mask *= _donut_mask

                # embed masks in img shape extracted from PrairieView
                donut_mask = 0.*self._dummy_img
                print('sliced array shape', donut_mask[bounding_slices[0], bounding_slices[1]].shape)
                #ToDo: make sure dimensions don't get screwed up when real image is present
                donut_mask[bounding_slices[0], bounding_slices[1]] = _donut_mask

                phase_mask = 0*self._dummy_img
                phase_mask[bounding_slices[0], bounding_slices[1]] = _phase_mask

                # bin wedges
                self.wedge_masks = np.zeros((*self._dummy_img.shape, self.wedge_resolution))
                bin_edges = np.linspace(1E-5, 2 * np.pi, num=self.wedge_resolution + 1)

                self.wedge_centers = []
                self.wedge_sizes = []
                for itr, (ledge, redge) in enumerate(zip(bin_edges[:-1].tolist(), bin_edges[1:])):
                    tmp_mask = (donut_mask > 0) * (phase_mask >= ledge) * (phase_mask < redge)
                    self.wedge_masks[:, :, itr] = tmp_mask
                    self.wedge_centers.append((ledge + redge) / 2.)
                    self.wedge_sizes.append(tmp_mask.ravel().sum())

                self.wedge_centers = np.array(self.wedge_centers)
                self.wedge_sizes = np.array(self.wedge_sizes)
                print('wedge size', self.wedge_sizes)
            elif self.rois['type'] == 'PB':
                raise NotImplementedError
            else:
                raise NotImplementedError

    def _make_donut_mask(self):

        bounding_slices = self.rois['outer ellipse'].getArraySlice(self._dummy_img, self.ch1_curr_image)[0]

        outer_mask = np.copy(self._dummy_img)[bounding_slices[0], bounding_slices[1]]
        # fix the occasional 1 pixel error
        _outer_mask = 1. * (self.rois['outer ellipse'].getArrayRegion(self._dummy_img, self.ch1_curr_image) > 0)
        outer_mask[:_outer_mask.shape[0], :_outer_mask.shape[1]] = _outer_mask

        _inner_mask = 1. * (self.rois['inner ellipse'].getArrayRegion(self._dummy_img, self.ch1_curr_image) > 0)

        inner_mask_rel_pos = (int(self.rois['inner ellipse'].pos()[1] - self.rois['outer ellipse'].pos()[1]),
                              int(self.rois['inner ellipse'].pos()[0] - self.rois['outer ellipse'].pos()[0]))

        inner_mask = np.zeros(outer_mask.shape)
        inner_mask[inner_mask_rel_pos[0]:inner_mask_rel_pos[0] + _inner_mask.shape[0],
        inner_mask_rel_pos[1]:inner_mask_rel_pos[1] + _inner_mask.shape[1]] = _inner_mask

        donut_mask = 1. * ((outer_mask - inner_mask) > 1E-5)
        print(donut_mask.shape)
        return bounding_slices, donut_mask

    @njit
    def phase_calc(self, nrows, ncols, center=None):
        phase_mat = np.zeros([nrows, ncols])

        if center is None:
            center = (int(nrows / 2), int(ncols / 2))

        for row, col in itertools.product(range(nrows), range(ncols)):
            phase_mat[row, col] = np.arctan2(col - center[1], row - center[0]) + np.pi + 1E-5

        return phase_mat

    def set_func_ch(self):

        if self.ch1FuncChanButton.isChecked():
            self._func_ch = 1
        elif self.ch2FuncChanButton.isChecked():
            self._func_ch = 2
        else:
            self._func_ch = None

        if self._func_ch is not None:
            if self._zbuffers[self._func_ch] is None:
                self._set_dummy_img()
                self._zbuffers[self._func_ch] = np.zeros((*self._dummy_img.shape, self._zstack_frames))

    def set_baseline_ch(self):

        if self.ch1StaticChanButton.isChecked():
            self._baseline_ch = 1
        elif self.ch2StaticChanButton.isChecked():
            self._baseline_ch = 2
        else:
            self._baseline_ch = None

        if self._baseline_ch is not None:
            if self._zbuffers[self._baseline_ch] is None:
                self._set_dummy_img()
                self._zbuffers[self._baseline_ch] = np.zeros((*self._dummy_img.shape, self._zstack_frames))

    def set_streaming(self):

        if self.streamDataCheckBox.isChecked():
            self._stream_bump = True
            self._start_streaming()
        else:
            self._stream_bump = False
            self._stop_streaming()

    def _start_streaming(self, baseline_time=60, func_time=.01, bump_signal_time=2):
        '''

        :param baseline_time: buffer size in seconds
        :return:
        '''

        num_func_samples = int(np.maximum(func_time / self._zstack_period, 1))
        if self._baseline_ch == self._func_ch:
            num_baseline_samples = int(baseline_time / self._zstack_period)
        else:
            num_baseline_samples = num_func_samples
        num_bump_samples = int(bump_signal_time / self._zstack_period)

        if self.rois['type'] == 'EB':
            # start buffer for baseline
            # num rois, baseline_time
            self._baseline_data_buffer = np.nan * np.zeros([self.wedge_resolution, num_baseline_samples])
            self._func_data_buffer = np.nan * np.zeros([self.wedge_resolution, num_func_samples])
            print('func buff size', self._func_data_buffer.shape)
            self._bump_signal = np.zeros((self.wedge_resolution, num_bump_samples))
            self._bump_phase = np.zeros((num_bump_samples,))
            self._bump_mag = np.zeros((num_bump_samples,))
        elif self.rois['type'] == 'PB':
            raise NotImplementedError

    def _update_bump(self):

        if self._stream_bump:
            self._apply_roi_masks()
            self._calc_bump_phase()
            self._plot_bump()
            self._send_bump_2_VR()
        else:
            return

    def _apply_roi_masks(self):

        if self.rois['type'] == "EB":
            self._update_bump_buffers(self._apply_EB_masks())
        elif self.rois['type'] == 'PB':
            raise NotImplementedError
        else:
            raise NotImplementedError

    @njit
    def _apply_EB_masks(self):
        mask_data = {1: None, 2: None}
        for ch, zproj in self._zproj.items():
            if zproj is not None:
                num = np.squeeze(
                    (zproj[:, :, np.newaxis] * self.wedge_masks).sum(axis=0, keepdims=True).sum(axis=1, keepdims=True))
                mask_data[ch] = num / self.wedge_sizes

        return mask_data

    def _update_bump_buffers(self, mask_data):

        self._baseline_data_buffer[:, :-1] = self._baseline_data_buffer[:, 1:]
        self._baseline_data_buffer[:, -1] = mask_data[self._baseline_ch]

        self._func_data_buffer[:, :-1] = self._func_data_buffer[:, 1:]
        self._func_data_buffer[:, -1] = mask_data[self._func_ch]

    @staticmethod
    @njit
    def _signal(func_data, baseline_data):
        return np.nanmean(func_data, axis=1) / np.nanpercentile(baseline_data + 1E-5, 5, axis=1)

    def _calc_bump_phase(self):

        signal = self._signal(self._func_data_buffer, self._baseline_data_buffer)

        if self.rois['type'] == 'EB':
            x, y = pol2cart(signal, self.wedge_centers)
            mag, phase = cart2pol(x.mean(), y.mean())
            phase = (phase+2*np.pi)%(2.*np.pi)
        elif self.rois['type'] == 'PB':
            mag, phase = None, None
            raise NotImplementedError
        else:
            mag, phase = None, None

        self._bump_signal[:, :-1] = self._bump_signal[:, 1:]
        self._bump_signal[:, -1] = signal
        self._bump_mag[:-1] = self._bump_mag[ 1:]
        self._bump_mag[-1] = mag
        self._bump_phase[:-1] = self._bump_phase[1:]
        self._bump_phase[-1] = phase

        self._bump_queue.put(f"{mag}, {phase}\n")

    def _plot_bump(self):
        self.bump_heatmap.setImage(self._bump_signal)
        self.bump_plot.setData(np.arange(0, self._bump_signal.shape[1]), self._bump_phase /2./np.pi*self.wedge_resolution)

    def _send_bump_2_VR(self):
        # ToDo: send info over serial port to teensy or directly to VR computer
        pass

    def _stop_streaming(self):

        self._func_data_buffer = None
        self._baseline_data_buffer = None

        self._bump_signal = None
        self._bump_mag = None
        self._bump_phase = None

    def closeEvent(self, event: QtGui.QCloseEvent):
        # close serial ports

        # disconnect from prairie link
        self.pl.Disconnect()
        self._pl_active.clear()

        # join threads
        self.teensy_srl_handle.join()
        self.bump_srl_handle.join()

        event.accept()




def main():
    app = QApplication(sys.argv)
    widget = PLUI()
    widget.show()
    r = app.exec_()
    sys.exit(r)



if __name__ == '__main__':
    main()


