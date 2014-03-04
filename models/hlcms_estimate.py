import pandas as pd, numpy as np, statsmodels.api as sm
from synthicity.urbanchoice import *
from synthicity.utils import misc
import time, copy, os, sys
from patsy import dmatrix

SAMPLE_SIZE=100

def hlcms_estimate(dset,year=None,show=True):

  assert "locationchoicemodel" == "locationchoicemodel" # should match!
  returnobj = {}
  
  # TEMPLATE configure table
  households = dset.households
  households = households[households.tenure<>1]
  # ENDTEMPLATE
  
  # TEMPLATE randomly choose estimatiors
  households = households.loc[np.random.choice(households.index, 10000,replace=False)]
  # ENDTEMPLATE
  # TEMPLATE specifying alternatives
  alternatives = dset.building_filter(residential=1)
  # ENDTEMPLATE
  
  # TEMPLATE merge 
  t_m = time.time()
  alternatives = pd.merge(alternatives,dset.fetch_csv('nodes.csv',index_col='node_id'),**{'right_index': True, 'left_on': '_node_id'})
  print "Finished with merge in %f" % (time.time()-t_m)
  # ENDTEMPLATE
  t1 = time.time()

  # TEMPLATE creating segments
  segments = households.groupby(['income_quartile'])
  # ENDTEMPLATE
    
  for name, segment in segments:

    name = str(name)
    outname = "hlcms" if name is None else "hlcms_"+name

    global SAMPLE_SIZE
    sample, alternative_sample, est_params = interaction.mnl_interaction_dataset(
                                        segment,alternatives,SAMPLE_SIZE,chosenalts=segment["building_id"])

    print "Estimating parameters for segment = %s, size = %d" % (name, len(segment.index)) 

    # TEMPLATE computing vars
    print "WARNING: using patsy, ind_vars will be ignored"
    data = dmatrix("np.log1p(unit_sqft) + sum_residential_units + ave_unit_sqft + ave_lot_sqft + ave_income + poor + sfdu + renters + np.log1p(res_sales_price) - 1", data=alternative_sample, return_type='dataframe')
    # ENDTEMPLATE
    if show: print data.describe()

    d = {}
    d['columns'] = fnames = data.columns.tolist()

    data = data.as_matrix()
    if np.amax(data) > 500.0:
      raise Exception("WARNING: the max value in this estimation data is large, it's likely you need to log transform the input")
    fit, results = interaction.estimate(data,est_params,SAMPLE_SIZE)
 
    fnames = interaction.add_fnames(fnames,est_params)
    if show: print misc.resultstotable(fnames,results)
    misc.resultstocsv(fit,fnames,results,outname+"_estimate.csv",tblname=outname)
    
    d['null loglik'] = float(fit[0])
    d['converged loglik'] = float(fit[1])
    d['loglik ratio'] = float(fit[2])
    d['est_results'] = [[float(x) for x in result] for result in results]
    returnobj[name] = d
    
    dset.store_coeff(outname,zip(*results)[0],fnames)

  print "Finished executing in %f seconds" % (time.time()-t1)
  return returnobj
