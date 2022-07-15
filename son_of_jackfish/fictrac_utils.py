import os
import socket
import select
import subprocess
import threading
import queue
from utils import threaded

import pandas as pd

FICTRAC_PATH = r'C:\Users\fisherlab\Documents\FicTrac211\fictrac.exe'
CONFIG_PATH = r'C:\Users\fisherlab\Documents\FicTrac211\config.txt'


class FicTracSubProcess:

    def __init__(self, fictrac_path=FICTRAC_PATH, config_file=CONFIG_PATH):
        self.fictrac_path = fictrac_path
        self.config_file = config_file
        self.p = None
        self.open_evnt = threading.Event()

    def open(self, creationflags=subprocess.CREATE_NEW_CONSOLE):
        self.p = subprocess.Popen([self.fictrac_path, self.config_file], creationflags=creationflags)
        self.open_evnt.set()

    def close(self):
        self.p.kill()
        self.p.terminate()
        self.p = None
        self.open_evnt.clear()


class FicTracSocketManager:
    """


    """

    def __init__(self, fictrac_path=FICTRAC_PATH, config_file=CONFIG_PATH, host='127.0.0.1', port=65413,
                 columns_to_read={'heading': 17, 'integrated x': 20, 'integrated y': 21, 'speed': 19},
                 ):
        """

        :param fictrac_path:
        :param config_file:
        :param host:
        :param port:
        :param columns_to_read:
        """

        self.ft_subprocess = FicTracSubProcess(fictrac_path=fictrac_path,
                                               config_file=config_file)
        # self.ft_subprocess.open()

        self.host = host
        self.port = port
        self.reading = threading.Event()
        self._reading_thread_handle = None
        self._sock = None
        self._socket_open = threading.Event()
        self.open_socket()

        self.ft_timeout = 1
        self._ft_buffer_lock = threading.Lock()
        self.ft_buffer = ""
        self.ft_output_path = None
        self._ft_output_handle = None
        self.ft_queue = queue.Queue()
        self.columns_to_read = columns_to_read

        # start read thread

    def open(self):
        self.ft_subprocess.open()
        if not self._socket_open.is_set():
            self.open_socket()


    def start_reading(self, fictrac_output_file=os.path.join(os.getcwd(), "fictrac_output.log")):
        """

        :param fictrac_output_file:
        :return:
        """
        # check if output file exists
        post = 0
        while os.path.exists(fictrac_output_file):
            post+=1
            fictrac_output_file = "%s_%d.log" % (os.path.splitext(fictrac_output_file)[0], post)



        self.ft_output_path = fictrac_output_file
        self._ft_output_handle = open(self.ft_output_path, 'w')
        # open output file
        self.reading.set()
        self._reading_thread_handle = self._read_thread()

    def stop_reading(self, return_pandas=False):
        """

        :return:
        """

        self.reading.clear()
        self._reading_thread_handle.join()
        self._reading_thread_handle = None

        self._ft_output_handle.close()
        self._ft_output_handle = None

        if return_pandas:
            df = pd.read_csv(self.ft_output_path, sep=' ', header=None,
                               names=('FT', 'frame counter', 'delta rot. x (cam)',
                                      'delta rot. y (cam)', 'delta rot. z (cam)',
                                      'delta rot. error', 'delta rot. x (lab)',
                                      'delta rot. y (lab)', 'delta rot. z (lab)',
                                      'abs. rot. x (cam)', 'abs. rot. y (cam)',
                                      'abs. rot. z (cam)', 'abs. rot. x (lab)',
                                      'abs. rot. y (lab)', 'abs. rot. z (lab)',
                                      'int. x (lab)', 'int. y (lab)', 'int. z (lab)',
                                      'movement dir.', 'movement speed', 'int. forward',
                                      'int. side', 'timestamp', 'sequence counter',
                                      'delta timestamp', 'alt. timestamp'))
            # delete self.ft_output_path
            os.remove(self.ft_output_path)

            return df

    def open_socket(self):
        """

        :return:
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.host, self.port))
        self._sock.setblocking(False)
        self._socket_open.set()


    def close_socket(self):
        """

        :return:
        """
        self._sock.close()
        self._socket_open.clear()

    def close(self):
        """

        :return:
        """

        if self.reading.is_set():
            self.stop_reading()

        if self._socket_open.is_set():
            self.close_socket()

        if self.ft_subprocess.open_evnt.is_set():
            self.ft_subprocess.close()

        if isinstance(self._reading_thread_handle, threading.Thread):
            self._reading_thread_handle.join()
            self._reading_thread_handle = None

        # find fictrac output files

        # delete fictrac output files
        #os.remove(os.getcwd())


    def read_ft_queue(self):
        """

        :return:
        """
        try:
            return self.ft_queue.get()
        except queue.Empty:
            return None

    @threaded  # defined at top, need to work on this one
    def _read_thread(self):
        # while fictrack is running
        # print("readthread started")
        while self.reading.is_set():
            # print("reading is set")

            # Check to see whether there is data waiting
            ready = select.select([self._sock], [], [], self.ft_timeout)

            # Only try to receive data if there is data waiting
            if ready[0]:
                # print("reading single line")
                single_line = self._process_line()
                # maybe want to replace queue with just a locked value to speed up plotting
                self.ft_queue.put(single_line)
            else:
                pass

    def _process_line(self):
        # Receive one data frame
        new_data = self._sock.recv(4096)  # new_data = 0 if no bytes sent
        if not new_data:
            return

        # Decode received data
        with self._ft_buffer_lock:
            self.ft_buffer += new_data.decode('UTF-8')

            # Find the first frame of data
            endline = self.ft_buffer.find("\n")
            line = self.ft_buffer[:endline]  # copy first frame
            # self.ft_buffer = self.ft_buffer[endline + 1:]  # delete first frame

            # Tokenise
            toks = line.split(", ")

            # Check that we have sensible tokens
            if ((len(toks) < 24) | (toks[0] != "FT")):
                print('Bad read')
                return

            # print to output file
            # print('ft_output', self.ft_buffer)
            self._ft_output_handle.writelines([str(self.ft_buffer),])
            self.ft_buffer = self.ft_buffer[endline + 1:]  # delete first frame

        # extract fictrac variables
        # (see https://github.com/rjdmoore/fictrac/blob/master/doc/data_header.txt for descriptions)
        return {k: toks[v] for k, v in self.columns_to_read.items()}
