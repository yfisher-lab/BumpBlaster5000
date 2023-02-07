import numpy as np
from time import sleep
from datetime import datetime



def build_cmd_str(queue):

    queue.put('0,4\n'.encode('UTF-8'))

    max_dac_val = 4096
    n_spots = 96 # one per pixel
    n_reps = 5

    headings = np.arange(0, max_dac_val, max_dac_val/n_spots, dtype=int)
    # print(headings.shape)


    queue.put('1,7,4095\n'.encode('UTF-8'))
    sleep(5)
    for r in range(n_reps):
        for h in headings.tolist():
            cmd = '2, 8, ' + f"{h}" + ', 0\n' 
            queue.put(cmd.encode('UTF-8'))
            sleep(.2)
            # cmd.extend([h, 0, 1, 0, 1875])
    # cmd.extend([0,  4095,   0,  0, 5000])
    queue.put('1,7,4095\n'.encode('UTF-8'))
    sleep(5)

    # cmd_str = ""
    # for item in cmd:
    #     cmd_str = cmd_str + f"{item},"
    # cmd_str = cmd_str[:-1] + "\n"

    # queue.put(cmd_str.encode('UTF-8'))

    # sleep(26.1)
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
    


