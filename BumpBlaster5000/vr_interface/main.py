import os
import threading
import multiprocessing as mp
import queue
import time
import sys
from collections import deque
import pickle

import numpy as np
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui, QtWidgets
from pyqtgraph.QtWidgets import QFileDialog

import serial

from . import pg_gui
import gui
from .camera import Flea3Cam
from . import ui_gui
from .. import params
# import params
from . import fictrac_utils as ft_utils
# import utils
from ..utils import threaded, pol2cart, numba_wrapped_histogram


class BumpBlaster(pg_gui.WidgetWindow):
    
    
    
    def __init__(self):
        super().__init__()

        ## com port params
        self._params = params.FT_PC_PARAMS

        ## Teensy connections
        self.start_scan_button.clicked.connect(self.start_scan)
        self.stop_scan_button.clicked.connect(self.stop_scan)
        self.trigger_opto_button.clicked.connect(self.trigger_opto)
        
        ## fictrac
        self.ft_frames = None
        self.ft_manager = ft_utils.FicTracSocketManager()
        self.launch_fictrac_checkbox.stateChanged.connect(self.toggle_fictrac)
        self._ft_process = None
        # self.save_fictrac_toggle.stateChanged.connect(self.set_fictrac_save_path)
        self.send_orientation_checkbox.stateChanged.connect(self.toggle_send_orientation)
        self._send_orientation = threading.Event()
        self.pl_serial = None
        

        ## set data output directory
        # TODO: force path to be set
        self.load_exp_button.clicked.connect(self.set_exp)
        self.run_exp_button.clicked.connect(self.run_exp)
        self.abort_exp_button.clicked.connect(self.abort_exp)


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

        #
        self.cumm_path_plotitem = self.config_remote_plot(self.cumm_path_view)
        self.cumm_path_plotitem.enableAutoRange(enable=True)
        self.heading_occ_plotitem = self.config_remote_plot(self.heading_occ_view)
        self.heading_occ_plotitem.setXRange(-.5,.5)
        self.heading_occ_plotitem.setYRange(-.5,.5)
        
        self.plot_update_timer = QtCore.QTimer()
        self.plot_update_timer.timeout.connect(self.update_plots)
        self.plot_update_timer.start(5)
    
    @staticmethod
    def config_remote_plot(remote_plot_view):
        remote_plot_view.pg.setConfigOptions(antialias = True)
        plot_item = remote_plot_view.pg.PlotItem()
        plot_item._setProxyOptions(deferGetattr=True)
        plot_item.showAxis('left', False)
        plot_item.showAxis('bottom', False)
        remote_plot_view.setCentralItem(plot_item)
        return plot_item
        

    def start_scan(self):
        '''

        :return:
        '''

        self.teensy_input_serial.write(b'1,0\n')  # see teensy_control.ino
        self.start_scan_button.setEnabled(False)
        self.trigger_opto_button.setEnabled(True)
        self.stop_scan_button.setEnabled(True)

        self.ft_frames = {'start': None, 'abort': None}

    def stop_scan(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'2,0\n')  # see teensy_control.ino
        while self.ft_frames['abort'] is None:
            time.sleep(.01)

        self.start_scan_button.setEnabled(True)
        self.trigger_opto_button.setEnabled(False)
        self.stop_scan_button.setEnabled(True)
        
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
        
        if self.send_orientation_checkbox.isChecked():
            try: 
                self.pl_serial = serial.Serial(self._params['prairie_link_com'], baudrate = self._params['baudrate'])
            except serial.SerialException:
                raise Exception("prairie link serial port %s couldn't be opened" % self._params['prairie_link_com'])
            self._send_orientation.set()
        else:
            self._send_orientation.clear()
            self.pl_serial.close()
        
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

        if self.launch_fictrac_checkbox.isChecked():
            # output path
            self.ft_output_path = QFileDialog.getExistingDirectory(self.centralwidget,
                                                               "FicTrac Output File")
            #other args
            print(self.ft_output_path)
            self.ft_manager.open()
            self.ft_manager.start_reading(fictrac_output_path=self.ft_output_path)
            
            
        else:
            self.ft_manager.stop_reading()
            self.ft_manager.close()
        
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
        
   
            
    def update_plots(self):
        '''

        :return:
        '''

        
        self.plot_cumm_path()
        self.plot_heading_occ()
            
    def plot_cumm_path(self):
        # print('calling plot')
        self.cumm_path_plotitem.plot(self.ft_manager.plot_deques['integrated x'], self.ft_manager.plot_deques['integrated y'],
                                     clear=True, _callSync='off')
        
    def plot_heading_occ(self):
        hist, edges = numba_wrapped_histogram(np.array(self.ft_manager.plot_deques['heading']), 20)
        x, y = pol2cart(hist, edges[1:])
        self.heading_occ_plotitem.plot(x,y, fillLevel=1,clear=True, _callSync='off')
        


    def closeEvent(self, event: QtGui.QCloseEvent):
        '''

        :param event:
        :return:
        '''

        # close fictrac
        
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

    

if __name__ == '__main__':
    bb = BumpBlaster()
    pg.exec()
