import numpy as np
import random
from time import sleep

def build_cmd_str(queue):
    queue.put('0,4\n'.encode('UTF-8')) # go into open loop

    max_dac_val = 4096 # value for the last scene in pattern
    n_spots = 96 # one per pixel
    n_reps = 2
    n_indexes = 5 # 5 scenes, 4 square elevations and 1 dark

    headings = np.arange(0, 2*np.pi, 2*np.pi/n_spots)
    indexes = np.arange(0, max_dac_val+1, max_dac_val/n_indexes)

    dark = indexes[-1]

    n_pr_inputs = 5 # num inputs to PointRunner (heading, index, opto_bool, opto_delay, combined_dur)
    frame_dur = 50 # ms
    dark_dur = 4000 # ms

    # cw/ccw spin followed by dark 
    for _ in range(n_reps):
        shuffled_ind = random.sample(indexes[1:-1].tolist(), k=len(indexes[1:-1])) # change elevation order during each rep
        for i in shuffled_ind:
            # cw spin
            cmd_len = n_pr_inputs*(n_spots + 1)
            cmd = [cmd_len, 10]
            for h in headings[::-1].tolist(): 
                cmd.extend([h, i, 0, 0, frame_dur])       
            cmd.extend([0, dark, 0, 0, dark_dur]) # dark period
            queue.put(cmd_to_str(cmd).encode('UTF-8'))
            sleep(((n_spots*frame_dur)+dark_dur)/1000)

            # ccw spin
            cmd_len = n_pr_inputs*(n_spots + 1)
            cmd = [cmd_len, 10]
            for h in headings.tolist(): 
                cmd.extend([h, i, 0, 0, frame_dur])
            cmd.extend([0, dark, 0, 0, dark_dur]) # dark period
            queue.put(cmd_to_str(cmd).encode('UTF-8'))
            sleep(((n_spots*frame_dur)+dark_dur)/1000)

    queue.put('0,5\n'.encode('UTF-8')) # go back into closed loop
    queue.put('1,7,0\n'.encode('UTF-8')) # set index back to 0 (top square) for troubleshooting end of expt

def cmd_to_str(cmd):
    cmd_str = ""
    for item in cmd:
        cmd_str = cmd_str + f"{item},"
    cmd_str = cmd_str[:-1] + "\n"
    return cmd_str

def run(queue):
    build_cmd_str(queue)
    return
