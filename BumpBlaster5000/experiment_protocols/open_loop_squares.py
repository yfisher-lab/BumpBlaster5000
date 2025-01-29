import numpy as np
import random
from time import sleep
from datetime import datetime

def build_cmd_str(queue):
    queue.put('0,4\n'.encode('UTF-8')) # go into open loop
    
    max_dac_val = 4096
    n_spots = 96 # one per pixel
    n_reps = 2
    n_indexes = 5 # 5 scenes, 4 square elevations and 1 dark

    # create heading and index arrays
    headings = np.arange(0, 2*np.pi, 2*np.pi/n_spots)
    indexes = np.arange(0, 5000, 5000/n_indexes)

    # initialize command string with expected length using point setter case
    cmd_len = 5*(2*((n_spots*n_reps*(n_indexes-1))+(n_reps*(n_indexes-1)))) # 5 inputs to point setter case + total reps of frame/index combos
    cmd = [cmd_len, 10]

    # set last index as dark scene
    dark = indexes[-1]

    # duration of each frame in heading (approx 1.1 deg / duration)
    frame_dur = 50 # ms
    # shuffled_ind = random.sample(indexes[0:-1].tolist(), k=len(indexes[0:-1]))

    # alternate cw and ccw in open loop at randomly ordered elevations
    # heading, index, opto_bool, opto_delay, combined_dur
    for r in range(n_reps):    
        shuffled_ind = random.sample(indexes[0:-1].tolist(), k=len(indexes[0:-1])) # change elevation order during each rep
        for i in shuffled_ind:    
            for h in headings.tolist():
                cmd.extend([h, i, 0, 0, frame_dur])
            
            cmd.extend([0, dark, 0, 0, 4000]) # dark period between cw/ccw
            
            for h in headings[::-1].tolist():
                cmd.extend([h, i, 0, 0, frame_dur])
    
            cmd.extend([0, dark, 0, 0, 4000]) # dark period between elevations

    # convert command string format
    cmd_str = ""
    for item in cmd:
        cmd_str = cmd_str + f"{item},"
    cmd_str = cmd_str[:-1] + "\n"

    # send command to queue and wait some time
    queue.put(cmd_str.encode('UTF-8'))
    sleep(2*((n_spots*n_reps*(n_indexes-1))+(n_reps*(n_indexes-1))))

    return

def run(queue):
    build_cmd_str(queue)

    return

