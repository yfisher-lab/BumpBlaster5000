import os
import threading
import multiprocessing as mp
import queue
import time
import sys

import numpy as np
from PySide2 import QtCore, QtGui, QtWidgets, QRect
from PySide2.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
import serial

import ui_gui, params
import fictrac_utils as ft_utils
from utils import threaded

class FLUI(QtWidgets.QMainWindow, ui_gui.Ui_MainWindow):
    
    
    
    def __init__(self, parent=None):
        super(FLUI, self).__init__(parent)
        self.setupUi(self)

        ## com port params
        self._params = params.FT_PC_PARAMS

        ## Teensy connections
        self.start_scan_push.clicked.connect(self.start_scan)
        self.stop_scan_push.clicked.connect(self.stop_scan)
        self.trigger_opto_push.clicked.connect(self.trigger_opto)
        
        ## fictrac
        self.ft_manager = ft_utils.FicTracSocketManager()  # add arguments
        self.ft_frames = None
        self.launch_fictrac_toggle.stateChanged.connect(self.toggle_fictrac)
        self.save_fictrac_toggle.stateChanged.connect(self.set_fictrac_save_path)
        self.send_orientation_toggle.stateChanged.connect(self.send_orientation)
        

        ## set data output directory
        # TODO: force path to be set
        self.exp_filepath_push.clicked.connect(self.set_exp)
        self.run_exp_push.clicked.connect(self.run_exp)
        self.abort_exp_push.clicked.connect(self.abort_exp)


        # start serial port to send commands to teensy
        try:
            self.teensy_input_serial = serial.Serial(self._params['teensy_input_com'], baudrate=self._params['baudrate'])
        except serial.SerialException:
            raise Exception("teensy input serial port %s couldn't be open" % self._params['teensy_input_com'])

        # start thread to read outputs from teensy
        self._isreading_teensy = threading.Event()
        self.teensy_read_queue = queue.SimpleQueue()
        self.teensy_read_handle = self.continuous_read()
        while not self._isreading_teensy.is_set():
            time.sleep(.01)
        self.teensy_queue_eater_handle = self.consume_queue()

        # change plot widgets to remote graphics views()
        self.cumm_path_plotwidget = pg.widgets.RemoteGraphicsView.RemoteGraphicsView(self.centralwidget)
        self.cumm_path_plotwidget.setObjectName(u"cumm_path_plotwidget")
        self.cumm_path_plotwidget.setGeometry(QRect(30, 200, 321, 231))
        self.cumm_path_plotitem = self.config_remote_plot(self.cumm_path_plotwidget)
        
        self.heading_occ_plotwidget = pg.widgets.RemoteGraphicsView.RemoteGraphicsView(self.centralwidget)
        self.heading_occ_plotwidget.setObjectName(u"heading_occ_plotwidget")
        self.heading_occ_plotwidget.setGeometry(QRect(510, 200, 321, 231))
        self.heading_occ_plotitem = self.config_remote_plot(self.heading_occ_plotwidget)
        
        # 
        self.plot_update_timer = QtCore.QTimer()
        self.plot_update_timer.timeout.connect(self.update_plots)
        self.plot_update_timer.start()
    
    @staticmethod
    def config_remote_plot(remote_plot_widget):
        remote_plot_widget.pg.setConfigOptions(antialias = True)
        plot_item = remote_plot_widget.pg.PlotItem()
        plot_item._setProxyOptions(deferGetattr=True)
        plot_item.showAxis('left', False)
        plot_item.showAxis('bottom', False)
        remote_plot_widget.setCentralItem(plot_item)
        return plot_item
        

    def start_scan(self):
        '''

        :return:
        '''

        self.teensy_input_serial.write(b'1,0\n')  # see teensy_control.ino
        self.start_scan_push.setEnabled(False)
        self.trigger_opto_push.setEnabled(True)
        self.stop_scan_push.setEnabled(True)

        self.ft_frames = {'start': None, 'abort': None}

    def stop_scan(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'2,0\n')  # see teensy_control.ino
        while self.ft_frames['abort'] is None:
            time.sleep(.01)

        self.start_scan_push.setEnabled(True)
        self.trigger_opto_push.setEnabled(False)
        self.stop_scan_push.setEnabled(True)

        #ToDo: handle case of fictrac not running. Error df referenced before assignment
        print(self.ft_frames)
        # print(df['frame counter'].iloc[0:10])
        #
        # idx = df.index[(df['frame counter'] >= self.ft_frames['start']) & (df['frame counter']<= self.ft_frames['abort'])]
        # df = df.loc[idx]
        #
        # ft_file = os.path.join(self.exp_path, "fictrac_aligned.csv")
        # post = 0
        # while os.path.exists(ft_file):
        #     post += 1
        #     ft_file = "%s_%d.csv" % (os.path.splitext(ft_file)[0], post)
        # print(ft_file)
        # df.to_csv(ft_file)

    def trigger_opto(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'3,0\n')  # see teensy_control.ino

    def toggle_fictrac(self):
        '''

        :return:
        '''

        if self.launch_fictrac_toggle.isChecked():
            self.ft_manager.open()
            while not self.ft_manager.ft_subprocess.open_evnt.is_set():
                time.sleep(.001)

            self.ft_manager.start_reading()
        else:
            self.ft_manager.close()

    def toggle_cam_view(self):
        '''

        :return:
        '''
        self.cam_view = self.cam_view_toggle.isChecked()
        
        if self.cam_view:
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
            self.cam_timer.start(10)
        else:
            self.cam_timer.stop()
            # close cameras
            self.cam.stop()
        


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
                msg = srl.readline().decode('UTF-8').rstrip.split(',')
                if msg[0] in set(('start', 'abort')):
                    self.ft_frames[msg[0]] = int(msg[1])
                # self.teensy_read_queue.put(srl.readline())
        srl.close()


    # @threaded
    # def _read_bump_data(self):
    #     '''

    #     :return:
    #     '''

    #     with serial.Serial(self._params['pl_widget_com'], baudrate=self._params['baudrate']) as srl:
    #         while self._isreading_bump.is_set():
    #             while srl.inWaiting() > 0:
    #                 self._bump_queue.put(srl.readline().decode('UTF-8').rstrip())

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
        # if self.plot_bump:
        #     bump_phase = self.bump_plotter()
        #     self.phase_offset_buffer[:-1] = self.phase_offset_buffer[1:]
        #     self.phase_offset_buffer[-1] = heading-bump_phase
        #     self.offset_plotter(heading, bump_phase)

    def fictrac_plotter(self):
        '''

        :return:
        '''

        if self.ft_manager.ft_subprocess.open_evnt.is_set():

            m = self.ft_manager.ft_queue.qsize()
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
                # self.fly_orientation_preview.show()
                return None #cart2pol(x,y)[1]
            else:
                return None
        else:
            return None

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
        # self._read_bump_event.clear()

        # join serial threads
        self.teensy_read_handle.join()
        self.teensy_queue_eater_handle.join()
        self.teensy_input_serial.close()
        self.bump_reader_thread.join()

        self.cumm_path_plotwidget.close()
        self.heading_occ_plotwidget.close()
        
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
