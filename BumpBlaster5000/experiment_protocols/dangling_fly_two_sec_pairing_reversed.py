import numpy as np
from time import sleep



def build_cmd_str(queue):

    queue.put('0,4\n'.encode('UTF-8'))

    max_dac_val = 4096
    


    unpaired_heading = int(max_dac_val/3 - 4096/24)
    paired_heading = int(max_dac_val/3*2 - 4096/24)
    
    
    # # flash each bar for 2 seconds 5 times interleaved with 5 seconds between
    for _ in range(5):
        cmd = [int(5*6), 10]
        # heading, index, opto_bool, opto_delay, combined_dur
        cmd.extend([paired_heading, 4095, 0, 0, 4900])
        cmd.extend([paired_heading, 0, 0, 0, 2000])
        cmd.extend([paired_heading, 4095, 0, 0, 100])
        cmd.extend([unpaired_heading, 4095, 0, 0, 4900])
        cmd.extend([unpaired_heading, 0, 0, 0, 2000])
        cmd.extend([unpaired_heading, 4095, 0, 0, 100])
        queue.put(cmd_to_str(cmd).encode('UTF-8'))
        sleep(14.1)

   
    for _ in range(3):
        cmd = [int(5*6), 10]
        # pair 1 bar with opto stim, while the other one just flashes
        cmd.extend([paired_heading, 4095, 0, 0, 4900])
        cmd.extend([paired_heading, 0, 1, 0, 2000])
        cmd.extend([paired_heading, 4095, 0, 0, 100])
        cmd.extend([unpaired_heading, 4095, 0, 0, 4900])
        cmd.extend([unpaired_heading, 0, 0, 0, 2000])
        cmd.extend([unpaired_heading, 4095, 0, 0, 100])
        queue.put(cmd_to_str(cmd).encode('UTF-8'))
        sleep(14.1)
    

    for _ in range(5):
        cmd = [int(5*6), 10]
        # heading, index, opto_bool, opto_delay, combined_dur
        cmd.extend([paired_heading, 4095, 0, 0, 4900])
        cmd.extend([paired_heading, 0, 0, 0, 2000])
        cmd.extend([paired_heading, 4095, 0, 0, 100])
        cmd.extend([unpaired_heading, 4095, 0, 0, 4900])
        cmd.extend([unpaired_heading, 0, 0, 0, 2000])
        cmd.extend([unpaired_heading, 4095, 0, 0, 100])
        queue.put(cmd_to_str(cmd).encode('UTF-8'))
        sleep(14.1)


  
    queue.put('0,5\n'.encode('UTF-8'))
    queue.put('1,7,4095\n'.encode('UTF-8'))

    
    return 
    
def cmd_to_str(cmd):
    cmd_str = ""
    for item in cmd:
        cmd_str = cmd_str + f"{item},"
    cmd_str = cmd_str[:-1] + "\n"
    return cmd_str
    
    
def run(queue):
  
  
    build_cmd_str(queue)

    return
    

