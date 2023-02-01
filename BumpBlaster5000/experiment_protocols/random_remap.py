import numpy as np
from time import sleep
from datetime import datetime



def build_cmd_str(queue):

    queue.put('0,4\n'.encode('UTF-8'))

    max_dac_val = 4096
    n_spots = 8


    rng = np.random.default_rng(int(datetime.now().timestamp()))
    headings = np.arange(0, max_dac_val, max_dac_val/n_spots, dtype=int)
    print(headings.shape)
    headings = np.roll(headings,rng.integers(0,n_spots))


    cmd_len = 5*(n_spots+2)
    cmd = [cmd_len, 10]
    # set index to 1 to hide scene
    # heading, index, opto_bool, opto_delay, combined_dur
    cmd.extend([0,  4095,   0,  0, 10000])
    # set each 
    for h in headings.tolist():
        cmd.extend([h, 0, 1, 0, 2000])
    cmd.extend([0,  4095,   0,  0, 10000])


    cmd_str = ""
    for item in cmd:
        cmd_str = cmd_str + f"{item},"
    cmd_str = cmd_str[:-1] + "\n"

    queue.put(cmd_str.encode('UTF-8'))

    sleep(36)
    queue.put('0,5\n'.encode('UTF-8'))
    queue.put('1,7,0\n'.encode('UTF-8'))

    # multiline_cmd = '0, 4 \n' + cmd_str + '0, 5 \n'
    return # multiline_cmd.encode('UTF-8')
    
    
def run(queue):
    # go to open loop
    
    # send remapping commands
    # queue.put(build_cmd_str())

    # back to closed loop
    build_cmd_str(queue)

    return
    





