import os
import ctypes

import numpy as np

from .. import params
from ..shared_memory import PMTBuffer

if params.hostname != 'bard-smaug-slayer':
    import win32com.client


# Only 1 instance of Prairie Link can be open
class RealTimePrairieLinkHandler:

    def __init__(self, remote_streaming_flag, pl_command_queue, **kwargs) -> None:

        self._pid = os.getpid()
        self._n_pmts = 2
        self.n_slices = 1  # ToDo: send this information from prairie_link_client
        self.n_zstacks_to_buffer = 100
        self._raw_dtype = np.int16
        self._n_raw_buffer_frames = 50

        self._pl = None
        self.open_praire_link()
        self.lines_per_frame = self._pl.LinesPerFrame()
        self.pixels_per_line = self._pl.PixelsPerLine()
        self.samples_per_pixel = self._pl.SamplesPerPixel()
        self.samples_per_frame = int(self._n_pmts * self.lines_per_frame * \
                                     self.pixels_per_line * self.samples_per_pixel)

        self.remote_streaming_flag = remote_streaming_flag
        self.pl_command_queue = pl_command_queue

        self._buffer_size = None
        self._pl_raw_buffer = None
        self._pl_raw_buffer_addr = None
        self._np_raw_buffer = None
        self._np_buffer_local = None
        self.pmt_buff_shape = None
        self.pmt_buff_axis_order = None
        self.pmt_buffer = None
        for k, v in kwargs.items():
            setattr(self, k, v)


    def open_praire_link(self):
        self._pl = win32com.client.Dispatch("PrairieLink64.Application")
        self._pl.Connect('127.0.1.1')
        self._pl.SendScriptCommands("-srd False")

    def close_prairie_link(self):
        self._pl.Disconnect()

    def _initialize_streaming_buffers(self):
        self._buffer_size = self.samples_per_frame * self._n_raw_buffer_frames
        self._np_raw_buffer = np.zeros((self._buffer_size,), dtype=np.int16)
        self._pl_raw_buffer = np.ctypeslib.as_ctypes(self._np_raw_buffer)
        # _buffer = ctypes.c_int * self._buffer_size
        # self._pl_raw_buffer = _buffer(*[0 for i in range(self._buffer_size)])
        self._pl_raw_buffer_addr = ctypes.addressof(self._pl_raw_buffer)
        # self._np_raw_buffer = np.ctypeslib.as_array(self._pl_raw_buffer)
        self._np_buffer_local = self._np_raw_buffer.copy()

        self.pmt_buff_shape = (self.n_zstacks_to_buffer,
                               self.n_slices,
                               self.lines_per_frame,
                               self.pixels_per_line,
                               self.samples_per_pixel,
                               self._n_pmts)
        self.pmt_buff_axis_order = ('buffer length',
                                    'z slice',
                                    'line',
                                    'column',
                                    'sample',
                                    'pmt')

        # update to incorporate synchronized frame index
        self.pmt_buffer = PMTBuffer(self.pmt_buff_shape, dtype=self._raw_dtype).create()

    def stream_data(self):
        # get buffer address
        print(f"-srd True {self._n_raw_buffer_frames}")
        self._pl.SendScriptCommands(f"-srd True {self._n_raw_buffer_frames}")
        self._initialize_streaming_buffers()
        while self.remote_streaming_flag.is_set():
            self.update()

        self._pl.SendScriptCommands('-srd False')
        # read data stream until no bytes are returned

        # unlink and destroy shared memory object
        self.pmt_buffer.close()

    def update(self):
        if not self.pl_command_queue.empty():
            self._pl.SendScriptCommands(self.pl_command_queue.get())
        n_samples = self.read_data_stream()
        if n_samples>0:
            self.pmt_buffer.update_buffer(n_samples, np.copy(self._np_raw_buffer[:n_samples]))

    def read_data_stream(self):
        return self._pl.ReadRawDataStream_3(self._pid, self._pl_raw_buffer_addr, self._buffer_size)
