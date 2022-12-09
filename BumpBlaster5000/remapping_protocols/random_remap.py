import numpy as np
from time import sleep



def send_cmd_str(queue):

    max_dac_val = 4096
    n_spots = 8


    rng = np.random.default_rng()
    headings = np.arange(0, max_dac_val, max_dac_val/n_spots, dtype=int)
    headings = np.roll(headings,rng.integers(0,n_spots))


    cmd_len = 5*(n_spots+2)
    cmd = [cmd_len, 10]
    # set index to 1 to hide scene
    # heading, index, opto_bool, opto_delay, combined_dur
    cmd.extend([0,  4095,   0,  0, 5000])
    # set each 
    for h in headings.tolist():
        cmd.extend([h, 0, 1, 0, 2000])
    cmd.extend([0,  4095,   0,  0, 5000])


    cmd_str = ""
    for item in cmd:
        cmd_str = cmd_str + f"{item},"
    cmd_str = cmd_str[:-1] + "\n"
    
    queue.put(cmd_str)
    
    





