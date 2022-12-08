import os
import threading
import multiprocessing as mp
import queue
import time
import sys
from collections import deque
import pickle

import numpy as np
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QApplication, QFileDialog, QInputDialog
import pyqtgraph as pg
import serial

from . import ui_gui
from .. import params
# import params
from . import fictrac_utils as ft_utils
# import utils
from ..utils import threaded, multiprocessed


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
        self.run_ft_evnt = mp.Event()
        self.ft_frames = None
        self.launch_fictrac_toggle.stateChanged.connect(self.toggle_fictrac)
        self._ft_process = None
        self._ft_manager = ft_utils.FicTracSocketManager()
        # self.save_fictrac_toggle.stateChanged.connect(self.set_fictrac_save_path)
        self.send_orientation_toggle.stateChanged.connect(self.toggle_send_orientation)
        self._send_orientation = threading.Event()
        self.pl_serial = None
        

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
        self.teensy_read_handle = self.continuous_read_teensy_com()
        while not self._isreading_teensy.is_set():
            time.sleep(.01)

        # change plot widgets to remote graphics views()
        self.cumm_path_plotwidget = pg.widgets.RemoteGraphicsView.RemoteGraphicsView(self.centralwidget)
        self.cumm_path_plotwidget.setObjectName(u"cumm_path_plotwidget")
        self.cumm_path_plotwidget.setGeometry(QtCore.QRect(30, 220, 321, 231))
        self.cumm_path_plotitem = self.config_remote_plot(self.cumm_path_plotwidget)
        
        self.heading_occ_plotwidget = pg.widgets.RemoteGraphicsView.RemoteGraphicsView(self.centralwidget)
        self.heading_occ_plotwidget.setObjectName(u"heading_occ_plotwidget")
        self.heading_occ_plotwidget.setGeometry(QtCore.QRect(490, 220, 321, 231))
        self.heading_occ_plotitem = self.config_remote_plot(self.heading_occ_plotwidget)
        
        plot_buffer_time = 600 #seconds
        self.plot_buffers = {'integrated x': deque(maxlen=int(ft_utils.FICTRAC_FRAME_RATE*plot_buffer_time)),
                            'integrated y': deque(maxlen=int(ft_utils.FICTRAC_FRAME_RATE*plot_buffer_time)),
                            'heading': deque(maxlen=int(ft_utils.FICTRAC_FRAME_RATE*plot_buffer_time))}
            
        self.cumm_path_checkbox.stateChanged.connect(self.toggle_cumm_path)
        self.heading_occ_checkbox.stateChanged.connect(self.toggle_heading_occ)
            
        
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
        
        # save ft_frames
        if self.ft_output_path is not None:
            scan_number = 0
            filename = os.path.join(self.ft_output_path,f"ft_frames_scan{scan_number}.pkl")
            while os.path.exists(filename):
                scan_number+=1
                filename = os.path.join(self.ft_output_path,f"ft_frames_scan{scan_number}.pkl")
            
            with open(filename,'wb') as file:
                pickle.dump(self.ft_frames,file)
            

        
    def trigger_opto(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'3,0\n')  # see teensy_control.ino


    def toggle_send_orientation(self):
        
        if self.send_orientation_toggle.isChecked():
            try: 
                self.pl_serial = serial.Serial(self._params['prairie_link_com'], baudrate = self._params['baudrate'])
            except serial.SerialException:
                raise Exception("prairie link serial port %s couldn't be opened" % self._params['prairie_link_com'])
            self._send_orientation.set()
        else:
            self._send_orientation.clear()
            self.pl_serial.close()
        
    def toggle_cumm_path(self): 
        self.plot_buffers['integrated x'].clear()
        self.plot_buffers['integrated y'].clear()
            
    def toggle_heading_occ(self):
        self.plot_buffers['heading'].clear()

    def set_exp(self):
        pass

    def run_exp(self):
        pass

    def abort_exp(self):
        pass
        
    def toggle_fictrac(self):
        '''

        :return:
        '''

        if self.launch_fictrac_toggle.isChecked():
            # # queue
            # self.ft_queue = queue.SimpleQueue()
            # # run fictrac event
            # self.run_ft_evnt.set()
            # output path
            self.ft_output_path = QFileDialog.getExistingDirectory(self.centralwidget,
                                                           "FicTrac Output File")
            #other args
            os.chdir(self.ft_output_path)
            print(self.ft_output_path)
            self._ft_manager.open()
            self._ft_manager.start_reading()
            self._read_ft_handle = self.read_ft_queue()
            
            self._ft_process = threaded(_run_ft_process(self.ft_queue, self.run_ft_evnt, self.ft_output_path))
        else:
            
            # self.run_ft_evnt.clear()
            self._ft_process.join()
            self._read_ft_handle.join()
        
    @threaded
    def continuous_read_teensy_com(self):
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
        srl.close()
        
    @threaded
    def read_ft_queue(self):
        
        while self.run_ft_evnt.is_set():
            # read queue
            if not self.ft_queue.empty():
                line = self.ft_queue.get()
                
                if self.cumm_path_checkbox.isChecked():
                    self.plot_buffers['integrated x'].append(line['integrated x'])
                    self.plot_buffers['integrated y'].append(line['integrated y'])
                    
                if self.heading_occ_checkbox.isChecked():
                    self.plot_buffers['heading'].append(line['heading'])
                
                # send heading info to prairie link    
                if self._send_orientation.is_set():
                    self.pl_serial.write(f"{line['heading']}\n".encode('UTF-8'))
            
    def update_plots(self):
        '''

        :return:
        '''

        if self.cumm_path_checkbox.isChecked():
            self.plot_cumm_path()
        if self.heading_occ_checkbox.isChecked():
            self.plot_heading_occ()
            
    def plot_cumm_path(self):
        self.cumm_path_plotitem.plot(self.plot_buffers['integrated x'], self.plot_buffers['integrated y'],
                                     pen=(200,200,200),clear=True, _callSync='off')
        
    def plot_heading_occ(self):
        hist, edges = utils.numba_histogram(self.plot_buffers['heading'], 20)
        x, y = utils.pol2cart(edges[1:],hist)
        self.heading_occ_plotitem.plot(x,y, fillLevel=.5,clear=True, _callSync='off')
        


    def closeEvent(self, event: QtGui.QCloseEvent):
        '''

        :param event:
        :return:
        '''

        # close fictrac
        self.run_ft_evnt.clear()
        self._ft_process.join()
        self._read_ft_handle.join()
        if self.pl_serial is not None:
            self.pl_serial.close()

        # stop scan
        self.stop_scan()
        self._isreading_teensy.clear()

        # join serial threads
        self.teensy_read_handle.join()
        self.teensy_input_serial.close()
        

        self.cumm_path_plotwidget.close()
        self.heading_occ_plotwidget.close()
        
        self.disconnect()
        event.accept()



def _run_ft_process(ft_queue, run_ft_evnt, output_path):
    ft_utils.MPFictracSocketManager.run(ft_queue, run_ft_evnt, output_path)

def main():
    app = QApplication(sys.argv)
    form = FLUI()
    form.show()
    r = app.exec_()
    sys.exit(r)


if __name__ == '__main__':
    main()
