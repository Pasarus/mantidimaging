from __future__ import (absolute_import, division, print_function)
import numpy as np


def execute(config):
    commands = config.func.imopr

    action = get_function(commands.pop())

    # the rest is a list of indices
    indices = [int(c) for c in commands]

    from helper import Helper
    h = Helper(config)
    config.helper = h
    h.check_config_integrity(config)

    from imgdata import loader
    sample, flat, dark = loader.load_data(config, h)

    # the [:] is necessary to get the actual data and not just the nxs header
    # sample = loader.nxsread(config.func.input_path)[:]
    h.tomo_print("Data shape {0}".format(sample.shape))
    flat, dark = None, None

    # from recon.runner import pre_processing
    # sample, flat, dark = pre_processing(config, sample, flat, dark)
    return action(sample, None, None, config, indices)


def get_function(string):
    if string == "recon":
        from imopr import recon
        return recon.execute
    if string == "sino":
        from imopr import sinogram
        return sinogram.execute
    if string == "show" or string == "vis":
        from imopr import visualiser
        return visualiser.execute
    if string == "cor":
        from imopr import cor
        return cor.execute
    if string == "corvo":
        from imopr import corvo
        return corvo.execute
    if string == "corpc":
        from imopr import corpc
        return corpc.execute
    if string == "corwrite":
        from imopr import corwrite
        return corwrite.execute
