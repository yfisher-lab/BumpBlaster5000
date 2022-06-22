import sys

import win32com.client
import serial
# from multiprocessing import Process, Queue
from queue import Queue
from threading import Thread
import psutil
import time





def continuous_read_serial(q, TEENSY_COM='COM11'):
    global PRAIRIE_VIEW_ACTIVE
    with serial.Serial(TEENSY_COM) as srl:
        while PRAIRIE_VIEW_ACTIVE:
            q.put(srl.readline().decode('UTF-8').rstrip())


def get_queue(q):
    global PRAIRIE_VIEW_ACTIVE
    global pl
    success = pl.Connect()
    if not success:
        sys.exit("failed to connect to Prairie Link")

    while PRAIRIE_VIEW_ACTIVE:
        try:
            cmd = q.get()
            print(cmd)
            _ = pl.SendScriptCommands(cmd)
        except Queue.Empty:
            pass

    pl.Disconnect()

def is_prairie_view_open():
    if "Prairie View.exe" in (i.name() for i in psutil.process_iter()):
        return True
    else:
        return False


def prairie_view_monitor():
    global PRAIRIE_VIEW_ACTIVE
    while PRAIRIE_VIEW_ACTIVE:
        if is_prairie_view_open():
            PRAIRIE_VIEW_ACTIVE = True
            time.sleep(1)
        else:
            PRAIRIE_VIEW_ACTIVE = False




if __name__ == "__main__":

    if is_prairie_view_open():

        global PRAIRIE_VIEW_ACTIVE
        global pl
        pl = win32com.client.Dispatch("PrairieLink.Application")
        PRAIRIE_VIEW_ACTIVE = is_prairie_view_open()
        pl_queue = Queue()
        # # keep everything going until prarie view closes
        prairie_view_monitor_process = Thread(target = prairie_view_monitor)
        prairie_view_monitor_process.start()
        time.sleep(.1)

        # continuous listen
        read_serial_process = Thread(target = continuous_read_serial, args = (pl_queue,))
        read_serial_process.start()


        # continous read queue
        get_queue_process = Thread(target = get_queue, args = (pl_queue,))
        get_queue_process.start()

        prairie_view_monitor_process.join()
        read_serial_process.join()
        get_queue_process.join()
    else:
        sys.exit("Prairie View must be open to start client")








