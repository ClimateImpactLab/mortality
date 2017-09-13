import xarray as xr
import pandas as pd
import numpy as np


class Impact():
  '''
    Base class for computing an impact as specified by the Climate Impact Lab

  '''
  def __init__(self, gammas ):
    self.gammas = gammas

  def get_annual_weather(self, weather, preds):
    '''
    Constructs the annual weather dataset for a given years impact

    Parameters
    ----------
    models_paths: list
        unformatted string representing path to weather variables for that year

    preds: dict
      describes how to format input file paths for weather files

    Returns
    -------

      Dataset
        :py:class `~xarray Dataset` with each weather variable as an `~xarray DataArray`
    '''
    weather_files = [weather.format(pred=pred) for pred in preds]

    datasets = []
    for file in weather_files:
      with xr.open_dataset(file) as ds:
          ds.load()
          datasets.append(ds)

    weather = xr.concat(datasets, pd.Index(preds, name='prednames'))

    return weather

  def compute_betas(self, clim_covars, gdp_covars):
    '''
    Computes the matrices beta*gamma x IR for each covariates 
    
    Parameters
    ----------
    gammas: :py:class `~xarray.Dataset`
        Coefficients for pred/covar combo

    spec: 
      specifies the shape/structure of computation

    clim_covars: :py:class `~xarray.Dataset`
        covariates for each hierid
    
    gpd_covars: :py:class `~xarray.Dataset`
        covariates for each hierid
 
    Returns
    -------
      :py:class `~xarray.Dataset` values for each predname beta

    '''

    betas = xr.Dataset()

    
    covars = xr.merge([clim_covars, gdp_covars])

    #add intercept for easy math
    covars['1'] = ('hierid', ), np.ones(len(covars.hierid))

    betas = sum((self.gammas*covars).data_vars.values())

    return betas


  def compute(self,  
              spec, 
              gdp_covars,
              clim_covars,
              annual_weather_paths,
              baseline,
              min_function=None,
              min_max=None,
              min_write_path=None,
              impact_function=None,
              postprocess_daily=False,
              postprocess_annual=False):
    '''
    Computes an impact for a unique set of gdp, climate, weather and gamma coefficient inputs.
    For each set of these, we take the analytic minimum value between two points and 
    

    Parameters
    ----------


    Returns
    -------
      :py:class `~xarray.Dataset` of impacts by hierid by outcome group 

    '''
    #Generate Betas
    betas = self.compute_betas(clim_covars, gdp_covars)

    #Compute Raw Impact
    impact= impact_function(betas, self.annual_weather, spec)

    #Compute the min for flat curve adaptation
    if min_function:
      m_star = self.compute_m_star(betas, min_max, min_write_path)
      #Compare values and evaluate a max
      impact = np.minimum(impact, m_star)

    if postprocess_daily:
      impact = postprocess_daily(impact)
    if postprocess_annual:
      impact = postprocess_annual(impact)

    #Sum to annual, substract baseline, normalize 
    impact_annual = (impact.sum(dim='time')  - baseline['baseline'])

    return impact_annual

  def postprocess_daily(self, impact):
    raise NotImplementedError

  def postprocess_annual(self, impact):
    raise NotImplementedError
