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
from pyqtgraph import QtCore, QtGui, Qt
from pyqtgraph.Qt.QtWidgets import QFileDialog

import serial

from . import pg_gui
from .. import params, shared_memory
# import params
from . import fictrac_utils as ft_utils
# import utils
from ..utils import threaded, pol2cart, numba_wrapped_histogram, numba_histogram


class BumpBlaster(pg_gui.WidgetWindow):
    
    
    
    def __init__(self, plot_timeout = 30):
        super().__init__()

        ## com port params
        self._params = params.FT_PC_PARAMS

        ## Teensy push button connections
        self.start_scan_button.clicked.connect(self.start_scan)
        self.stop_scan_button.clicked.connect(self.stop_scan)
        self.trigger_opto_button.clicked.connect(self.trigger_opto)
        
        ## fictrac
        self.ft_frames = {'start': [], 'opto': [], 'abort': []}
        self.ft_manager = ft_utils.FicTracSocketManager()
        self.launch_fictrac_checkbox.stateChanged.connect(self.toggle_fictrac)
        self._ft_process = None
        self.send_orientation_checkbox.stateChanged.connect(self.toggle_send_orientation)
        self._send_orientation = threading.Event()

        #TODO: Set up prairie link serial, deal with send orientation checkbox
        self.pl_serial = None
        

        #TODO: deal with these functions
        self.load_exp_button.clicked.connect(self.set_exp)
        self.run_exp_button.clicked.connect(self.run_exp)
        self.abort_exp_button.clicked.connect(self.abort_exp)


        # start serial port to send commands to teensy
        try:
            self.teensy_input_serial = serial.Serial(self._params['teensy_input_com'], baudrate=self._params['baudrate'])
        except serial.SerialException:
            raise Exception("teensy input serial port %s couldn't be open" % self._params['teensy_input_com'])
        self.teensy_input_queue = mp.SimpleQueue()
        

        # start thread to read outputs from teensy
        self._isreading_teensy = threading.Event()
        self.teensy_read_queue = queue.SimpleQueue()
        self.teensy_read_handle = self.continuous_read_teensy_com()
        while not self._isreading_teensy.is_set():
            time.sleep(.01)

        #
        self.plot_deques = {'integrated x': None,
                            'integrated y': None,
                            'heading': None}
        self.reset_plots_button.clicked.connect(self.ft_manager.reset_plot_dequeus)
        #
        
        self.plot_update_timer = QtCore.QTimer()
        self.plot_update_timer.timeout.connect(self.update_plots)
        self.plot_update_timer.start(30)
        
    
        _, _ = numba_histogram(np.linspace(0,10), 5)
        _, _ = pol2cart(0,0)

    def start_scan(self):
        '''

        :return:
        '''

        self.teensy_input_serial.write(b'0,1\n')  # see teensy_control.ino
        self.start_scan_button.setEnabled(False)
        self.trigger_opto_button.setEnabled(True)
        self.stop_scan_button.setEnabled(True)

        # self.ft_frames = {'start': None, 'opto': None, 'abort': None}

    def stop_scan(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'0,2\n')  # see teensy_control.ino
        while self.ft_frames['abort'] is None:
            time.sleep(.01)

        self.start_scan_button.setEnabled(True)
        self.trigger_opto_button.setEnabled(False)
        self.stop_scan_button.setEnabled(True)
        
        # save ft_frames
        if self.ft_output_path is not None:
            scan_number = 0
            basename, ext = os.path.splitext(self.ft_output_path)

            filename = os.path.join(f"{basename}_scan{scan_number}.pkl")
            while os.path.exists(filename):
                scan_number+=1
                filename = os.path.join(self.ft_output_path,f"ft_frames_scan{scan_number}.pkl")
            
            with open(filename,'wb') as file:
                pickle.dump(self.ft_frames,file)
            

        
    def trigger_opto(self):
        '''

        :return:
        '''
        self.teensy_input_serial.write(b'0,3\n')  # see teensy_control.ino


    def toggle_send_orientation(self):
        
        if self.send_orientation_checkbox.isChecked():
            try: 
                self.pl_serial = serial.Serial(self._params['pl_com'], baudrate = self._params['baudrate'])
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
            self.ft_output_path = QFileDialog.getSaveFileName(self.layout,
                                                               "FicTrac Output File")[0]
            #other args
            print(self.ft_output_path)
            #TODO: make this an actual filename rather than a directory and extract directory
            self.ft_manager.open(output_path=self.ft_output_path)
            self.ft_manager.start_reading()
            self._pl_serial_thread = self.write_to_pl_com()
            for k in self.plot_deques.keys():
                self.plot_deques[k] = shared_memory.CircularFlatBuffer(int(450*600), name = k).connect()
            
            
        else:
            self.ft_manager.stop_reading()
            self.ft_manager.close()
            self._pl_serial_thread.join()

    @threaded 
    def write_to_pl_com(self):
        while self.ft_manager.reading.is_set():
            if not self.ft_manager.ft_serial_queue.empty():
                heading = self.ft_manager.ft_serial_queue.get()
                if self._send_orientation.is_set():
                    self.pl_serial.write(f"{heading}\n".encode('UTF-8'))


    @threaded
    def write_to_teensy_input_com(self):
        while self._isreading_teensy.set():
            if not self.teensy_input_queue.empty():
                self.teensy_input_serial.write(self.teensy_input_queue.get())
    

        
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
                msg = srl.readline().decode('UTF-8').rstrip().split(',')
                if msg[0] in set(('start', 'opto', 'abort')):
                    self.ft_frames[msg[0]].append(int(msg[1]))
        srl.close()

            
    def update_plots(self):
        '''

        :return:
        '''

        if self.ft_manager.reading.is_set():
            self.plot_cumm_path()
            self.plot_heading_hist()
            # self.plot_current_heading()
            
    def plot_cumm_path(self):
        self.cumm_path_plotitem.plot(self.plot_deques['integrated x'].buff[self.plot_deques['integrated y'].first_filled_index[0]:], self.plot_deques['integrated y'].vals,
                                     clear=True, _callSync='off')
        
    def plot_heading_hist(self):
        headings = self.plot_deques['heading'].vals
        hist, edges = numba_histogram(headings, 20)

        # self.plot_current_heading(headings[-1])

        # print(hist,edges)
        # x, y = pol2cart(hist, edges)
        self.heading_hist_plotitem.plot(edges[1:], hist, brush=(0,0,255,150),
                                        fillLevel=0, clear=True, _callSync='off')
        self.heading_hist_plotitem.plot([headings[-1], headings[-1]], [0,.2], pen=(255,0,0))
        # self.heading_hist_plotitem.addLine(x=0,pen=.4)
        # self.heading_hist_plotitem.addLine(y=0, pen=.4)

    def plot_current_heading(self,heading):

        x,y = pol2cart(1.,heading)
        self.current_heading_plotitem.plot([0,x],[0,y], pen=(200, 200, 200), symbolBrush=(255, 0, 0),
                     symbolPen='w', clear = True, _callSync='off')
        # self.current_heading_plotitem.addLine(x=0, pen=.4)
        # self.current_heading_plotitem.addLine(y=0, pen=.4)

        
        


    def closeEvent(self, event: QtGui.QCloseEvent):
        '''

        :param event:
        :return:
        '''

        # close fictrac
        self.ft_manager.stop_reading()
        self.ft_manager.close()
        self._pl_serial_thread.join()
        
        # stop scan
        self.stop_scan()
        self._isreading_teensy.clear()

        # join serial threads
        self.teensy_read_handle.join()
        self.teensy_input_serial.close()
        

        self.cumm_path_plotwidget.close()
        self.heading_hist_plotwidget.close()
        
        self.disconnect()
        event.accept()
