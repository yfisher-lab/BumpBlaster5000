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