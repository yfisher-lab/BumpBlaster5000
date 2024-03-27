import numpy as np
from time import sleep



def build_cmd_str(queue):

    n_baseline=10
    n_pair = 5
    n_post = 10



    for r in range(n_baseline):
        queue.put('0,3\n'.encode('UTF-8'))
        sleep(10)
   

    for r in range(n_pair):
        queue.put('5,13,0,0,1,0,2500\n'.encode('UTF-8'))
        sleep(10)

    for r in range(n_post):
        queue.put('0,3\n'.encode('UTF-8'))
        sleep(10)



    
    return # multiline_cmd.encode('UTF-8')
    
    
def run(queue):
   
    build_cmd_str(queue)

    return
    





