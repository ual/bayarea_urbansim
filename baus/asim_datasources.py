import orca
import pandas as pd
import os
import asim_utils
import asim_simulate
import asim_misc
import skim as askim
import tracing
import openmatrix as omx


################################
# from asim.abm.tables.landuse #
################################

@orca.table()
def land_use(asim_store):

    df = asim_store["land_use/taz_data"]

    print("loaded land_use %s" % (df.shape,))

    # replace table function with dataframe
    orca.add_table('land_use', df)

    return df


###################################
# from asim.abm.tables.size_terms #
###################################

@orca.table()
def size_terms(configs_dir):
    f = os.path.join(configs_dir, 'destination_choice_size_terms.csv')
    return pd.read_csv(f, index_col='segment')


@orca.table()
def destination_size_terms(land_use, size_terms):
    land_use = land_use.to_frame()
    size_terms = size_terms.to_frame()
    df = pd.DataFrame({key: asim_utils.size_term(
        land_use, row) for key, row in size_terms.iterrows()},
        index=land_use.index)
    df.index.name = "TAZ"
    return df


##############################
# from asim.abm.tables.skims #
##############################

@orca.injectable(cache=True)
def omx_file(data_dir, asim_settings):
    print("opening omx file")

    fname = os.path.join(data_dir, asim_settings["skims_file"])
    file = omx.open_file(fname)
    asim_utils.close_on_exit(file, fname)

    return file


@orca.injectable(cache=True)
def skim_dict(omx_file, cache_skim_key_values):

    print("skims injectable loading skims")

    skim_dict = askim.SkimDict()
    skim_dict.offset_mapper.set_offset_int(-1)

    skims_in_omx = omx_file.listMatrices()
    for skim_name in skims_in_omx:
        key, sep, key2 = skim_name.partition('__')
        skim_data = omx_file[skim_name]
        if not sep:
            # no separator - this is a simple 2d skim - we load them all
            skim_dict.set(key, skim_data)
        else:
            # there may be more time periods in the skim than
            # are used by the model. cache_skim_key_values is a list of
            # time periods (frem settings) that are used
            # FIXME - assumes that the only types of key2 are time_periods
            if key2 in cache_skim_key_values:
                skim_dict.set((key, key2), skim_data)

    return skim_dict


###################################
# from asim.abm.tables.households #
###################################

@orca.table()
def asim_households(asim_store, households_sample_size, trace_hh_id):

    df_full = asim_store["households"]

    # if we are tracing hh exclusively
    if trace_hh_id and households_sample_size == 1:

        # df contains only trace_hh (or empty if not in full store)
        df = tracing.slice_ids(df_full, trace_hh_id)

    # if we need sample a subset of full store
    elif households_sample_size > 0 and \
            len(df_full.index) > households_sample_size:

        # take the requested random sample
        df = asim_simulate.random_rows(df_full, households_sample_size)

        # if tracing and we missed trace_hh in sample, but it is in full store
        if trace_hh_id and trace_hh_id not in df.index and \
                trace_hh_id in df_full.index:
            # replace first hh in sample with trace_hh
            print(
                "replacing household %s with %s in household sample" %
                (df.index[0], trace_hh_id))
            df_hh = tracing.slice_ids(df_full, trace_hh_id)
            df = pd.concat([df_hh, df[1:]])

    else:
        df = df_full

    print("loaded households %s" % (df.shape,))

    # replace table function with dataframe
    orca.add_table('asim_households', df)

    asim_utils.get_rn_generator().add_channel(df, 'asim_households')

    if trace_hh_id:
        tracing.register_traceable_table('asim_households', df)
        tracing.trace_df(df, "asim_households", warn_if_empty=True)

    return df


################################
# from asim.abm.tables.persons #
################################

# this assigns a chunk_id to each household so we can iterate
# over persons by whole households
@orca.column("asim_households", cache=True)
def chunk_id(asim_households):

    # FIXME - pathological knowledge of name of chunk_id column
    # used by hh_chunked_choosers

    chunk_ids = pd.Series(range(len(asim_households)), asim_households.index)
    return chunk_ids


@orca.table()
def asim_persons(asim_store, households_sample_size, asim_households,
                 trace_hh_id):

    df = asim_store["persons"]

    if households_sample_size > 0:
        # keep all persons in the sampled households
        df = df[df.household_id.isin(asim_households.index)]

    print("loaded asim asim_persons %s" % (df.shape,))

    # replace table function with dataframe
    orca.add_table('asim_persons', df)

    asim_utils.get_rn_generator().add_channel(df, 'asim_persons')

    if trace_hh_id:
        tracing.register_traceable_table('asim_persons', df)
        tracing.trace_df(df, "asim_persons", warn_if_empty=True)

    return df


# another common merge for persons
@orca.table()
def asim_persons_merged(asim_persons, asim_households, land_use,
                        accessibility):
    return orca.merge_tables(asim_persons.name, tables=[
        asim_persons, asim_households, land_use, accessibility])


# this is the placeholder for all the columns to update after the
# workplace location choice model
@orca.table()
def persons_workplace(asim_persons):
    return pd.DataFrame(index=asim_persons.index)


# this use the distance skims to compute the raw distance to work from home
@orca.column("persons_workplace")
def distance_to_work(asim_persons, skim_dict):
    distance_skim = skim_dict.get('DIST')
    return pd.Series(distance_skim.get(asim_persons.home_taz,
                                       asim_persons.workplace_taz),
                     index=asim_persons.index)


# this uses the free flow travel time in both directions
# MTC TM1 was MD and MD since term is free flow roundtrip_auto_time_to_work
@orca.column("persons_workplace")
def roundtrip_auto_time_to_work(asim_persons, skim_dict):
    sovmd_skim = skim_dict.get(('SOV_TIME', 'MD'))
    return pd.Series(sovmd_skim.get(asim_persons.home_taz,
                                    asim_persons.workplace_taz) +
                     sovmd_skim.get(asim_persons.workplace_taz,
                                    asim_persons.home_taz),
                     index=asim_persons.index)


@orca.column('persons_workplace')
def workplace_in_cbd(asim_persons, land_use, asim_settings):
    s = asim_utils.reindex(land_use.area_type, asim_persons.workplace_taz)
    return s < asim_settings['cbd_threshold']
