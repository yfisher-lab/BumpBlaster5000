import time
import PyCapture2 as pycap
import numpy as np

from utils import threaded


class Flea3Cam:
    def __init__(self, serial_number = 13192198):

        self._bus = pycap.BusManager()
        self._uid = self._bus.getCameraFromSerialNumber(serial_number)
        self.cam = pycap.Camera()
        self.n_rows = None
        self.n_cols = None

    def connect(self):
        self.cam.connect(self._uid)


    def disconnect(self):
        self.cam.disconnect()

    def start(self):
        self.cam.startCapture()
        # get first frame
        time.sleep(.1)
        tmp_img = self.cam.retrieveBuffer()
        self.n_rows = tmp_img.getRows()
        self.n_cols = tmp_img.getCols()


    def stop(self):
        self.cam.stopCapture()


    def get_frame(self):
        img = self.cam.retrieveBuffer()
        return np.array(img.getData(), dtype='uint8').reshape((self.n_rows, self.n_cols)).T







