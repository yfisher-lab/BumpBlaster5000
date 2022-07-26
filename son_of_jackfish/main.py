import os
import threading
import queue
import time

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
import sys

import gui
import serial

from camera import Flea3Cam

import fictrac_utils as ft_utils
from utils import threaded

TEENSY_INPUT_COM = "COM7"
TEENSY_OUTPUT_COM = "COM9"


class FLUI(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(FLUI, self).__init__(parent)
        self.setupUi(self)



        ## Teensy connections
        self.start_scan_push.clicked.connect(self.start_scan)
        self.stop_scan_push.clicked.connect(self.stop_scan)
        self.trigger_opto_push.clicked.connect(self.trigger_opto)

        ## camera preview
        self.cam_view_toggle.stateChanged.connect(self.toggle_cam_view)

        ## fictrac
        self.ft_manager = ft_utils.FicTracSocketManager()  # add arguments
        self.ft_frames = None
        self.launch_fictrac_toggle.stateChanged.connect(self.toggle_fictrac)

        ## set data output directory
        # TODO: force path to be set
        # TODO: talk to Bruker API to make similar paths
        self.set_path_push.clicked.connect(self.set_path)
        self.filepath = ""
        self.expt_name = ""
        self.exp_path = os.environ['USERPROFILE']

        # TODO: create socket to prairie_link_client

        # start serial port to send commands to teensy
        try:
            self.teensy_input_serial = serial.Serial(TEENSY_INPUT_COM)
        except serial.SerialException:
            raise Exception("teensy input serial port %s couldn't be open" % TEENSY_INPUT_COM)
        # start thread to read outputs from teensy
        self._isreading = threading.Event()
        self.teensy_read_queue = queue.Queue()
        self.teensy_read_handle = self.continuous_read()

        while not self._isreading.is_set():
            time.sleep(.01)
        self.teensy_queue_eater_handle = self.consume_queue()

        # initialize fly orientation plot
        self.fly_theta = np.pi / 2.
        self.fly_speed = 0.
        self.fly_orientation_pi = self.fly_orientation_preview.getPlotItem()  # look up usage of pyqtgraph
        self.fly_orientation_plot = self.fly_orientation_preview.getPlotItem().plot()  # look up usage of pyqtgraph
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
        x = (self.fly_speed + .02) * np.cos(self.fly_theta)
        y = (self.fly_speed + .02) * np.sin(self.fly_theta)

        self.fly_orientation_plot.setData([0, x], [0, y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
        self.fly_orientation_preview.show()

        # TODO: change this to EB/PB phase calculation, plot like behavioral orientation
        # initialize z stack plot
        self.z_proj_data = [0]
        self.scan_z_proj_plot = self.scan_z_proj_preview  # .getPlotItem().plot() # want to plot z-stack or BOT of glomeruli

        # TODO: add another plot that's phase offset between fly orientation and bump phase

        # TODO: add checkbox to enable preview of camera
        self.cam = Flea3Cam()
        self.cam.connect()
        self.cam.start()
        self.cam_prev_plot = self.cam_prev.getPlotItem()
        self.cam_curr_image = pg.ImageItem()
        self.cam_prev_plot.addItem(self.cam_curr_image)
        self.cam_prev_plot.showAxis('left', False)
        self.cam_prev_plot.showAxis('bottom', False)
        self.cam_prev_plot.setAspectLocked(lock=True, ratio=1)
        self.cam_prev_plot.invertY(True)
        self.cam_curr_image.setImage(self.cam.get_frame())

        # start timers for plot updating
        self.cam_timer = QtCore.QTimer()
        self.cam_timer.timeout.connect(self.cam_updater)
        self.cam_timer.start(20)

        self.fictrac_timer = QtCore.QTimer()
        self.fictrac_timer.timeout.connect(self.fictrac_plotter)
        self.fictrac_timer.start()

        # TODO: start bump orientation timer
        # self.zproj_timer = QtCore.QTimer()
        # self.zproj_timer.timeout.connect(self.zproj_plotter)

        # TODO: start offset plotter timer

    def start_scan(self):

        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            # if save fictrac
            # set filenames
            self.ft_manager.start_reading()

        self.teensy_input_serial.write(b'1')  # see teensy_control.ino
        self.start_scan_push.setEnabled(False)
        self.trigger_opto_push.setEnabled(True)
        self.stop_scan_push.setEnabled(True)

        self.ft_frames = {'start': None, 'abort': None}

    def stop_scan(self):
        self.teensy_input_serial.write(b'2')  # see teensy_control.ino
        while self.ft_frames['abort'] is None:
            time.sleep(.01)

        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            df = self.ft_manager.stop_reading(return_pandas=True)

        self.start_scan_push.setEnabled(True)
        self.trigger_opto_push.setEnabled(False)
        self.stop_scan_push.setEnabled(True)


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

        # for msg in iter(self.teensy_read_queue.get, b'END QUEUE\r\n'):
        #     print(msg.decode('UTF-8').rstrip())

    def trigger_opto(self):
        self.teensy_input_serial.write(b'3')  # see teensy_control.ino

    def toggle_fictrac(self):

        if self.launch_fictrac_toggle.isChecked():
            self.ft_manager.open()
        else:
            self.ft_manager.close()

    def toggle_cam_view(self):
        self.cam_view = self.cam_view_toggle.isChecked()

    def closeEvent(self, event: QtGui.QCloseEvent):

        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            self.ft_manager.close()

        self.stop_scan()
        self._isreading.clear()

        self.teensy_read_handle.join()
        self.teensy_queue_eater_handle.join()
        self.teensy_input_serial.close()

        # TODO: find output and log files from fictrac and get rid of them

        # close cameras
        self.cam.stop()
        self.disconnect()
        event.accept()


    def set_path(self):

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
        try:
            srl = serial.Serial(TEENSY_OUTPUT_COM)
        except serial.SerialException:
            raise Exception("teensy output serial port %s couldn't be opened" % TEENSY_OUTPUT_COM)

        self._isreading.set()

        while self._isreading.is_set():
            while srl.inWaiting() > 0:
                self.teensy_read_queue.put(srl.readline())
        srl.close()

    @threaded
    def consume_queue(self):
        '''

        :return:
        '''


        while self._isreading.is_set():
            if self.teensy_read_queue.qsize() > 0:
                msg = self.teensy_read_queue.get().decode('UTF-8').rstrip().split(',')
                print(msg)
                if msg[0] in set(("start", "abort")):
                    self.ft_frames[msg[0]] = int(msg[1])
                else:  # add functionality for other teensy ouputs here
                    pass

    def cam_updater(self):
        '''

        :return:
        '''

        self.cam_curr_image.setImage(self.cam.get_frame())

    def fictrac_plotter(self):

        if self.ft_manager.ft_subprocess.open_evnt.is_set():

            m = self.ft_manager.ft_queue.qsize()
            # print(m)
            if m > 0:

                x, y, speed = 0, 0, 0
                for _ in range(m):
                    line = self.ft_manager.ft_queue.get()
                    heading = float(line['heading'])
                    speed += float(line['speed'])
                    x += np.cos(heading)
                    y += np.sin(heading)

                x /= m
                y /= m
                speed /= m
                self.fly_orientation_plot.setData((speed + .02) * np.array([0, x]), (speed + .02) * np.array([0, y]))
                self.fly_orientation_preview.show()

    def zproj_plotter(self):
        pass


def main():
    app = QApplication(sys.argv)
    form = FLUI()
    form.show()
    r = app.exec_()
    # form.shutdown()
    sys.exit(r)


if __name__ == '__main__':
    main()
