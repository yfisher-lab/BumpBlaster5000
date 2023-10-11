# This experimental protocol will start in closed loop for 5 minutes. 
# Then, the bar will jump to a specific location and hold there for 2 seconds. 
# Then, jump again and hold for 2 seconds.
# Then, return to closed loop for 3 minutes.


import numpy as np
from time import sleep



def build_cmd_str(queue):

    #closed loop for 5 minutes
    queue.put('0,5\n'.encode('UTF-8'))
    sleep(60*5) 

    # 2 seqential bar jumps:
    new_bar1 = 0 # 0' to 360' is equivalent to 0V to 4095V. So, this is presumably 0'
    new_bar2 = int(4095 / 4) # and this is presumably 90'
    
    queue.put('0,4\n'.encode('UTF-8')) #open loop  
    queue.put('1,6,new_bar1\n'.encode('UTF-8')) #bar jump 
    sleep(2) #hold 2 seconds

    queue.put('0,4\n'.encode('UTF-8')) #open loop  
    queue.put('1,6,new_bar2\n'.encode('UTF-8')) #bar jump 
    sleep(2) #hold 2 seconds

    #return to closed loop for 3 minutes (ideally the bar wouldn't jump again when returning to closed loop)
    queue.put('0,5\n'.encode('UTF-8'))
    sleep(60*3)

    return






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



