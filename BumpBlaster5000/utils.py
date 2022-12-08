import threading
import multiprocessing as mp

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

def multiprocessed(fn):
    '''

    :param fn:
    :return:
    '''
    def wrapper(*args, **kwargs):
        process = mp.Process(target=fn, args=args, kwargs=kwargs)
        process.start()
        return process
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


@njit
def get_bin_edges(a, bins):
    bin_edges = np.zeros((bins+1,), dtype=np.float64)
    a_min = a.min()
    a_max = a.max()
    delta = (a_max - a_min) / bins
    for i in range(bin_edges.shape[0]):
        bin_edges[i] = a_min + i * delta

    bin_edges[-1] = a_max  # Avoid roundoff error on last point
    return bin_edges


@njit
def compute_bin(x, bin_edges):
    # assuming uniform bins for now
    n = bin_edges.shape[0] - 1
    a_min = bin_edges[0]
    a_max = bin_edges[-1]

    # special case to mirror NumPy behavior for last bin
    if x == a_max:
        return n - 1 # a_max always in last bin

    bin = int(n * (x - a_min) / (a_max - a_min))

    if bin < 0 or bin >= n:
        return None
    else:
        return bin


@njit
def numba_wrapped_histogram(a, bins, bin_edges=None):
    hist = np.zeros((bins+1,), dtype=np.float64)
    if bin_edges is None:
        bin_edges = get_bin_edges(a, bins)

    for x in a.flat:
        bin = compute_bin(x, bin_edges)
        if bin is not None:
            hist[int(bin)] += 1
    hist[-1]=hist[0]
    hist /= hist[:-1].sum()

    return hist, bin_edges
