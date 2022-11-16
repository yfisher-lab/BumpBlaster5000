import os
from sys import platform
if platform != 'linux':
    import win32com.client
import numpy as np
# from time import sleep
from ctypes import c_int, addressof, pointer



class PrairieLinkDataPlotter:

    def __init__(self, command_queue, ) -> None:
        pass