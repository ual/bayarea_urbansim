import os
import yaml
import orca
import asim_utils
import asim_datasources
import tracing
from interaction_sample import interaction_sample
from urbansim.utils import misc
import pandas as pd


DUMP = False

############################################################
#                                                          #
# (1) ACTIVITYSIM ORCA STEPS FOR DATA MODEL INITIALIZATION #
#                                                          #
############################################################


@orca.injectable('asim_settings', cache=True)
def asim_settings():
    """
    This step loads the ActivitySim settings, which are kept
    separate for clarity. Ultimately we might want to merge
    them with ual_settings or just the main settings config

    Data expectations
    -----------------
    -   'configs' folder contains a file called 'ual_settings.yaml'
    -   'os.path' is expected to provide the root level of the urbansim
        instance, so be sure to either (a) launch the python process
        from that directory, or (b) use os.chdir to
        switch to that directory before running any model steps
    """
    with open(os.path.join(misc.configs_dir(), 'asim_settings.yaml')) as f:
        return yaml.load(f)


@orca.injectable()
def workplace_location_sample_spec(configs_dir):
    return asim_utils.read_model_spec(
        configs_dir, 'workplace_location_sample.csv')


@orca.injectable()
def workplace_location_settings(configs_dir):
    return asim_utils.read_model_settings(
        configs_dir, 'workplace_location.yaml')


@orca.injectable()
def workplace_location_spec(configs_dir):
    return asim_utils.read_model_spec(
        configs_dir, 'workplace_location.csv')


############################################################
#                                                          #
# (2) ACTIVITYSIM ORCA STEPS FOR SIMULATION LOGIC          #
#                                                          #
############################################################


@orca.step()
def workplace_location_sample(asim_persons_merged,
                              workplace_location_sample_spec,
                              workplace_location_settings,
                              skim_dict,
                              destination_size_terms,
                              chunk_size,
                              trace_hh_id):
    """
    build a table of workers * all zones in order
    to select a sample of alternative work locations.

    PERID,  dest_TAZ, rand,            pick_count
    23750,  14,       0.565502716034,  4
    23750,  16,       0.711135838871,  6
    ...
    23751,  12,       0.408038878552,  1
    23751,  14,       0.972732479292,  2
    """

    trace_label = 'workplace_location_sample'

    choosers = asim_persons_merged.to_frame()
    alternatives = destination_size_terms.to_frame()

    constants = asim_utils.get_model_constants(workplace_location_settings)

    sample_size = workplace_location_settings["SAMPLE_SIZE"]
    alt_col_name = workplace_location_settings["ALT_COL_NAME"]

    print("Running workplace_location_sample with %d persons" % len(choosers))

    # create wrapper with keys for this lookup - in this case there is a TAZ
    # in the choosers and a TAZ in the alternatives which get merged during
    # interaction the skims will be available under the name "skims" for any
    # @ expressions
    skims = skim_dict.wrap("TAZ", "TAZ_r")

    locals_d = {
        'skims': skims
    }
    if constants is not None:
        locals_d.update(constants)

    # FIXME - MEMORY HACK - only include columns actually used in spec
    chooser_columns = workplace_location_settings['SIMULATE_CHOOSER_COLUMNS']
    choosers = choosers[chooser_columns]

    choices = interaction_sample(
        choosers,
        alternatives,
        sample_size=sample_size,
        alt_col_name=alt_col_name,
        spec=workplace_location_sample_spec,
        skims=skims,
        locals_d=locals_d,
        chunk_size=chunk_size,
        trace_label=trace_label)

    orca.add_table('workplace_location_sample', choices)


@orca.step()
def workplace_location_logsums(asim_persons_merged,
                               land_use,
                               skim_dict, skim_stack,
                               workplace_location_sample,
                               configs_dir,
                               chunk_size,
                               trace_hh_id):
    """
    add logsum column to existing workplace_location_sample able

    logsum is calculated by running the mode_choice model for each
    sample (person, dest_taz) pair in workplace_location_sample,
    and computing the logsum of all the utilities

                                                   <added>
    PERID,  dest_TAZ, rand,            pick_count, logsum
    23750,  14,       0.565502716034,  4           1.85659498857
    23750,  16,       0.711135838871,  6           1.92315598631
    ...
    23751,  12,       0.408038878552,  1           2.40612135416
    23751,  14,       0.972732479292,  2           1.44009018355

    """

    trace_label = 'workplace_location_logsums'

    logsums_spec = asim_utils.mode_choice_logsums_spec(configs_dir, 'work')

    workplace_location_settings = asim_utils.read_model_settings(
        configs_dir, 'workplace_location.yaml')

    alt_col_name = workplace_location_settings["ALT_COL_NAME"]

    # FIXME - just using settings from tour_mode_choice
    logsum_settings = asim_utils.read_model_settings(
        configs_dir, 'tour_mode_choice.yaml')

    asim_persons_merged = asim_persons_merged.to_frame()
    workplace_location_sample = workplace_location_sample.to_frame()

    print("Running workplace_location_sample with %s rows" % len(
        workplace_location_sample))

    # FIXME - MEMORY HACK - only include columns actually used in spec
    chooser_columns = workplace_location_settings['LOGSUM_CHOOSER_COLUMNS']
    asim_persons_merged = asim_persons_merged[chooser_columns]

    choosers = pd.merge(workplace_location_sample,
                        asim_persons_merged,
                        left_index=True,
                        right_index=True,
                        how="left")

    choosers['in_period'] = asim_utils.time_period_label(
        workplace_location_settings['IN_PERIOD'])
    choosers['out_period'] = asim_utils.time_period_label(
        workplace_location_settings['OUT_PERIOD'])

    # FIXME - should do this in expression file?
    choosers['dest_topology'] = asim_utils.reindex(
        land_use.TOPOLOGY, choosers[alt_col_name])
    choosers['dest_density_index'] = asim_utils.reindex(
        land_use.density_index, choosers[alt_col_name])

    tracing.dump_df(
        DUMP, asim_persons_merged, trace_label, 'asim_persons_merged')
    tracing.dump_df(
        DUMP, choosers, trace_label, 'choosers')

    logsums = asim_utils.compute_logsums(
        choosers, logsums_spec, logsum_settings, skim_dict, skim_stack,
        alt_col_name, chunk_size, trace_hh_id, trace_label)

    # "add_column series should have an index matching the table to which
    # it is being added" when the index has duplicates, however, in the
    # special case that the series index exactly matches the table index,
    # then the series value order is preserved logsums now does, since
    # workplace_location_sample was on left side of merge de-dup merge
    orca.add_column("workplace_location_sample", "mode_choice_logsum", logsums)
