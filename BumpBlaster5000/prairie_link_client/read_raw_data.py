import os
import multiprocessing as mp
import ctypes

import numpy as np

from .. import params, shared_memory
from ..shared_memory import PMTBuffer

if params.hostname != 'bard-smaug-slayer':
    import win32com.client


# Only 1 instance of Prairie Link can be open
class RealTimePrairieLinkHandler:

    def __init__(self, pl_command_queue, *kwargs) -> None:

        self._pid = os.getpid()
        self._n_pmts = 2
        self.n_slices = 1  # ToDo: send this information from
        self.n_stacks_to_buffer = 100
        self._raw_dtype = np.int16

        self.lines_per_frame = self._pl.LinesPerFrame()
        self.pixels_per_line = self._pl.PixelsPerLine()
        self.samples_per_pixel = self._pl.SamplesPerPixel()
        self.samples_per_frame = int(self._n_pmts * self.lines_per_frame * \
                                     self.pixels_per_line * self.samples_per_pixel)
        self.pl_command_queue = pl_command_queue
        for k, v in kwargs:
            setattr(self, k, v)

    def open_praire_link(self):
        self._pl = win32com.client.Dispatch("PrairieLink64.Application")
        return self

    def _initialize_streaming_buffers(self):
        self._buffer_size = self.samples_per_frame * self._n_buffer_frames
        BUFFER = ctypes.c_int * self._buffer_size
        self._pl_raw_buffer = BUFFER(*[0 for i in range(self._buffer_size)])
        self._pl_raw_buffer_addr = ctypes.addressof(self._pl_raw_buffer)
        self._np_raw_buffer = np.ctypeslib.as_array(self._plt_raw_buffer)
        self._np_buffer_local = np.zeros(self._np_raw_buffer.shape)

        self.pmt_buff_shape = (self.n_stacks_to_buffer,
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
        self.pmt_buffer = PMTBuffer(self.pmt_buff_shape).create().buffer

    def stream_data(self):
        # get buffer address
        self._pl.SendScriptScriptCommands(f"-srd True {self.n_buffer_frames}")

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
        self._np_buffer_local[:n_samples] = self._np_raw_buffer[:n_samples]
        self.pmt_buffer.update_buffer(n_samples, np.copy(self._np_buffer_local))
