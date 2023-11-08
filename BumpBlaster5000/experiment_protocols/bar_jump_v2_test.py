# This is a test protocol for bar jumps. It is intended to go very quickly 
#     to verify that the code works without wasting 5 minutes.
# It takes 30 seconds to run: 6 sec cl, 2 sec bar jump, 2 sec bar jump, repeat


import numpy as np
from time import sleep

def build_cmd_str(queue):
    #These 2 variables can be edited to change bar jump time and closed loop time. Input only as integers.
    t_bj = 2 #time bar is held in place after jump, in seconds
    t_cl = 6 #time vr system is in closed loop between double jumps, in seconds

    t_ttl = 30 #total time is 5 mins for the entire protocol. this is to make data processing easier later
    
    num_trials = int(t_ttl / ((2*t_bj) + t_cl)) #number of trials (closed loop + 2 bar jumps); int() will round down to nearest integer
    t_end = t_ttl - (num_trials * ((2*t_bj)+t_cl)) #time in closed loop at the end of trials. Added if trials do not perfectly fit in 5 minute interval.
    #to make a list of dac bit values equivalent to 0', 90', 180', and 270':
    max_dac_val = 4096
    min_dac_val = 0
    n_spots = 4 
    headings = np.arange(min_dac_val, max_dac_val, max_dac_val/n_spots, dtype=int)
    # headings = [0,1023,2046,3070]

    for i in range(num_trials):
        
        #closed loop for t_cl seconds
        queue.put('0,5\n'.encode('UTF-8')) #closed loop
        sleep(t_cl)
        
        #Calculate bar jumps
        barjump_1 = headings[i%4] #this will vary first bar jump by 90' each iteration.
        barjump_2 = headings[(i%4)-1] #second bar jump will always be 90' from first.
        bj1_cmd = '1,6,' + str(barjump_1) + '\n'
        bj2_cmd = '1,6,' + str(barjump_2) + '\n'
        
        #Two bar jumps, each held for t_bj seconds
        queue.put('0,4\n'.encode('UTF-8')) #open loop  
        
        queue.put(bj1_cmd.encode('UTF-8')) #bar jump 
        sleep(t_bj)

        queue.put(bj2_cmd.encode('UTF-8')) #bar jump 
        sleep(t_bj)
    
    queue.put('0,5\n'.encode('UTF-8')) #closed loop
    sleep(t_end)
    queue.put('1,7,4095\n'.encode('UTF-8'))

    
def run(queue):

    build_cmd_str(queue)

    return