import numpy as np
import random
from time import sleep

def build_cmd_str(queue):
    queue.put('0,4\n'.encode('UTF-8')) # go into open loop

    max_dac_val = 4096
    n_spots = 96 # one per pixel
    n_reps = 2
    n_indexes = 5 # 5 scenes, 4 square elevations and 1 dark

    headings = np.arange(0, 2*np.pi, 2*np.pi/n_spots)
    indexes = np.arange(0, max_dac_val+1, max_dac_val/n_indexes)

    cmd_len = 5*(n_spots+1)
    cmd = [cmd_len, 10]

    dark = indexes[-1]

    frame_dur = 100 # ms

    # cw/ccw spin followed by dark
    i = indexes[2]
    # for h in headings.tolist(): # ccw
    #     cmd.extend([h, i, 0, 0, frame_dur])

    # cmd.extend([0, dark, 0, 0, 4000]) # dark period

    for h in headings[::-1].tolist(): # cw
        cmd.extend([h, i, 0, 0, frame_dur])
    
    cmd.extend([0, dark, 0, 0, 4000]) # dark period between elevations

    cmd_str = ""
    for item in cmd:
        cmd_str = cmd_str + f"{item},"
    cmd_str = cmd_str[:-1] + "\n"

    queue.put(cmd_str.encode('UTF-8'))
    sleep((((n_spots*frame_dur) + 4000))/1000) # sec, this needs to be the approximate length of the open loop duration or else it moves on to the next queue immediately

    queue.put('0,5\n'.encode('UTF-8')) # go back into closed loop
    queue.put('1,7,0\n'.encode('UTF-8')) # set index back to 0

def run(queue):

    build_cmd_str(queue)

    return
