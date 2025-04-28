# This experimental protocol will start in closed loop for 5 minutes. 
# Then, the bar will jump to a specific location and hold there for 2 seconds. 
# Then, jump again and hold for 2 seconds.
# Then, return to closed loop for 3 minutes.


import numpy as np
from time import sleep

def build_cmd_str(queue):
    #These 2 variables can be edited to change bar jump time and closed loop time. Input only as integers.
    t_bj = 2 #time bar is held in place after jump, in seconds
    t_cl = 56 #time vr system is in closed loop between double jumps, in seconds

    t_ttl = 60*5 #total time is 5 mins for the entire protocol. this is to make data processing easier later
    
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
    
    if t_end > 0: #remainder of 5 minutes(if any) will be spent in closed loop
        queue.put('0,5\n'.encode('UTF-8')) #closed loop
        sleep(t_end)

def run(queue):

    build_cmd_str(queue)

    return
    

#This is old code that I might implement later.
    # Determining where the bar will jump to:
    #Could jump 90' from original spot or could jump to a set location. 
    #OPTION 1: 90' jump. Whether it is +90' or -90' will depend on where the bar is at the moment of the jump (to avoid the area where there is no LEDs)
    
    #actual_dac_value = self.pl_serial = serial.Serial(self._params['pl_com']) #possibly this? not sure what form this value would be in. Got this from vr_interface.main, line 141

    #if actual_dac_value > max_dac_val/2:
        #new_bar_Opt1 = actual_dac_value - (max_dac_val/(4*n_spots)) #roughly -90'
    #else:
        #new_bar_Opt1 = actual_dac_value + (max_dac_val/(4*n_spots)) #roughly +90'
    #Option 2: Bar jumps to a set location. Interpretation of these results should include how big the jump was from the original location in closed loop.
    #new_bar_O2 = max_dac_val/(2*n_spots)

    # #closed loop for 5 minutes
    # queue.put('0,5\n'.encode('UTF-8'))
    # sleep(60*5) 

    # # 2 seqential bar jumps:
    # new_bar1 = 0 # 0' to 360' is equivalent to 0V to 4095V. So, this is presumably 0'
    # new_bar2 = int(4095 / 4) # and this is presumably 90'
    
    # queue.put('0,4\n'.encode('UTF-8')) #open loop  
    # queue.put('1,6,new_bar1\n'.encode('UTF-8')) #bar jump 
    # sleep(2) #hold 2 seconds

    # queue.put('0,4\n'.encode('UTF-8')) #open loop  
    # queue.put('1,6,new_bar2\n'.encode('UTF-8')) #bar jump 
    # sleep(2) #hold 2 seconds

    # #return to closed loop for 3 minutes (ideally the bar wouldn't jump again when returning to closed loop)
    # queue.put('0,5\n'.encode('UTF-8'))
    # sleep(60*3)

    # return



