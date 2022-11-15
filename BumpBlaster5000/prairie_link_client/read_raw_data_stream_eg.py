import os
import win32com.client
import numpy as np
# from time import sleep
from ctypes import c_int, addressof, pointer


if __name__ == "__main__":
    n_pmts = 2  # number of pmts
    n_buffer_frames = 100 # number of frames to put in buffer

    pid = os.getpid()
    pl = win32com.client.Dispatch("PrairieLink64.Application")
    pl.Connect('127.0.0.1')
    print(pl.Connected())

    samples = pl.LinesPerFrame() * pl.PixelsPerLine() * pl.SamplesPerPixel() * n_pmts
    print(samples)
    buffer_size = int(samples * n_buffer_frames)
    BUFFER = c_int * buffer_size # np.zeros([buffer_size, ])
    buffer = BUFFER(*[0 for i in range(buffer_size)])
    buffer_address = addressof(buffer)
    print("buffer initialized")
    pl.SendScriptCommands(f"-srd True {n_buffer_frames}")

    print("entering reading loop")
    while True:
        _int = pl.ReadRawDataStream_3(pid, buffer_address, buffer_size)
        if (_int > 0):
            print(_int, _int - buffer_size)
            cpy = np.ctypeslib.as_array(buffer)

