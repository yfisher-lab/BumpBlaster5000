import threading
import numpy as np
from numba import njit

def threaded(fn):
    '''
    make a function threaded
    to be used as a decorator for a function

    :param fn: function to be threaded, function should be thread safe (i.e no returns)
    :return: handle for thread, must call thread.join() when thread needs to be ended
    '''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

@njit
def cart2pol(x, y):
    '''
    cartesian to polar coordinates
    :param x:
    :param y:
    :return: rho: length of vector
             phi: angle of vector
    '''
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y,x)
    return rho, phi

@njit
def pol2cart(rho, phi):
    '''
    polar to cartesian coordinates

    :param rho: vector length
    :param phi: angle
    :return:
    '''
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y
