import numpy as np
from time import sleep



def build_cmd_str(queue):

    queue.put('0,4\n'.encode('UTF-8'))

    max_dac_val = 4096
    


    paired_heading = int(max_dac_val/3)
    unpaired_heading = int(max_dac_val/3*2)
    
    
    cmd_len = 2*4*5 + 4
    cmd = [cmd_len, 10]
    
    # flash each bar for 2 seconds 5 times interleaved with 5 seconds between
    for _ in range(5):
        # heading, index, opto_bool, opto_delay, combined_dur
        cmd.extend([0, 4095, 0, 0, 5000])
        cmd.extend([paired_heading, 0, 0, 0, 2000])
        cmd.extend([0, 4095, 0, 0, 5000])
        cmd.extend([unpaired_heading, 0, 0, 0, 2000])
      
    
    # pair 1 bar with opto stim, while the other one just flashes
    cmd.extend([0, 4095, 0, 0, 5000])
    cmd.extend([paired_heading, 0, 1, 0, 2000])
    cmd.extend([0, 4095, 0, 0, 5000])
    cmd.extend([unpaired_heading, 0, 0, 0, 2000])
    
    # flash each bar again for 2 seconds 5 times interleaved
    for _ in range(5):
        cmd.extend([0, 4095, 0, 0, 5000])
        cmd.extend([paired_heading, 0, 0, 0, 2000])
        cmd.extend([0, 4095, 0, 0, 5000])
        cmd.extend([unpaired_heading, 0, 0, 0, 2000])

    queue.put(cmd.encode('UTF-8'))

    
    return 
    
    
def run(queue):
  
  
    build_cmd_str(queue)

    return
    

