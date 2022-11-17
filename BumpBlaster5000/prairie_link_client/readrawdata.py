import os
import multiprocessing as mp
import ctypes

import numpy as np

from sys import platform
if platform != 'linux':
    import win32com.client

# from time import sleep

NP_SHARED_NAME = 'pmt_buffer_array'

#ToDo: change this to shared memory object?
class BufferFrameIndex:


    def __init__(self, initval=0, maxval = 100):
        self.val = mp.Value('i', initval)

    def increment(self):
        with self.val.get_lock():
            self.val.value = (self.val.value+1) % self.maxval
    
    @property
    def value(self):
        with self.val.get_lock():
            return self.val.value

class MultiDimBuffer():
    def __init__(self, shape, name='pmt_buffer', dtype=np.int16,
                axis_order=None):

        self.name = 'pmt_buffer'
        self.shape = shape
        self.dtype = dtype
        self._size = np.dtype(dtype).itemsize() * np.prod(np.array(shape))
        
        self._shm = None
        self.buffer = None
        self.creator = False

    def create(self):
        self._shm = mp.shared_memory.SharedMemory(create=True, size=self._size, name = self.name)
        self._init_buffer()
        self.creator = True
        return self

    def connect(self):
        if not self.creator:
            self._shm = mp.shared_memory.SharedMemory(name = self.name)
        else: 
            return
        self._init_buffer()
        return self

    def _init_buffer(self):
        self.buffer = np.ndarray(shape=self.shape, dtype=self.dtype, buffer=self._shm.buf)
        self.buffer[:]=0

    def close(self):
        self._shm.close()
        if self.creator:
            self._shm.unlink()


class PMTBuffer(MultiDimBuffer):

    def __init__(self, shape, frame_sync = None, name='pmt_buffer', dtype=np.int16, axis_order=None):
        super().__init__(shape, name, dtype, axis_order)

        if frame_sync is None:
            self.frame_sync = BufferFrameIndex(maxval=shape[0])
        
        if axis_order is None:
            self.axis_order = ('buffer length',
                                'z slice',
                                'line',
                                'column',
                                'sample',
                                'pmt')

        self.buffer_index = 0
        self.max_buffer = shape[0]

        self.z_index = 0
        self.max_z_index = shape[1]

        self.line = 0
        self.max_line = shape[2]

        self.column = 0
        self.max_column = shape[3]

        self.sample = 0
        self.max_samples = shape[4]

        self.pmt = 0
        self.max_pmt = shape[5]

        self.samples_per_frame = np.prod(shape[2:])

        self.curr_flat_index = 0

    def update_buffer(self, n_samples, flat_data):

        n_new_frames, new_flat_index = divmod(self.curr_flat_index+n_samples, 
                                            self.samples_per_frame)
        
        if n_new_frames == 0:
            fill_frame(self.curr_flat_index,new_flat_index, flat_data)
        else:
            flat_data_idx = 0
            for frame in range(n_new_frames):
                frame_size = self.samples_per_frame-self.curr_flat_index
                new_flat_data_idx = flat_data_idx + frame_size
                # fill frame
                tmp_data = flat_data[flat_data_idx:new_flat_data_idx]
                fill_frame(self.curr_flat_index,self.samples_per_frame, tmp_data)
                
                # set curr_flat index to 0
                flat_data_idx=new_flat_data_idx
                self.curr_flat_index=0

                # update z_index
                new_buff_ind, self.z_index = divmod(self.z_index+1,self.max_z_index)

                # update 
                self.buffer_index = (self.buffer_index + new_buff_ind) % self.max_buffer

            fill_frame(self.curr_flat_index,new_flat_index, flat_data[flat_data_idx:])


        def fill_frame(start,stop,data_slice):
            sub_mat = self.buffer[self.buffer_index,self.z_index,:,:,:,:]
            lines, columns, samples, pmts = np.unravel_index(np.arange(start,stop))
            sub_mat[lines,columns,samples,pmts]=data_slice

            


    
    


# Only 1 instance of Prairie Link can be open
class RealTimePrairieLinkHandler:

    def __init__(self, pl_command_queue, 
                       np_shared_name = None, *kwargs ) -> None:

        self._pid = os.getpid()
        self._n_pmts = 2
        self.n_slices = 1 #ToDo: send this information from 
        self.n_stacks_to_buffer = 100
        self._raw_dtype = np.int16
        
        if np_shared_name is None:
            self.np_shared_name = NP_SHARED_NAME

        self.lines_per_frame = self._pl.LinesPerFrame()
        self.pixels_per_line = self._pl.PixelsPerLine()
        self.samples_per_pixel = self._pl.SamplesPerPixel()
        self.samples_per_frame = int(self._n_pmts * self.lines_per_frame * \
                                self.pixels_per_line * self.samples_per_pixel)

        
        

    def open_praire_link(self):
        self._pl = win32com.client.Dispatch("PrairieLink64.Application")
        return self

    def _initialize_streaming_buffers(self):
        self._buffer_size = self.samples_per_frame * self._n_buffer_frames
        BUFFER = ctypes.c_int * self._buffer_size
        self._pl_raw_buffer = BUFFER(*[0 for i in range(self._buffer_size)])
        self._pl_raw_buffer_addr = ctypes.addressof(self._pl_raw_buffer)
        
        self.pmt_buff_shape = (self.n_stacks_to_buffer,
                      self.n_slices,
                      self.lines_per_frame,
                      self.pixels_per_line,
                      self.samples_per_pixel,
                      self._n_pmts)
        self.pmt_buff_axis_order=('buffer length',
                                'z slice',
                                'line',
                                'column',
                                'sample',
                                'pmt')

        self.plot_frame_index = BufferFrameIndex(maxval=self.n_stacks_to_buffer)
        # update to incorporate synchronized frame index
        self.pmt_buffer = PMTBuffer(self.pmt_buff_shape).create().buffer
        
    

    def stream_data(self):
        # get buffer address
        self._pl.SendScriptScriptCommands(f"-srd True {self.n_buffer_frames}")

        while self.remote_streaming_flag.is_set():
            self.update()

        self._pl.SendScriptCommands('-srd False')



        

    def update():
        pass
        # check queue
        # if prairie link command in queue
        #   send command
        # read raw data stream




    def terminate_data_streaming(self):

        self._pl.SendScriptCommands('-srd False')
        # read data stream until no bytes are returned

        # unlink shared memory object

        # destroy shared memory object

    
    def process_pl_commands(self):
        # if prairie link command queue length>0:
        # send prairie link commands
        raise NotImplementedError
        

    def read_data_stream(self):
        return self._pl.ReadRawDataStream_3(self.pid, self.buffer_address, self.buffer_size)

    def data_stream_to_pmt_buffer(self):
        last_index
        num_samples = self.read_data_stream()

        # each time a zstack is filled increment a shared counter 
        # that keeps track of where in the buffer we are

        number_of_new_frames, remaining_samples = divmod(last_index+num_samples,)

   




