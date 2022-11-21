import numpy as np
import multiprocessing as mp

from . import params, shared_memory, utils

if params.hostname == 'bard-smaug-slayer':
    pass
elif params.hostname == 'SMAUG':
    from . import prairie_link_client
else:
    from . import son_of_jackfish