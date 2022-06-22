import os
import subprocess
from fictrac_utils import FictracProcess
from multiprocessing import Queue, Process
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

TEENSY_INPUT_COM = "COM11"
TEENSY_OUTPUT_COM = "COM12"
ISREADING = True;


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
        self.ft_process = FictracProcess()

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
        self.teensy_read_queue = Queue()
        self.teensy_read_process = Process(target=self.continous_read, args = (self.teensy_read_queue,))
        self.teensy_read_process.start()

        self.cam_timer = QtCore.QTimer()
        self.cam_timer.timeout.connect(self.cam_updater)
        self.fictrac_timer = QtCorre.QTimer()
        self.fictrac_timer.timeout.connect(self.fictrac_plotter)
        self.zproj_timer.timeout.connect(self.zproj_plotter)


    def start_scan(self):

        self.teensy_input_serial.write(b'1') # see teensy_control.ino
        self.start_scan_push.setEnabled(False)
        self.trigger_opto_push.setEnabled(True)
        self.stop_scan_push.setEnabled(True)





    def stop_scan(self):
        self.teensy_input_serial.write(b'2') # see teensy_control.ino
        self.start_scan_push.setEnabled(True)
        self.trigger_opto_push.setEnabled(False)
        self.stop_scan_push.setEnabled(True)

        #TODO: gather SerialUSB2 values and save
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


    def toggle_cam_view(self):
        self.cam_view = self.cam_view_toggle.isChecked()

    def shutdown(self):

        if self.ft_process.p is not None:
            self.ft_process.close()
        self.stop_scan()
        ISREADING = False
        self.teensy_read_process.join()



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

    @staticmethod
    def continous_read(q):
        try:
            srl = serial.Serial(TEENSY_OUTPUT_COM)
        except serial.SerialException:
            raise Exception("teensy output serial port %s couldn't be opened" % TEENSY_OUTPUT_COM)

        while ISREADING:
            while srl.inWaiting()>0:
                q.put(srl.readline())

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
