import numpy as np
from time import sleep

def build_cmd_str(queue):

    queue.put('0,4\n'.encode('UTF-8'))

    max_dac_val = 1024
    n_spots = 8
    n_rep = 5

    headings = np.arange(0, 2*np.pi, 2*np.pi/n_spots)
    headings = headings[[4,5,6,7,0,1,2,3]]

    def send_points(points, duration):
        cmd = [5*len(points), 10]
        for point in points:
            cmd.extend(point)
        queue.put(cmd_to_str(cmd).encode('UTF-8'))
        sleep(duration)

    # Send short independent commands so each packet is parsed before timeout.
    send_points([[0, max_dac_val-1, 0, 0, 5000]], 5.1)
    for _ in range(n_rep):
        for h in headings.tolist():
            send_points([
                [h, 0, 1, 0, 400],
                [h, max_dac_val-1, 0, 0, 800],
                [h, 0, 0, 0, 400],
                [h, max_dac_val-1, 0, 0, 800],
            ], 2.5)

    send_points([[0, max_dac_val-1, 0, 0, 5000]], 5.1)

    queue.put('0,5\n'.encode('UTF-8'))
    queue.put('1,7,0\n'.encode('UTF-8'))

    return
    

def cmd_to_str(cmd):
    return ",".join(str(item) for item in cmd) + "\n"

def run(queue):
    # go to open loop
    
    # send remapping commands
    # queue.put(build_cmd_str())

    # back to closed loop
    build_cmd_str(queue)

    return
    



