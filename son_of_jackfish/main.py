import os

import threading
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
from PyQt5.QtGui import QPixmap, QImage
from functools import partial
import sys
# from cam import FJCam
import gui
import serial


import fictrac_utils as ft_utils
from utils import threaded

TEENSY_INPUT_COM = "COM11"
TEENSY_OUTPUT_COM = "COM12"


class FLUI(QtWidgets.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(FLUI, self).__init__(parent)
        self.setupUi(self)

        ## Teensy connections
        self.start_scan_push.clicked.connect(self.start_scan)
        self.stop_scan_push.clicked.connect(self.stop_scan)
        self.trigger_opto_push.clicked.connect(self.trigger_opto)

        #TODO: edit to deal with our cameras and FicTrac params

        ## camera preview
        self.cam_view_toggle.stateChanged.connect(self.toggle_cam_view)

        ## fictrac
        self.launch_fictrac_toggle.stateChanged.connect(self.toggle_fictrac)
        self.ft_manager = ft_utils.FicTracSocketManager() # add arguments

        ## set data output directory
        #TODO: talk to Bruker API to make similar paths
        self.set_path_push.clicked.connect(self.set_path)
        self.filepath = ""
        self.expt_name = ""
        self.exp_path = os.environ['USERPROFILE']

        #TODO: create socket to prairie_link_client


        try:
            self.teensy_input_serial = serial.Serial(TEENSY_INPUT_COM)
        except serial.SerialException:
            raise Exception("teensy input serial port %s couldn't be open" % TEENSY_INPUT_COM)


        # start serial port client
        self._isreading = threading.Event()
        self.teensy_read_queue = threading.Queue()
        self.teensy_read_handle = self.continuouse_read()
        # self.teensy_read_process.start()

        # initialize fly orientation plot
        self.fly_theta = [np.pi/2.]
        self.fly_speed = 0.
        self.fly_orientation_plot = self.fly_orientation_preview.getPlotItem().plot() # look up usage of pyqtgraph
        self.fly_orientation_plot.addLine(x=0, pen=0.2)
        self.fly_orientation_plot.addLine(y=0, pen=0.2)
        for r in range(2, 20, 2):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.fly_orientation_plot.addItem(circle)

        # Transform to cartesian and plot
        x = (self.fly_speed+1) * np.cos(self.fly_theta)
        y = (self.fly_speed+1) * np.sin(self.fly_theta)
        self.fly_orientation_plot.plot([0, x], [0, y], pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')
        self.fly_orientation_plot.setData(self.fly_orientation_data)
        self.fly_orientation_preview.show()

        # initialize z stack plot
        self.z_proj_data = [0]
        self.scan_z_proj_plot = self.scan_z_proj_preview.getPlotItem().plot() # want to plot z-stack or BOT of glomeruli
        self.scan_z_proj_plot.setData([0])
        self.scan_z_proj_preview.show()


        #TODO: start camera and add checkbox to enable preview of camera, add data to box

        # start timers for plot updating
        #TODO: look up default timing on QTimer
        self.cam_timer = QtCore.QTimer()
        self.cam_timer.timeout.connect(self.cam_updater)
        self.fictrac_timer = QtCore.QTimer()
        self.fictrac_timer.timeout.connect(self.fictrac_plotter)
        self.zproj_timer = QtCore.QTimer()
        self.zproj_timer.timeout.connect(self.zproj_plotter)


    def start_scan(self):

        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            # if save fictrac
            # set filenames
            self.ft_manager.start_reading()

        self.teensy_input_serial.write(b'1') # see teensy_control.ino
        self.start_scan_push.setEnabled(False)
        self.trigger_opto_push.setEnabled(True)
        self.stop_scan_push.setEnabled(True)


    def stop_scan(self):
        self.teensy_input_serial.write(b'2') # see teensy_control.ino
        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            # if save fictrac
            # set filenames
            self.ft_manager.stop_reading()

        self.start_scan_push.setEnabled(True)
        self.trigger_opto_push.setEnabled(False)
        self.stop_scan_push.setEnabled(True)

        #TODO: gather SerialUSB2 values and save fictrac information
        # currently just printing to debug
        for msg in iter(self.teensy_read_queue.get, b'END QUEUE\r\n'):
            print(msg.decode('UTF-8').rstrip())

    def trigger_opto(self):
        self.teensy_input_serial.write(b'3') # see teensy_control.ino

    def toggle_fictrac(self):
        #TODO: integrate Minseung's FicTrac_Utils
        if self.launch_fictrac_toggle.isChecked():
            self.ft_process.open()
        else:
            self.ft_process.close()
            #TODO: find Fictrac

    def toggle_cam_view(self):
        self.cam_view = self.cam_view_toggle.isChecked()

    def shutdown(self):

        if self.ft_manager.ft_subprocess.open_evnt.is_set():
            self.ft_manager.close()

        self.stop_scan()
        self._isreading.clear()


        self.teensy_read_handle.join()
        self.teensy_input_serial.close()

        #TODO: find output and log files from fictrac and get rid of them

        # close cameras

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
    def continous_read(self):
        try:
            srl = serial.Serial(TEENSY_OUTPUT_COM)
        except serial.SerialException:
            raise Exception("teensy output serial port %s couldn't be opened" % TEENSY_OUTPUT_COM)

        self._isreading.set()

        while self._isreading.is_set():
            while srl.inWaiting()>0:
                self.teensy_read_queue.put(srl.readline())
        srl.close()

    def cam_updater(self):
        pass

    def fictrac_plotter(self):

        m = self.ft_manager.ft_queue.size
        x, y, speed = 0, 0, 0
        for _ in range(m):
            heading = self.ft_manager.ft_queue.get()[17]
            speed += self.ft_manager.ft_queue.get()[19]
            x += np.sin(heading)
            y += np.sing(heading)

        x /= m
        y /= m
        speed /= m
        self.fly_orientation_plot.setData((speed+1.) * np.array([0, x]),(speed+1.) * np.array([0, y]))
        self.fly_orientation_preview.show()

    def zproj_plotter(self):
        pass






def main():
    app = QApplication(sys.argv)
    form = FLUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
