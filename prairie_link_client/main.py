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

import plugin_viewer
# from .. import utils
from utils import pol2cart, cart2pol, threaded


class PLUI(QtWidgets.QMainWindow, plugin_viewer.Ui_MainWindow):
    def __init__(self, parent=None):
        super(PLUI, self).__init__(parent)
        self.setupUi(self)

        pg.setConfigOptions(imageAxisOrder='row-major')

        # connect number of channels input, set default
        self.numSlicesInput.editingFinished.connect(self.set_num_slices)
        self.num_slices = 1
        self._zstack_frames = 1
        self.numSlicesInput.setText('1')

        # connect to prairie link
        self.pl = None
        self._pl_active = threading.Event()
        self.open_prairie_link()
        self._frame_period = self._get_frame_period()
        self._zstack_period = self._frame_period * self._zstack_frames
        self._dummy_img = None

        while not self._pl_active.is_set():
            time.sleep(.01)
        self.teensy_srl_handle = self.continuous_read_teensy_pl_commands()



        # connect channel view buttons
        self.ch1ViewButton.stateChanged.connect(self.set_ch1_active)
        self.ch1_active = False
        self._ch1_data = None
        self.ch2ViewButton.stateChanged.connect(self.set_ch2_active)
        self.ch2_active = False
        self._zbuffers = {1: None,
                          2: None}
        self._zproj = {1: None,
                       2: None}

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

        # radio button .toggled.connect()
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
        self.bump_srl_handle = self.write_bump_data_serial()

        # bump viewer
        # TODO: set colormap and pen color for plots
        self.bump_viewer = self.bumpViewer.getPlotItem()
        self.bump_heatmap = pg.ImageItem()
        self.bump_viewer.addItem(self.plugin_heatmap)
        self.bump_plot = pg.PlotDataItem()
        self.bump_viewer.addItem(self.bump_plot)

        # self.bump_.showAxis('left', False)
        # self.bump_plot.showAxis('bottom', False)
        # self.bump_plot.setAspectLocked(lock=True, ratio=1)
        # self.bump_plot.invertY(True)

        self.frame_timer = QtCore.QTimer(self._frame_period)
        self.frame_timer.timeout.connect(self.frame_update())
        self.frame_timer.start()

        # TODO: add serial port to listen to commands from Teensy

        # TODO: df/f, sending data over serial port

    @threaded
    def continuous_read_teensy_pl_commands(self, teensy_com='COM12', baudrate=115200):

        with serial.Serial(teensy_com, baudrate=baudrate) as srl:
            while self._pl_active.is_set():
                # read serial and send as commands to Prairie Link
                self.pl.SendScriptCommands(srl.readline().decode('UTF-8').rstrip())

    @threaded
    def write_bump_data_serial(self, vr_com='COM11', baudrate=115200):
        #ToDo: make com port names and baudrates a parameter saved in a separate file

        # while prairie link is active
        with serial.Serial(vr_com, baudrate=baudrate) as srl:
            while self._pl_active.is_set():
                try:
                    bump_data = self._bump_queue.get()
                    srl.write(bump_data.encode('utf-8'))
                except queue.Queue.Empty:
                    pass



    def open_prairie_link(self):

        self.pl = win32com.client.Dispatch("PrairieLink.Application")
        self.pl.Connect()

        self._pl_active.set()

        self._set_dummy_img()

    def _set_dummy_img(self):
        if self._pl_active.is_set():
            self._dummy_img = np.ones((self.pl.LinesPerFrame(), self.pl.PixelsPerLine(), 3))

    def _get_frame_period(self):
        self._frame_period = np.float(self.pl.GetState("framePeriod"))

    def set_ch1_active(self):
        '''

        :return:
        '''
        if self.ch1ViewButton.isChecked():
            self.ch1_active = True
            self._set_dummy_img()
            self._get_frame_period()
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
            self.ch1_curr_image.autoRange()

        if self.ch2_active:
            # set image
            self.ch2_curr_image.setImage(self._zproj[2])
            self.ch2_curr_image.autoRange()

    def _get_channel_image(self, channel):
        '''

        :return:
        '''
        return np.array(self.pl.GetImage_2(channel, self.pl.PixelsPerLine(), self.pl.LinesPerFrame())).T

    def load_EB_rois(self):

        self.rois = {'type': 'EB',
                     'outer_ellipse': pg.EllipseROI([50, 50], [50, 50], pen=(3, 9), scaleSnap=True, translateSnap=True),
                     'inner_ellipse': pg.EllipseROI([70, 70], [10, 10], pen=(3, 9), scaleSnap=True, translateSnap=True)}

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
                    pos, size = val.pos(), val.size()
                    self.ch1_plot.removeItem(self.rois[key])
                    self.ch2_plot.removeItem(self.rois[key])

                    if self.rois['type'] == "EB":
                        self.rois[key] = pg.EllipseROI(pos, size, pen=(3, 9), movable=False, rotatable=False,
                                                       resizable=False)
                        self.ch1_plot.addItem(self.rois[key])
                        self.ch2_plot.addItem(self.rois[key])
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
                    self.ch2_plot.removeItem(self.rois[key])

                    if self.rois['type'] == "EB":
                        self.rois[key] = pg.EllipseROI(pos, size, pen=(3, 9), scaleSnap=True, translateSnap=True),
                        self.ch1_plot.addItem(self.rois[key])
                        self.ch2_plot.addItem(self.rois[key])
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

                # get circular phase of each pixel, assuming origin in center of larger roi
                _phase_mask = self.phase_calc(_donut_mask.shape[0], _donut_mask.shape[1])
                _phase_mask *= _donut_mask

                # embed masks in img shape extracted from PrairieView
                donut_mask = np.copy(self._dummy_img)
                donut_mask[bounding_slices[0], bounding_slices[1]] = _donut_mask

                phase_mask = np.copy(self._dummy_img)
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
                self.wedge_sizes = np.array(self.wedge_size)
            elif self.rois['type'] == 'PB':
                raise NotImplementedError
            else:
                raise NotImplementedError

    def _make_donut_mask(self):

        bounding_slices = self.rois['outer_ellipse'].getArraySlice(self._dummy_img, self.ch1_curr_image)

        outer_mask = 1. * (self.rois['outer ellipse'].getArrayRegion(self._dummy_img, self.ch1_curr_image) > 0)
        _inner_mask = 1. * (self.rois['inner ellipse'].getArrayRegion(self._dummy_img, self.ch1_curr_image) > 0)

        inner_mask_rel_pos = (int(self.rois['inner ellipse'].pos()[1] - self.rois['outer ellipse'].pose()[1]),
                              int(self.rois['inner ellipse'].pos()[0] - self.rois['outer ellipse'].pose()[0]))

        inner_mask = np.zeros(outer_mask.shape)
        inner_mask[inner_mask_rel_pos[0]:inner_mask_rel_pos[0] + _inner_mask.shape[0],
        inner_mask_rel_pos[1]:inner_mask_rel_pos[1] + _inner_mask.shape[1]] = _inner_mask

        donut_mask = 1. * ((outer_mask - inner_mask) > 1E-5)
        return bounding_slices, donut_mask

    @staticmethod
    def phase_calc(nrows, ncols, center=None):
        phase_mat = np.zeros([nrows, ncols])

        if center is None:
            center = (int(nrows / 2), int(ncols / 2))

        for row, col in itertools.product(range(nrows), range(ncols)):
            phase_mat[row, col] = np.arctan2(col - center[1], row - center[0]) + np.pi + 1E-5

        return phase_mat

    def set_func_ch(self):

        if self.ch1FuncChanBfutton.isChecked():
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

    def _start_streaming(self, baseline_time=60, func_time=1, bump_signal_time=60):
        '''

        :param baseline_time: buffer size in seconds
        :return:
        '''

        num_func_samples = int(func_time / self._zstack_period)
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
            self._bump_signal = np.zeros((self.wedge_resolution, num_bump_samples))
            self._bump_phase = np.zeros((self.wedge_resolution, num_bump_samples))
            self._bump_mag = np.zeros((self.wedge_resolution, num_bump_samples))
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

    # @jit
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

    def _calc_bump_phase(self):

        signal = self._func_data_buffer.mean(axis=1) / np.percentile(self._baseline_data_buffer, 5, axis=1)

        if self.rois['type'] == 'EB':
            x, y = pol2cart(signal, self.wedge_centers)
            mag, phase = cart2pol(x.mean(), y.mean())
        elif self.rois['type'] == 'PB':
            mag, phase = None, None
            raise NotImplementedError
        else:
            mag, phase = None, None

        self._bump_signal[:, :-1] = self._bump_signal[:, 1:]
        self._bump_signal[:, -1] = signal
        self._bump_mag[:, :-1] = self._bump_mag[:, 1:]
        self._bump_mag[:, -1] = mag
        self._bump_phase[:, :-1] = self._bump_phase[:, 1:]
        self._bump_phase[:, -1] = phase

        self._bump_queue.put(f"{mag}, {phase}\n")

    def _plot_bump(self):
        self.bump_heatmap.setImage(self._bump_signal)
        self.bump_plot.setData(np.arange(0, self._bump_signal.shape[1]), self._bump_phase)

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
