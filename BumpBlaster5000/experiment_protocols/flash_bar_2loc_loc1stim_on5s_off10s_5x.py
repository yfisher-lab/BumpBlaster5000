import numpy as np
from time import sleep
from datetime import datetime
import random



def build_cmd_str(queue):

    queue.put('0,4\n'.encode('UTF-8'))

    max_dac_val = 1024
    loc1 = 1.96 # approx 45 degrees
    loc2 = 3.53 # approx -45 degrees
    locations = (loc1, loc2)
    n_locs = len(locations)

    n_reps = 5
    opto_reps = 5

    # print(headings.shape)


   
    for _ in range(n_reps):
        cmd_len = 5*n_locs*(opto_reps+1) # number of commands

        cmd = [cmd_len, 10]
        # set index to 1 to hide scene
        # heading, index, opto_bool, opto_delay, combined_dur
        # set each 
        
        for __ in range(opto_reps):
            cmd.extend([loc1, 0, 1, 0, 1000])

        cmd.extend([0, max_dac_val-1, 0, 0, 10000])

        for __ in range(opto_reps):
            cmd.extend([loc2, 0, 0, 0, 1000])

        cmd.extend([0, max_dac_val-1, 0, 0, 10000])

        
    


        cmd_str = ""
        for item in cmd:
            cmd_str = cmd_str + f"{item},"
        cmd_str = cmd_str[:-1] + "\n"

        queue.put(cmd_str.encode('UTF-8'))
        sleep(n_locs*(opto_reps+10))

    queue.put('0,5\n'.encode('UTF-8')) # closed loop but don't make bar visible
    return 
    
       
def run(queue):
    # go to open loop
    
    # send remapping commands
    # queue.put(build_cmd_str())

    # back to closed loop
    build_cmd_str(queue)

    return
    