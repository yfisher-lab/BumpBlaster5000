import os
import socket
import subprocess
import threading


FICTRAC_PATH = r'C:\Users\fisherlab\Documents\FicTrac211\fictrac.exe'
CONFIG_PATH = r'C:\Users\fisherlab\Documents\FicTrac211\config.txt'

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

# try using events, locks, or barriers instead of globals


class FicTracSubProcess:

    def __init__(self, fictrac_path=FICTRAC_PATH, config_file=CONFIG_PATH):
        self.fictrac_path = fictrac_path
        self.config_file = config_file
        self.p = None
        self.open_evnt = threading.Event()

    def open(self, creationflags=subprocess.CREATE_NEW_CONSOLE):
        self.p = subprocess.Popen([self.fictrac_path, self.config_file], creationflags=creationflags)
        self.open_evnt.is_set()

    def close(self):
        self.p.kill()
        self.p.terminate()
        self.p = None
        self.open_evnt.clear()


class FicTracSocketManager:

    def __init__(self, fictrac_path = FICTRAC_PATH, config_file=CONFIG_PATH, host='127.0.0.1', port=65413,
                 columns_to_read = {'heading':17, 'integrated x': 20, 'integrated y': 21},
                 ):

        self.ft_subprocess = FicTracSubProcess(fictrac_path=fictrac_path,
                                               config_file=config_file)
        self.ft_subprocess.open()

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


        # start read thread

    def start_reading(self, fictrac_output_file = os.path.join(os.getcwd(),"fictrac_output.log")):
        # check if output file exists
        self.ft_output_path = fictrac_output_file
        # open output file
        self.reading.is_set()
        self._reading_thread_handle = self.read_thread()

    def stop_reading(self):
        self.reading.clear()
        self._reading_thread_handle.join()
        self.close_socket()
        # close output file

    def open_socket(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.host, self.port))
        self._sock.setblocking(False)
        self.sock_open.set()

    def close_socket(self):
        self._sock.close()
        self.sock_open.clear()


    @threaded # defined at top, need to work on this one
    def read_thread(self):

        # while fictrack is running
        while self.reading.is_set():

            # Check to see whether there is data waiting
            ready = select.select([sock], [], [], fictrac_timeout)

            # Only try to receive data if there is data waiting
            if ready[0]:
                self._process_line()
            else:
                pass


        self.socket_open.clear()

    def _process_line(self, recvd_data):
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
            self.ft_buffer = self.ft_buffer[endline + 1:]  # delete first frame

        # Tokenise
        toks = line.split(", ")

        # Check that we have sensible tokens
        if ((len(toks) < 24) | (toks[0] != "FT")):
            print('Bad read')
            return

        # print to output file

        # extract fictrac variables
        # (see https://github.com/rjdmoore/fictrac/blob/master/doc/data_header.txt for descriptions)
        return {k:toks[v] for k,v in self.columns_to_read.items()}



