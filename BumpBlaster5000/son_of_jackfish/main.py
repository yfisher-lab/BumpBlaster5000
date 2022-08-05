import os
import threading
import queue
import time
import sys

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
import serial

import gui
from camera import Flea3Cam
import fictrac_utils as ft_utils
from BumpBlaster5000.utils import threaded, cart2pol, pol2cart

from BumpBlaster5000 import params

class FicTracLiveHeadingEstimate(ft_utils.FicTracSocketManager):
    def __init__(self, **kwargs):
        super(FicTracLiveHeadingEstimate, self).__init__(**kwargs)

        self._live_estimate_thread_handle = None

        self.heading = 0
        self.rot_vel = 0

        self._m = 1
        self._heading_x = 0
        self._heading_y = 0

        self.heading_x = 0
        self.heading_y = 0
        self.data_lock = threading.Lock()

    def start_reading(self, fictrac_output_file=os.path.join(os.getcwd(), "fictrac_output.log")):

        super(FicTracLiveHeadingEstimate, self).start_reading(fictrac_output_file=fictrac_output_file)
        self._live_estimate_thread_handle = self.start_live_heading_estimate()

    @threaded
    def start_live_heading_estimate(self):

        while self.ft_subprocess.open_evnt.is_set():
            # print(self.ft_queue.qsize())
            line = self.read_ft_queue()
            # print(self.ft_queue.qsize())
            if line is not None:
                x, y = pol2cart(float(line['speed'])+.02, float(line['heading']))
                with self.data_lock:
                    self._m += 1
                    self._heading_x += x
                    self._heading_y += y

                    self.heading_x = self._heading_x/self._m
                    self.heading_y = self._heading_y/self._m
                    speed, heading = cart2pol(self.heading_x,self.heading_y)
                    self.heading = heading
                    self.rot_vel = speed
            else:
                print("empty queue")

    def get_heading(self):

        with self.data_lock:
            self._m = 0
            self._heading_y = 0
            self._heading_x = 0

            return self.heading_x, self.heading_y, self.heading, self.rot_vel



class FLUI(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(FLUI, self).__init__(parent)
        self.setupUi(self)

        ## com port params
        self._params = params.FT_PC_PARAMS

        ## Teensy connections
        self.start_scan_push.clicked.connect(self.start_scan)
        self.stop_scan_push.clicked.connect(self.stop_scan)
        self.trigger_opto_push.clicked.connect(self.trigger_opto)

        ## camera preview
        self.cam_view_toggle.stateChanged.connect(self.toggle_cam_view)

        ## fictrac
        self.ft_manager = FicTracLiveHeadingEstimate()  # add arguments
        self.ft_frames = None
        self.launch_fictrac_toggle.stateChanged.connect(self.toggle_fictrac)

        ## set data output directory
        # TODO: force path to be set
        self.set_path_push.clicked.connect(self.set_path)
        self.filepath = ""
        self.expt_name = ""
        self.exp_path = os.environ['USERPROFILE']


        # start serial port to send commands to teensy
        try:
            self.teensy_input_serial = serial.Serial(self._params['teensy_input_com'], baudrate=self._params['baudrate'])
        except serial.SerialException:
            raise Exception("teensy input serial port %s couldn't be open" % self._params['teensy_input_com'])

        # start thread to read outputs from teensy
        self._isreading_teensy = threading.Event()
        self.teensy_read_queue = queue.Queue()
        self.teensy_read_handle = self.continuous_read()
        while not self._isreading_teensy.is_set():
            time.sleep(.01)
        self.teensy_queue_eater_handle = self.consume_teensy_queue()

        # initialize fly orientation plot
        self.fly_orientation_pi = self.fly_orientation_preview.getPlotItem()  # look up usage of pyqtgraph
        self.fly_orientation_pi.showAxis('left', False)
        self.fly_orientation_pi.showAxis('bottom', False)
        self.fly_orientation_pi.setAspectLocked(lock=True, ratio=1)
        self.fly_orientation_preview.addLine(x=0, pen=0.2)
        self.fly_orientation_preview.addLine(y=0, pen=0.2)
        self.fly_orientation_preview.setXRange(-.08, .08)
        self.fly_orientation_preview.setYRange(-.08, .08)
        for r in np.arange(.001, .08, .01):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.fly_orientation_preview.addItem(circle)

        # Transform to cartesian and plot
        self.fly_orientation_plot = self.fly_orientation_preview.getPlotItem().plot()  # look up usage of pyqtgraph
        x, y, _, _ = self.ft_manager.get_heading()
        self.fly_orientation_plot.setData([0, x], [0, self.ft_manager.heading_y],
                                          pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
        self.fly_orientation_preview.disableAutoRange()

        #initialize bump data plot
        self.bump_plot = self.fly_orientation_preview.getPlotItem().plot()
        self.bump_data = {'phase': None, 'mag': None}
        self._bump_queue = queue.Queue()
        self._isreading_bump = threading.Event()
        self._isreading_bump.set()
        self.bump_reader_thread = self._read_bump_data()
        # ToDo: make checkbox in designer for whether or not to plot bump data
        self.plot_bump = False


        self.fly_orientation_preview.show()

        # TODO: change this to phase offset history
        self.phase_offset_plot = self.scan_z_proj_preview
        self.phase_offset_buffer = np.zeros([1000,])

        # # TODO: add checkbox to enable preview of camera
        # self.cam = Flea3Cam()
        # self.cam.connect()
        # self.cam.start()
        # self.cam_prev_plot = self.cam_prev.getPlotItem()
        # self.cam_curr_image = pg.ImageItem()
        # self.cam_prev_plot.addItem(self.cam_curr_image)
        # self.cam_prev_plot.showAxis('left', False)
        # self.cam_prev_plot.showAxis('bottom', False)
        # self.cam_prev_plot.setAspectLocked(lock=True, ratio=1)
        # self.cam_prev_plot.invertY(True)
        # self.cam_curr_image.setImage(self.cam.get_frame())

        # start timers for plot updating
        # self.cam_timer = QtCore.QTimer()
        # self.cam_timer.timeout.connect(self.cam_updater)
        # self.cam_timer.start(10)

        # TODO: put fictrac and phase offset plot on same timer
        self.plot_update_timer = QtCore.QTimer()
        self.plot_update_timer.timeout.connect(self.update_plots)
        self.plot_update_timer.start(5)

        # self.fictrac_timer = QtCore.QTimer()
        # self.fictrac_timer.timeout.connect(self.fictrac_plotter)
        # self.fictrac_timer.start(5)
        #
        # # TODO: start offset plotter timer
        # self.phase_offset_timer = QtCore.QTimer()
        # self.phase_offset_timer.timeout.connect(self.phase_offset_plotter)
        # self.phase_offset_timer.start(20)

    def start_scan(self):
        '''

        :return:
        '''

        # if self.ft_manager.ft_subprocess.open_evnt.is_set():
        #     # if save fictrac
        #     # set filenames
        #     self.ft_manager.start_reading()

        self.teensy_input_serial.write(b'1')  # see teensy_control.ino
        self.start_scan_push.setEnabled(False)
        self.trigger_opto_push.setEnabled(True)
        self.stop_scan_push.setEnabled(True)

        # self.cam_timer.stop()

        self.ft_frames = {'start': None, 'abort': None}

    def stop_scan(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'2')  # see teensy_control.ino
        while self.ft_frames['abort'] is None:
            time.sleep(.01)

        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            df = self.ft_manager.stop_reading(return_pandas=True)

        self.start_scan_push.setEnabled(True)
        self.trigger_opto_push.setEnabled(False)
        self.stop_scan_push.setEnabled(True)

        #ToDo: handle case of fictrac not running. Error df referenced before assignment
        print(self.ft_frames)
        print(df['frame counter'].iloc[0:10])

        idx = df.index[(df['frame counter'] >= self.ft_frames['start']) & (df['frame counter']<= self.ft_frames['abort'])]
        df = df.loc[idx]

        ft_file = os.path.join(self.exp_path, "fictrac_aligned.csv")
        post = 0
        while os.path.exists(ft_file):
            post += 1
            ft_file = "%s_%d.csv" % (os.path.splitext(ft_file)[0], post)
        print(ft_file)
        df.to_csv(ft_file)

    def trigger_opto(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'3')  # see teensy_control.ino

    def toggle_fictrac(self):
        '''

        :return:
        '''

        if self.launch_fictrac_toggle.isChecked():
            self.ft_manager.open()

            self.ft_manager.start_reading()
            self.ft_manager.start_live_heading_estimate()
        else:
            self.ft_manager.close()

    def toggle_cam_view(self):
        '''

        :return:
        '''
        self.cam_view = self.cam_view_toggle.isChecked()


    def set_path(self):
        '''

        :return:
        '''

        options = QFileDialog.Options()
        self.filepath = QFileDialog.getExistingDirectory(self, "Select save directory")

        self.expt_name, ok = QInputDialog.getText(self, 'Enter experiment name', 'Experiment name:')
        if not ok:
            self.expt_name = ""

        if not (self.filepath == "" or self.expt_name == ""):
            self.filepath_label.setText(f'{self.filepath} >>> {self.expt_name}')
            self.exp_path = os.path.join(self.filepath, self.expt_name)
            os.mkdir(self.exp_path)

    @threaded
    def continuous_read(self):
        '''

        :return:
        '''
        try:
            srl = serial.Serial(self._params['teensy_output_com'], baudrate=self._params['baudrate'])
        except serial.SerialException:
            raise Exception("teensy output serial port %s couldn't be opened" % self._params['teensy_output_com'])

        self._isreading_teensy.set()

        while self._isreading_teensy.is_set():
            while srl.inWaiting() > 0:
                self.teensy_read_queue.put(srl.readline())
        srl.close()

    @threaded
    def consume_teensy_queue(self):
        '''

        :return:
        '''
        while self._isreading_teensy.is_set():
            if self.teensy_read_queue.qsize() > 0:
                msg = self.teensy_read_queue.get().decode('UTF-8').rstrip().split(',')
                print(msg)
                if msg[0] in set(("start", "abort")):
                    self.ft_frames[msg[0]] = int(msg[1])
                else:  # add functionality for other teensy ouputs here
                    pass

    @threaded
    def _read_bump_data(self):
        '''

        :return:
        '''

        with serial.Serial(self._params['pl_widget_com'], baudrate=self._params['baudrate']) as srl:
            while self._isreading_bump.is_set():
                while srl.inWaiting() > 0:
                    self._bump_queue.put(srl.readline().decode('UTF-8').rstrip())

    def cam_updater(self):
        '''

        :return:
        '''

        self.cam_curr_image.setImage(self.cam.get_frame())

    def update_plots(self):
        '''

        :return:
        '''

        heading = self.fictrac_plotter()
        if self.plot_bump:
            bump_phase = self.bump_plotter()
            self.phase_offset_buffer[:-1] = self.phase_offset_buffer[1:]
            self.phase_offset_buffer[-1] = heading-bump_phase
            self.offset_plotter(heading, bump_phase)


    def fictrac_plotter(self):
        '''

        :return:
        '''

        x, y, heading, _ = self.ft_manager.get_heading()
        self.fly_orientation_plot.setData(np.array([0, self.ft_manager.heading_x]),
                                          np.array([0, self.ft_manager.heading_y]))
        return heading


    def bump_plotter(self):
        '''

        :return:
        '''

        # read bump
        m = self._bump_queue.qsize()
        if m > 0:
            phase, mag = [], []
            for i in range(m):
                _phase, _mag = self._bump_queue.get().split(',')
                phase.append(_phase)
                mag.append(_mag)
            _x , _y = pol2cart(mag,phase)
            x = _x.mean()
            y = _y.mean()
            self.bump_plot.setData([0, x], [0, y])
            return cart2pol(x, y)[1]
        else:
            return None


    def offset_plotter(self):
        '''

        :return:
        '''
        self.phase_offset_plot.setData(self._phase_x,self.phase_offset_buffer)

    def closeEvent(self, event: QtGui.QCloseEvent):
        '''

        :param event:
        :return:
        '''

        # close fictrac
        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            self.ft_manager.close()

        # stop scan
        self.stop_scan()
        self._isreading_teensy.clear()

        # clear events for reading bump phase
        self._read_bump_event.clear()

        # join serial threads
        self.teensy_read_handle.join()
        self.teensy_queue_eater_handle.join()
        self.teensy_input_serial.close()
        self.bump_reader_thread.join()

        # close cameras
        self.cam.stop()
        self.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    form = FLUI()
    form.show()
    r = app.exec_()
    sys.exit(r)


if __name__ == '__main__':
    main()
