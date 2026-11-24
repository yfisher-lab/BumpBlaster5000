import numpy as np
from time import sleep

def build_cmd_str(queue):

    queue.put('0,4\n'.encode('UTF-8'))

    max_dac_val = 1024
    n_spots = 8
    n_rep = 5
    n_strobes = 5

    headings = np.arange(0, 2*np.pi, 2*np.pi/n_spots)

    def send_points(points, duration):
        cmd = [5*len(points), 10]
        for point in points:
            cmd.extend(point)
        queue.put(cmd_to_str(cmd).encode('UTF-8'))
        sleep(duration)

    def strobe_points(h, n_strobes, strobe_ms=150, off_ms=300):
        # Each strobe is a low point followed by a high point, all the same duration.
        # Only the very first point carries the 1 at index 2.
        points = []
        for i in range(n_strobes):
            flag = 1 if i == 0 else 0
            points.append([h, 0, flag, 0, strobe_ms])
            points.append([h, max_dac_val-1, 0, 0, off_ms])
        return points

    # Send short independent commands so each packet is parsed before timeout.
    send_points([[0, max_dac_val-1, 0, 0, 5000]], 5.1)
    for _ in range(n_rep):
        for h in headings.tolist():
            send_points(strobe_points(h, n_strobes), 2.5)

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
    



