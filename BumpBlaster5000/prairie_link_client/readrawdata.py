import os
import multiprocessing as mp
import ctypes

import numpy as np

from sys import platform
if platform != 'linux':
    import win32com.client

# from time import sleep

NP_SHARED_NAME = 'pmt_buffer_array'



class PMTBuffer():
    #ToDo: change to not inherit but to instantiate two buffers 
    # (1 for buffer, 1 for index) and overload methods
    def __init__(self, shape, names=None, dtype=np.int16, axis_order=None,
                resonant = True):
        # super().__init__(shape, name, dtype, axis_order)

        if names is None:
            self.names = {'buffer':'pmt_buffer','frame_sync':'frame_sync'}
        
        
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

        self.samples_per_frame = np.prod(shape[2:])

        self.curr_flat_index = 0

        self._buffer_inst = None
        self._frame_sync_inst = None

    def create(self):



    def update_buffer(self, n_samples, flat_data):

        n_new_frames, new_flat_index = divmod(self.curr_flat_index+n_samples, 
                                            self.samples_per_frame)
        
        if n_new_frames == 0:
            sub_mat = self.buffer[self.buffer_index,self.z_index,:,:,:,:]
            fill_frame(self.curr_flat_index,new_flat_index, flat_data)
        else:
            flat_data_idx = 0
            for frame in range(n_new_frames):
                sub_mat = self.buffer[self.buffer_index,self.z_index,:,:,:,:]

                frame_size = self.samples_per_frame-self.curr_flat_index
                new_flat_data_idx = flat_data_idx + frame_size
                # fill frame
                tmp_data = flat_data[flat_data_idx:new_flat_data_idx]
                fill_frame(self.curr_flat_index,self.samples_per_frame, tmp_data)
                
                # set curr_flat index to 0
                flat_data_idx=new_flat_data_idx
                self.curr_flat_index=0

                #reverse odd lines to deal with resonant mirror
                sub_mat[:,:,:,:] = sub_mat[:,::-1,:,:]

                # update z_index
                new_buff_ind, self.z_index = divmod(self.z_index+1,self.max_z_index)

                # update 
                self.buffer_index = (self.buffer_index + new_buff_ind) % self.max_buffer
                

            fill_frame(self.curr_flat_index,new_flat_index, flat_data[flat_data_idx:])


        def fill_frame(start,stop,data_slice):
            lines, columns, samples, pmts = np.unravel_index(np.arange(start,stop))
            sub_mat[lines,columns,samples,pmts]=data_slice
    
    @property
    def latest_full_zstack(self):
        return 

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
        # read data stream until no bytes are returned

        # unlink shared memory object

        # destroy shared memory object



        

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

   




