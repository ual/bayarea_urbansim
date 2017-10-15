import os
import yaml
import pandas as pd
import numpy as np
import random
import orca
from skim import SkimDictWrapper, SkimStackWrapper
import tracing
import asim_simulate

_OPEN_FILES = {}
_PRNG = random.Random()


#########################
# from asim.core.config #
#########################

def setting(key, default=None):
    settings = orca.get_injectable('asim_settings')
    return settings.get(key, default)


def read_model_settings(configs_dir, file_name):
    settings = None
    file_path = os.path.join(configs_dir, file_name)
    if os.path.isfile(file_path):
        with open(file_path) as f:
            settings = yaml.load(f)

    if settings is None:
        settings = {}

    return settings


def get_model_constants(model_settings):
    """
    Read constants from model settings file

    Returns
    -------
    constants : dict
        dictionary of constants to add to locals
        for use by expressions in model spec
    """
    return model_settings.get('CONSTANTS', {})


def get_logit_model_settings(model_settings):
    """
    Read nest spec (for nested logit) from model settings file

    Returns
    -------
    nests : dict
        dictionary specifying nesting structure and nesting coefficients

    constants : dict
        dictionary of constants to add to locals for use
        by expressions in model spec
    """
    nests = None

    if model_settings is not None:

        # default to MNL
        logit_type = model_settings.get('LOGIT_TYPE', 'MNL')

        if logit_type not in ['NL', 'MNL']:
            print("Unrecognized logit type '%s'" % logit_type)
            raise RuntimeError("Unrecognized logit type '%s'" % logit_type)

        if logit_type == 'NL':
            nests = model_settings.get('NESTS', None)
            if nests is None:
                print("No NEST found in model spec for NL model type")
                raise RuntimeError(
                    "No NEST found in model spec for NL model type")

    return nests


#######################
# from asim.core.util #
#######################

def reindex(series1, series2):
    """
    This reindexes the first series by the second series.  This is an extremely
    common operation that does not appear to  be in Pandas at this time.
    If anyone knows of an easier way to do this in Pandas, please inform the
    UrbanSim developers.

    The canonical example would be a parcel series which has an index which is
    parcel_ids and a value which you want to fetch, let's say it's land_area.
    Another dataset, let's say of buildings has a series which indicate the
    parcel_ids that the buildings are located on, but which does not have
    land_area.  If you pass parcels.land_area as the first series and
    buildings.parcel_id as the second series, this function returns a series
    which is indexed by buildings and has land_area as values and can be
    added to the buildings dataset.

    In short, this is a join on to a different table using a foreign key
    stored in the current table, but with only one attribute rather than
    for a full dataset.

    This is very similar to the pandas "loc" function or "reindex" function,
    but neither of those functions return the series indexed on the current
    table.  In both of those cases, the series would be indexed on the foreign
    table and would require a second step to change the index.

    Parameters
    ----------
    series1, series2 : pandas.Series

    Returns
    -------
    reindexed : pandas.Series

    """

    # turns out the merge is much faster than the .loc below
    df = pd.merge(series2.to_frame(name='left'),
                  series1.to_frame(name='right'),
                  left_on="left",
                  right_index=True,
                  how="left")
    return df.right


def quick_loc_series(loc_list, target_series):
    """
    faster replacement for target_series.loc[loc_list]

    pandas Series.loc[] indexing doesn't scale
    for large arrays (e.g. > 1,000,000 elements)

    Parameters
    ----------
    loc_list : list-like (numpy.ndarray, pandas.Int64Index, or pandas.Series)
    target_series : pandas.Series

    Returns
    -------
        pandas.Series
    """

    left_on = "left"

    if isinstance(loc_list, pd.Int64Index):
        left_df = pd.DataFrame({left_on: loc_list.values})
    elif isinstance(loc_list, pd.Series):
        left_df = loc_list.to_frame(name=left_on)
    elif isinstance(loc_list, np.ndarray):
        left_df = pd.DataFrame({left_on: loc_list})
    else:
        raise RuntimeError(
            "quick_loc_series loc_list of unexpected type %s" %
            type(loc_list))

    df = pd.merge(left_df,
                  target_series.to_frame(name='right'),
                  left_on=left_on,
                  right_index=True,
                  how="left")

    # regression test
    # assert list(df.right) == list(target_series.loc[loc_list])

    return df.right


##########################################
# from asim.abm.models.tables.size_terms #
##########################################

def size_term(land_use, destination_choice_coeffs):
    """
    This method takes the land use data and multiplies various columns of the
    land use data by coefficients from the spec table in order
    to yield a size term (a linear combination of land use variables).

    Parameters
    ----------
    land_use : DataFrame
        A dataframe of land use attributes - the column names should match
        the index of destination_choice_coeffs
    destination_choice_coeffs : Series
        A series of coefficients for the land use attributes - the index
        describes the link to the land use table, and the values are floating
        points numbers used to do the linear combination

    Returns
    -------
    values : Series
        The index will be the same as land use, and the values will the
        linear combination of the land use table columns specified by the
        coefficients series.
    """
    coeffs = destination_choice_coeffs

    # first check for missing column in the land_use table
    missing = coeffs[~coeffs.index.isin(land_use.columns)]

    if len(missing) > 0:
        print("%s  missing columns in land use" % len(missing.index))
        for v in missing.index.values:
            print("missing: %s" % v)

    return land_use[coeffs.index].dot(coeffs)


###########################
# from asim.core.pipeline #
###########################

def close_on_exit(file, name):
    assert name not in _OPEN_FILES
    _OPEN_FILES[name] = file


def get_rn_generator():
    """
    Return the singleton random number object

    Returns
    -------
    activitysim.random.Random
    """

    return _PRNG


def add_dependent_columns(base_dfname, new_dfname):
    tbl = orca.get_table(new_dfname)
    for col in tbl.columns:
        # logger.debug("Adding dependent column %s" % col)
        orca.add_column(base_dfname, col, tbl[col])


#####################################
# from asim.abm.models.util.logsums #
#####################################

def time_period_label(hour):
    time_periods = setting('time_periods')
    bin = np.digitize([hour % 24], time_periods['hours'])[0] - 1
    return time_periods['labels'][bin]


def mode_choice_logsums_spec(configs_dir, dest_type):
    DEST_TO_TOUR_TYPE = \
        {'university': 'university',
         'highschool': 'school',
         'gradeschool': 'school',
         'work': 'work'}

    tour_type = DEST_TO_TOUR_TYPE.get(dest_type)
    spec = asim_simulate.read_model_spec(
        configs_dir, 'logsums_spec_%s.csv' % tour_type)
    return spec


def compute_logsums(choosers, logsum_spec, logsum_settings,
                    skim_dict, skim_stack, alt_col_name,
                    chunk_size, trace_hh_id, trace_label):
    """

    Parameters
    ----------
    choosers
    logsum_spec
    logsum_settings
    skim_dict
    skim_stack
    alt_col_name
    chunk_size
    trace_hh_id
    trace_label

    Returns
    -------
    logsums: pandas series
        computed logsums with same index as choosers
    """

    trace_label = tracing.extend_trace_label(trace_label, 'compute_logsums')

    nest_spec = get_logit_model_settings(logsum_settings)
    constants = get_model_constants(logsum_settings)

    print("Running compute_logsums with %d choosers" % len(choosers.index))

    if trace_hh_id:
        tracing.trace_df(logsum_spec,
                         tracing.extend_trace_label(trace_label, 'spec'),
                         slicer='NONE', transpose=False)

    # setup skim keys
    odt_skim_stack_wrapper = skim_stack.wrap(
        left_key='TAZ', right_key=alt_col_name, skim_key="out_period")
    dot_skim_stack_wrapper = skim_stack.wrap(
        left_key=alt_col_name, right_key='TAZ', skim_key="in_period")
    od_skim_stack_wrapper = skim_dict.wrap('TAZ', alt_col_name)

    skims = [
        odt_skim_stack_wrapper, dot_skim_stack_wrapper, od_skim_stack_wrapper]

    locals_d = {
        "odt_skims": odt_skim_stack_wrapper,
        "dot_skims": dot_skim_stack_wrapper,
        "od_skims": od_skim_stack_wrapper
    }
    if constants is not None:
        locals_d.update(constants)

    logsums = asim_simulate.simple_simulate_logsums(
        choosers,
        logsum_spec,
        nest_spec,
        skims=skims,
        locals_d=locals_d,
        chunk_size=chunk_size,
        trace_label=trace_label)

    return logsums
