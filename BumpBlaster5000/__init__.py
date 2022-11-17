import numpy as np
import multiprocessing as mp

from . import params, shared_memory, utils

if params.hostname == 'bard-smaug-slayer':
    pass
else:
    from . import prairie_link_client, son_of_jackfish