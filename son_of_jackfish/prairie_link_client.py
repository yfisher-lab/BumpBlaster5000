import sys

import win32com.client
import serial
from multiprocessing import Process, Queue
import psutil
import time

TEENSY_COM = 'COM11'
PRAIRIE_VIEW_ACTIVE = False



def continuous_read_serial(q):
    with serial.Serial(TEENSY_COM) as srl:
        while PRAIRE_VIEW_ACTIVE:
            q.put(srl.readline().decode('UTF-8').rstrip())

def get_queue(q):
    pl = win32com.client.Dispatch("PrairieLink.Application")
    sucess = pl.Connect()
    if not success:
        sys.exit("failed to connect to Prairie Link")

    while PRAIRIE_VIEW_ACTIVE:
        try:
            cmd = q.get(block=False)
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
    while PRAIRIE_VIEW_ACTIVE:
        if is_prairie_view_open():
            PRAIRIE_VIEW_ACTIVE = True
            time.sleep(1)
        else:
            PRAIRIE_VIEW_ACTIVE = False




if __name__ == "__main__":

    if is_prairie_view_open():

        pl_queue = Queue()
        # keep everything going until prarie view closes
        prairie_view_monitor_process = Process(target = prairie_view_monitor)
        prairie_view_monitor_process.start()
        time.sleep(.1)

        # continuous listen
        read_serial_process = Process(target = continuous_read_serial, args = (pl_queue,))
        read_serial_process.start()


        # continous read queue
        get_queue_process = Process(target = get_queue, args = (pl_queue,))
        get_queue_process.start()

        prairie_view_monitor_process.join()
        read_serial_process.join()
        get_queue_process.join()
    else:
        sys.exit("Prairie View must be open to start client")








