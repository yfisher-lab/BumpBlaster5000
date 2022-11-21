from warnings import warn
import multiprocessing.shared_memory

from . import mp, np


class SharedPeriodicCounter:

    def __init__(self, initval=0, maxval = 100):
        """process-safe shared periodic counter

        Args:
            initval (int, optional): Initial value. Defaults to 0.
            maxval (int, optional): Max value. If counter exceeds this value, 
            counter wraps back to 0. Defaults to 100.
        """
        self.val = mp.Value('i', initval)
        self.maxval = maxval

    def increment(self):
        """process safe increment counter
        """
        with self.val.get_lock():
            self.val.value = (self.val.value+1) % self.maxval
    
    def decrement(self):
        """proce ss safe decrement counter. Also wraps to maxval if counter 
        goes negative
        """
        with self.val.get_lock():
            self.val.value -= 1
            if self.val.value < 0:
                self.val.value = self.maxval + 1 - self.val.value
    
    @property
    def value(self):
        """getter for value property

        Returns:
            _type_: value of counter
        """
        with self.val.get_lock():
            return self.val.value


class SharedArray:
    def __init__(self, shape: tuple, name='buffer', dtype=np.int16):
        
        """wrapper class for multiprocessing.shared_memory.SharedMemory.
        Implements a process-safe shared memory object of given shape, 
        data type and name. This class can be used by the creating process 
        as well as the connecting process

        Args:
            shape (tuple): shape of numpy array that will be created
            name (str, optional): name of memory object. Defaults to 'buffer'.
            dtype (_type_, optional): numpy datatype for array. Defaults to np.int16.
        """
        
        self.name = name
        self.shape = shape
        self.dtype = dtype
        self._size = np.dtype(dtype).itemsize * np.prod(np.array(shape))
        
        self._shm = None
        self.buff = None
        self._creator = False
        
    def __del__(self):
        self.close(suppress_warning=True)

    def create(self, inplace = False):
        """create shared memory object and initialize the buffer

        Args:
            inplace (bool, optional): Whether to return a reference to the object
            for cascading. Defaults to False which will return the ref.

        Returns:
            _type_: self reference for cascading
        """
        
        try:
            self._shm = mp.shared_memory.SharedMemory(create=True, size=self._size, name = self.name)
        except FileExistsError:
            raise Exception(f"Shared memory object name '{self.name}' already exists. \
                            Pick a different name")
        self._init_buffer()
        self.buff[:]=0
        self._creator = True
        if not inplace:
            return self

    def connect(self, inplace = False, read_only=True):
        """ connect to an existing shared memory object and connect array

        Args:
            inplace (bool, optional): Whether to return a reference to the object
            for cascading. Defaults to False which will return the ref.
            read_only (bool, optional): When connecting to existing object, make a 
            read_only pointer to buffer
        Returns:
            _type_: self reference for cascading
        """
        
        if not self._creator:
            try:
                self._shm = mp.shared_memory.SharedMemory(name = self.name)
            except FileNotFoundError:
                raise Exception(f"Shared memory object named '{self.name}' does not exist")
        else: 
            warn("This process is the creator. Re-initializing buff")
            return
        
        self._init_buffer()
        if read_only:
            self.buff.setflags(write=False)
        if not inplace:
            return self

    def _init_buffer(self):
        """connect an instance of a numpy array to the shared memory buffer
        """
        self.buff = np.ndarray(shape=self.shape, dtype=self.dtype, buffer=self._shm.buf)

    def close(self, suppress_warning = False):
        """gracefully disconnect form memory object 
        """
        
        if self._shm is None:
            if not suppress_warning:
                warn('Instance of memory object does not exist. Either never created ' + \
                    'or already closed')
            return
        
        self._shm.close()
        if self._creator:
            self._shm.unlink()
        self._shm = None
        self._creator = False
        self.buff = None


class PMTBuffer:

    def __init__(self, shape, names=None, dtype=np.int16,
                 resonant=True):

        self._creator = None
        self.frame_sync = None
        self.axis_order = ('buffer length',
                           'z slice',
                           'line',
                           'column',
                           'sample',
                           'pmt')

        if len(shape) != 6:
            raise Exception('Shape of PMT buffer must be of length 6 ' +
                            f"{self.axis_order}")
        self.shape = shape

        if names is None:
            self.names = {'buffer': 'pmt_buffer',
                          'frame_sync': 'frame_sync'}

        # check that buffer and frame_sync are in keys
        if not isinstance(names, dict):
            raise Exception("names must be a dict with keys 'buffer' and 'frame_sync' ")
        if not ('buffer' in self.names.keys() and 'frame_sync' in self.names.keys()):
            raise Exception("names must contain keys 'buffer' and 'frame_sync'")

        self.dtype = dtype
        self.resonant = resonant

        self.buffer_index = 0
        self.max_buffer = shape[0]

        self.z_index = 0
        self.max_z_index = shape[1]

        self.samples_per_frame = np.prod(shape[2:])

        self.curr_flat_index = 0

        # allocate attributes
        self._buffer_inst = None
        self.buff = None
        self._frame_sync_inst = None
        self.frame_sync = None

    def create(self):

        self._buffer_inst = SharedArray(self.shape,
                                        name=self.names['pmt_buffer'],
                                        dtype=self.dtype).create()
        self.buff = self._buffer_inst.buff

        self._frame_sync_inst = SharedArray((1,),
                                            name=self.names['current_frame'],
                                            dtype=int).create()
        self.frame_sync = self._frame_sync_inst.buff

        self._creator = True

    def connect(self):
        self._buffer_inst = SharedArray(self.shape,
                                        name=self.names['pmt_buffer'],
                                        dtype=self.dtype).connect()
        self.buff = self._buffer_inst.buff

        self._frame_sync_inst = SharedArray((1, ),
                                            name=self.names['current_frame'],
                                            dtype=int).connect()
        self.frame_sync = self._frame_sync_inst.buff

        self._creator = False

    def close(self, suppress_warning=False):
        self._buffer_inst.close(suppress_warning=suppress_warning)
        self._frame_sync_inst.close(suppress_warning=suppress_warning)

    def __del__(self):
        self.close(suppress_warning=True)

    def update_buffer(self, n_samples, flat_data):

        def fill_frame(start, stop, data_slice):
            lines, columns, samples, pmts = np.unravel_index(np.arange(start, stop))
            sub_mat[lines, columns, samples, pmts] = data_slice

        n_new_frames, new_flat_index = divmod(self.curr_flat_index + n_samples,
                                              self.samples_per_frame)
        if n_new_frames == 0:
            sub_mat = self.buff[self.buffer_index, self.z_index, :, :, :, :]
            fill_frame(self.curr_flat_index, new_flat_index, flat_data)
        else:
            flat_data_idx = 0
            for frame in range(n_new_frames):
                sub_mat = self.buff[self.buffer_index, self.z_index, :, :, :, :]

                frame_size = self.samples_per_frame - self.curr_flat_index
                new_flat_data_idx = flat_data_idx + frame_size
                # fill frame
                tmp_data = flat_data[flat_data_idx:new_flat_data_idx]
                fill_frame(self.curr_flat_index, self.samples_per_frame, tmp_data)

                # set curr_flat index to 0
                flat_data_idx = new_flat_data_idx
                self.curr_flat_index = 0

                # reverse odd lines to deal with resonant mirror
                sub_mat[:, :, :, :] = sub_mat[:, ::-1, :, :]

                # update z_index
                new_buff_ind, self.z_index = divmod(self.z_index + 1, self.max_z_index)

                # update
                self.buffer_index = (self.buffer_index + new_buff_ind) % self.max_buffer

            fill_frame(self.curr_flat_index, new_flat_index, flat_data[flat_data_idx:])



    @property
    def latest_full_zstack(self):
        return self.buff[self.buffer_index - 1, :, :, :, :, :]

    def latest_n_zstacks(self, n=8):
        return self.buff[range(self.buffer_index - 1 - n, self.buffer_index - 1), :, :, :, :, :]