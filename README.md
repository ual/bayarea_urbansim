Fall 2017 Work
=======

Notes:

- need own mode_choice config for workplace location choice
- instead of asim logger, baus just redirects stdout to logfile and issues print commands
- Most Asim functions placed into `asim_*`-prefixed .py files in the baus directory
    - see below
- Most Asim configs placed into the configs directory w/o renaming
    - see below for list of config files
- skims are loaded from omx objects, we prob want to change this
- some “placeholder” columns were note included for persons/hh’s tables b/c they reference models that we’re not yet running

Lingering questions:

- If module c contains orca injectables, and I import module c inside module b, do those injectables get registered when I load module b in module a?
    - currently loading asim_misc in asim_datasources which gets loaded in asim_models

TO DO:

- [x] clean up interaction_sample.py in baus

- [x] clean up logit.py in baus

- [x] clean up asim_simulate.py in baus

- [x] port over workplace_location_logsums

- [x] clean up interaction_sample_simulate.py in baus

- [x] port over workplace_location_simulate

- [ ] try to run workplace_location_choice as a model step in urbansim

- [ ] workplace location choice needs its own mode_choice config

- [ ] replace datasources with “Full Example” datasources from MTC Box

- [ ] diff the datasources (persons/hh’s) with the urbansim datasources to see if they can be replaced

- [ ] replace asim_persons with urbansim persons

- [ ] replace asim_households with households

- [ ] merge asim_store with urbansim store

- [ ] replace random number generation in asim_utils.py with random seed urbansim

- [ ] replace logit.py with choiceModels logit

- [ ] merge asim_datasources, asim_models, asim_utils with main urbansim modules

- [ ] merge asim_settings.yaml with urbansim settings.yaml

- [ ] file addt’l asim modules (skim.py, asim_simulate.py, tracing.py, etc.) into core urbansim code

Datasources:

- [x] mtc_asim.h5

- [x] skims.omx

- [x] destination_mode_choice_size_terms.csv

In-memory orca tables:

- [x] asim_households

- [x] asim_persons

- [x] asim_persons_merged

- [x] destination_size_terms

- [x] asim_store

- [x] skim_dict

New baus files:

- asim_datasources.py
    - combination of orca registrations from:
        - asim.abm.tables.landuse
        - asim.abm.tables.size_terms
        - asim.abm.tables.skims
        - asim.abm.tables.households
        - asim.abm.tables.persons
- asim_models.py
- asim_utils.py
    - combination of functions from:
        - asim.core.config
        - asim.core.util
        - asim.core.pipeline
        - asim.abm.tables.size_terms
        - asim.abm.models.util.logsums

Configs files:

- [x] destination_choice_size_terms.csv

- [x] logsums_spec_work.csv

- [x] tour_mode_choice.yaml

- [x] workplace_location.csv

- [x] workplace_location_sample.csv

- [x] workplace_location.yaml

Addt’l files/scripts not placed in `asim_*`-prefixed .py files:

- [x] skim.py

- defines skim class objects that are necessary for loading the skims in asim_datasources.py

- [x] tracing.py

- for orca tracing, this should be very useful for urbansim but its already used by many asim models.

- [x] interaction_sample.py

- sampling of alternatives
- choosers must be merged with alternatives b/c there are interaction terms….not sure I understand merging here

- [x] interaction_simulate.py

- [x] interaction_sample_simulate.py

- [x] logit.py

- [x] asim_simulate.py

- from asim.core.simulate
- first tried to just merge functions into asim_utils but there’s too much code

- [x] asim_misc.py

- from asim.abm.misc
- basically just loading orca.injectables from asim_settings
- first tried to just merge functions into asim_utils but there’s too much code

New package requirements for urbansim:

- openmatrix
