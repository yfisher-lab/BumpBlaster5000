import threading
import numpy as np

def threaded(fn):
    '''
    make a function threaded
    to be used as a decorator for a function

    :param fn:
    :return: threaded function, that will now return a thread handle
    '''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

def cart2pol(x,y):
    '''
    cartesian to polar coordinates
    :param x:
    :param y:
    :return:
    '''
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y,x)
    return rho, phi

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
