FT_PC_PARAMS = {
    'teensy_input_com': 'COM11',
    'teensy_output_com': 'COM12',
    'pl_com': 'COM13',
    'baudrate': 115200,  
}

PL_PC_PARAMS = {
    'wedge_resolution': 16,
    'teensy_com': 'COM11',
    'vr_com': 'COM12',
    'baudrate': 115200,
    'baseline_time': 60,  # buffer size for baseline in df/f in seconds
    'func_time': .1,  # buffer size for df/f numerator in seconds (some unit is off here I think)
    'bump_signal_time': 10  # bump plot buffer size in seconds
}

import socket
hostname = socket.gethostname()
