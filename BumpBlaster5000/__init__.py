import numpy as np
import multiprocessing as mp

from . import params
if params.hostname == 'BRVM5K3':
    from . import utils
else:
    from . import shared_memory, utils


if params.hostname == 'bard-smaug-slayer':
    pass
elif params.hostname == 'SMAUG':
    from . import prairie_link_client
else:
    from . import vr_interface
