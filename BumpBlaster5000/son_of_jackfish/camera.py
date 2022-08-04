import time
import PyCapture2 as pycap
import numpy as np

from BumpBlaster5000 import params

class Flea3Cam:
    '''
    Simplifies flycap API for use with Flea3 FLIR camera
    '''
    def __init__(self):

        # open BUS and get camera
        self._bus = pycap.BusManager()
        self._uid = self._bus.getCameraFromSerialNumber(params.PL_PC_PARAMS['flea3_serial'])
        self.cam = pycap.Camera()
        self.n_rows = None
        self.n_cols = None

    def connect(self):
        '''
        alias for flycap method
        :return:
        '''
        self.cam.connect(self._uid)


    def disconnect(self):
        '''
        alias for flycap method
        :return:
        '''
        self.cam.disconnect()

    def start(self):
        '''
        begin collecting frames
        :return:
        '''
        self.cam.startCapture()
        # get dummy first frame
        time.sleep(1/60.)
        tmp_img = self.cam.retrieveBuffer()
        # get size of image
        self.n_rows = tmp_img.getRows()
        self.n_cols = tmp_img.getCols()


    def stop(self):
        '''
        stop collecting frames
        :return:
        '''
        self.cam.stopCapture()


    def get_frame(self):
        '''
        Get a single frame and return it as a numpy array. Must call start() method before this method.
        :return:
        '''
        img = self.cam.retrieveBuffer()
        return np.array(img.getData(), dtype='uint8').reshape((self.n_rows, self.n_cols)).T







