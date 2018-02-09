Fall 2017 Work
=======
## Merging Long-term Choice Models from ActivitySim
### Notes:

- Instead of the logger used throughought the Asim code, UrbanSim just redirects stdout to a logfile and issues print commands. I've converted all `logging` commands in Activitysim to `print()` statements. This was probably not the right thing to do, as the Asim code is more verbose than UrbanSim.
- Skims are loaded from omx objects, we prob want to change this
- Some “placeholder” columns were note included for persons/hh’s tables b/c they reference models that we’re not yet running

### Lingering questions:

- If module c contains orca injectables, and I import module c inside module b, do those injectables get registered when I load module b in module a?
    - currently loading `asim_misc` in `asim_datasources` which gets loaded in `asim_models`

### TO DO:

- [x] clean up interaction_sample.py in baus
- [x] clean up logit.py in baus
- [x] clean up asim_simulate.py in baus
- [x] port over `workplace_location_logsums`
- [x] clean up interaction_sample_simulate.py in baus
- [x] port over `workplace_location_simulate`
- [ ] try to run `workplace_location_choice` as a model step in urbansim
- [ ] workplace location choice needs its own mode_choice config
- [ ] replace datasources with “Full Example” datasources from MTC Box
- [ ] diff the datasources (persons/hh’s) with the urbansim datasources to see if they can be replaced
- [ ] replace `asim_persons` with urbansim `persons`
- [ ] replace `asim_households` with `households`
- [ ] merge `asim_store` with urbansim `store`
- [ ] replace random number generation in asim_utils.py with random seed urbansim
- [ ] replace logit.py with choiceModels logit
- [ ] merge `asim_datasources`, `asim_models`, `asim_utils` with main urbansim modules
- [ ] merge asim_settings.yaml with urbansim settings.yaml
- [ ] file addt’l asim modules (skim.py, asim_simulate.py, tracing.py, etc.) into core urbansim code
- [ ] deal with `workplace_location_logsums` dependence on *tour_mode_choice.yaml*

### Configs files needed:

- [x] *asim_settings.yaml* -- from *settings.yaml* in asim configs dir
- [x] *destination_choice_size_terms.csv*
- [x] *logsums_spec_work.csv*
- [x] *tour_mode_choice.yaml*
- [x] *workplace_location.csv*
- [x] *workplace_location_sample.csv*
- [x] *workplace_location.yaml*

### Datasources needed:

- [x] *mtc_asim.h5*
- [x] *skims.omx*

### In-memory orca tables needed:
This is really bad form, but I've prefixed all of these orca tables with `asim` in order to keep them separate from the tables of the same name used by the rest of urbansim. Eventually we can and should merge them all, but it was necessary to keep them separate until testing was complete. It's ugly, however, because many methods and functions depend on calls to the orca table names, so wherever `persons` or `households` is mentioned in the activitysim code I've had to add the prefix `asim_`. It was a pain to do so, and will be a pain to revert once the datasources have been merged. I also probably missed a bunch of calls where I should have added the prefix, but there's no way to know until things start to breaking. When they do, its a good chance this is the cause.

- [x] `asim_store`
    - [x] `asim_households`
    - [x] `asim_persons`
    - [x] `asim_persons_merged`
- [x] `destination_size_terms`
- [x] `skim_dict`

### New baus files:

- **asim_datasources.py** -- combination of orca registrations from:
    - `asim.abm.tables.landuse`
    - `asim.abm.tables.size_terms`
    - `asim.abm.tables.skims`
    - `asim.abm.tables.households`
    - `asim.abm.tables.persons`
- **asim_models.py**
- **asim_utils.py** -- combination of functions from:
    - `asim.core.config`
    - `asim.core.util`
    - `asim.core.pipeline`
    - `asim.abm.tables.size_terms`
    - `asim.abm.models.util.logsums`



### Addt’l modules ported over as-is:

- [x] **skim.py**
    - defines skim class objects that are necessary for loading the skims in asim_datasources.py
- [x] **tracing.py**
    - for orca tracing, this should be very useful for urbansim but its already used by many asim models.
- [x] **logit.py**
    - defines logit structure, makes choices
- [x] **asim_simulate.py** -- from `asim.core.simulate`
    - simulation logic: computing utilities, probabilities, evaluating estimated logit models
    - not to be confused with simulation.py which executes the model steps
- [x] **interaction_sample.py**
    - random sampling of alternatives when interaction terms are involved
- [x] **interaction_sample_simulate.py**
    - eval logit models when interaction terms are involved
- [x] **interaction_simulate.py**
    - same methods as above but for models specs without random sampling.
- [x] **asim_misc.py** -- from `asim.abm.misc`
    - loads orca.injectables from `asim_settings`

### New package requirements for urbansim:

- openmatrix
