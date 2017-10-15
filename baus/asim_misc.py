import os
import warnings
import numpy as np
import orca
import pandas as pd
import yaml
import asim_utils

warnings.filterwarnings('ignore', category=pd.io.pytables.PerformanceWarning)
pd.options.mode.chained_assignment = None


@orca.injectable(cache=True)
def store(data_dir, asim_settings):
    if 'store' not in asim_settings:
        print("store file name not specified in settings")
        raise RuntimeError("store file name not specified in settings")
    fname = os.path.join(data_dir, asim_settings["store"])
    if not os.path.exists(fname):
        print("store file not found: %s" % fname)
        raise RuntimeError("store file not found: %s" % fname)

    file = pd.HDFStore(fname, mode='r')
    asim_utils.close_on_exit(file, fname)

    return file


@orca.injectable(cache=True)
def cache_skim_key_values(asim_settings):
    return asim_settings['time_periods']['labels']


@orca.injectable(cache=True)
def households_sample_size(asim_settings):
    return asim_settings.get('households_sample_size', 0)


@orca.injectable(cache=True)
def chunk_size(asim_settings):
    return int(asim_settings.get('chunk_size', 0))


@orca.injectable(cache=True)
def check_for_variability(asim_settings):
    return bool(asim_settings.get('check_for_variability', False))


@orca.injectable(cache=True)
def trace_hh_id(asim_settings):

    id = asim_settings.get('trace_hh_id', None)

    if id and not isinstance(id, int):
        print(
            "setting trace_hh_id is wrong type, "
            "should be an int, but was %s" % type(id))
        id = None

    return id


@orca.injectable()
def trace_person_ids():
    # overridden by register_persons if trace_hh_id is defined
    return []


@orca.injectable()
def trace_tour_ids():
    # overridden by register_tours if trace_hh_id is defined
    return []


@orca.injectable(cache=True)
def hh_index_name(asim_settings):
    # overridden by register_households if trace_hh_id is defined
    return None


@orca.injectable(cache=True)
def persons_index_name(asim_settings):
    # overridden by register_persons if trace_hh_id is defined
    return None


@orca.injectable(cache=True)
def trace_od(asim_settings):

    od = asim_settings.get('trace_od', None)

    if od and not (isinstance(od, list) and len(od) == 2 and all(
            isinstance(x, int) for x in od)):
        print(
            "setting trace_od is wrong type,"
            " should be a list of length 2, but was %s" % od)
        od = None

    return od


@orca.injectable(cache=True)
def enable_trace_log(trace_hh_id, trace_od):
    return (trace_hh_id or trace_od)
