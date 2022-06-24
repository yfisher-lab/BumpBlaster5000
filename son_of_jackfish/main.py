import os
import subprocess

# from multiprocessing import Queue, Process
import threading
import numpy as np
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog
from PyQt5.QtGui import QPixmap, QImage
from functools import partial
import sys
# from cam import FJCam
import gui
import serial


import fictrac_utils as ft_utils

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
        # self.save_fictrac_toggle.stateChanged.connect(self.save_fictrac)
        self.ft_manager = ft_utils.FicTracSocketManager() # add arguments

        ## set data output directory
        #TODO: talk to Bruker API to make similar paths
        self.set_path_push.clicked.connect(self.set_path)
        self.filepath = ""
        self.expt_name = ""
        self.exp_path = os.environ['USERPROFILE']

        try:
            self.teensy_input_serial = serial.Serial(TEENSY_INPUT_COM)
        except serial.SerialException:
            raise Exception("teensy input serial port %s couldn't be open" % TEENSY_INPUT_COM)


        # start serial port client
        self._isreading = threading.Event()
        self.teensy_read_queue = threading.Queue()
        self.teensy_read_handle = self.continuouse_read()
        # self.teensy_read_process.start()

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
        pass

    def zproj_plotter(self):
        pass






def main():
    app = QApplication(sys.argv)
    form = FLUI()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
