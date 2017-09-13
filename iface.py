'''

Marginal impact of temperature on mortality 

Values are annual/daily expected damage resolved to GCP hierid/country level region. 

'''

import os
import logging
import time
import numpy as np
import datetime


from jrnr import slurm_runner

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('uploader')
logger.setLevel('DEBUG')


__author__ = 'Justin Simcock'
__contact__ = 'jsimcock@rhg.com'
__version__ = '0.1.1'



ANNUAL_WEATHER_FILE = (
    '/global/scratch/mdelgado/projection/gcp/climate/hierid/popwt/daily/' +
    'tas{poly}/{scenario}/{model}/{year}/1.5.nc4')

CLIMATE_COVAR = ('/global/scratch/jsimcock/data_files/covars/climate/hierid/popwt/tas_kernel_30/' +
    '{scenario}/{model}/{year}/0.1.1.nc4')

covar_files_hist = {
    'climtas': ,
    'loggdppc':
}


GDP_COVAR = ('/global/scratch/jsimcock/data_files/covars/ssp_kernel_13_gdppc/{ssp}/{econ_model}/{year}/0.1.0.nc')


GDP_2015 = ('/global/scratch/jsimcock/data_files/covars/ssp_kernel_13_gdppc/{ssp}/{econ_model}/2015/0.1.0.nc')

CLIMATE_2015 = ('/global/scratch/jsimcock/data_files/covars/climate/hierid/popwt/tas_kernel_30/' +
    'rcp85/{model}/2015/0.1.1.nc4')

GAMMAS_FILE = ('/global/scratch/jsimcock/data_files/covars/' + 
                'global_interaction_Tmean-POLY-4-AgeSpec.csvv')

GAMMAS_MIN_PATH = ('/global/scratch/jsimcock/data/covars/gamma_mins/{seed}/{scenario}/{econ_model}/{ssp}.nc') 

BASE_YEARS = [2000, 2010]

WRITE_PATH = ('/global/scratch/jsimcock/gcp/impacts/{variable}/{seed}/{scenario}/{econ_model}/{ssp}/{model}/{year}/{version}.nc')


description = '\n\n'.join(
        map(lambda s: ' '.join(s.split('\n')),
            __doc__.strip().split('\n\n')))

oneline = description.split('\n')[0]


ADDITIONAL_METADATA = dict(    
    oneline=oneline,
    description=description,
    author=__author__,
    contact=__contact__,
    version=__version__,
    repo='https://github.com/ClimateImpactLab/mortality',
    file=str(__file__),
    execute='python mortality.py run',
    project='gcp', 
    team='impacts-mortality',
    frequency='daily',
    variable='mortality-daily',
    created= str(datetime.datetime.now())
    )


MODELS = list(map(lambda x: dict(model=x), [
    'ACCESS1-0',
    # 'bcc-csm1-1',
    # 'BNU-ESM',
    # 'CanESM2',
    # 'CCSM4',
    # 'CESM1-BGC',
    # 'CNRM-CM5',
    # 'CSIRO-Mk3-6-0',
    # 'GFDL-CM3',
    # 'GFDL-ESM2G',
    # 'GFDL-ESM2M',
    # 'IPSL-CM5A-LR',
    # 'IPSL-CM5A-MR',
    # 'MIROC-ESM-CHEM',
    # 'MIROC-ESM',
    # 'MIROC5',
    # 'MPI-ESM-LR',
    # 'MPI-ESM-MR',
    # 'MRI-CGCM3',
    # 'inmcm4',
    # 'NorESM1-M'
    ]))

MINS = [dict(min_function='findpolymin')]

PERIODS = [ dict(scenario='historical', year=y) for y in range(1981, 2006)] + [dict(scenario='rcp85', year=y) for y in range(2006, 2100)]

SSP = [dict(ssp='SSP' + str(i)) for i in range(1,6)]

ECONMODEL = [dict(econ_model='low'), dict(econ_model='high')]


#we want to do a realization of all models for the periods at a given set of periods
JOB_SPEC = [PERIODS, MODELS, SSP, ECONMODEL]

@slurm_runner(filepath=__file__, job_spec=JOB_SPEC)
def impact`_annual(
                    metadata,
                    econ_model, 
                    model,
                    scenario,
                    ssp, 
                    year,
                    min_function=None,
                    mc=False,
                    interactive=False):
    '''
    Calculates the IR level daily/annual effect of temperature on Mortality Rates

    Parameters
    ----------

    climate_covar: str
        path to climate covar

    gammas_path: str
        path to csvv

    annual_climate_path: str
        path for a given year

    gdp_data: str
        path to gdp data

    year: int
        year of impacts to compute

    Returns
    -------

    Xarray Dataset 

    '''
    t_outer1 = time.time()
    import xarray as xr
    from impact import Impact
    from csvv import Gammas
    from baselines import impact_baseline


    metadata.update(ADDITIONAL_METADATA)
    metadata['year'] = year
    metadata['scenario'] = scenario
    metadata['econ_model'] = econ_model
    metadata['model'] = model
    metadata['ssp'] = ssp


    gdp_covar_current_path = GDP_COVAR.format(**metadata)
    gdp_covar_2015_path = GDP_2015.format(**metadata)

    climate_covar_current_path = CLIMATE_COVAR.format(**metadata)
    climate_covar_2015_path = CLIMATE_2015.format(**metadata)


    #Load data for baseline and clipping computations
    with xr.open_dataset(climate_covar_2015_path) as clim_covar_2015:
        clim_covar_2015.load()


    with xr.open_dataset(gdp_covar_2015_path) as gdp_covar_2015:
        gdp_covar_2015.load()


    if year < 2015:
        gdp_covar = gdp_covar_2015
        clim_covar = clim_covar_2015

    else: 
        with xr.open_dataset(gdp_covar_current_path,autoclose=True) as gdp_covar:
            gdp_covar.load()
        logger.debug('reading covariate data from {}'.format(gdp_covar_current_path))

        with xr.open_dataset(climate_covar_current_path, autoclose=True) as clim_covar:
            clim_covar.load()
        logger.debug('reading covariate data from {}'.format(climate_covar_current_path))


    ##################
    # Compute Median #
    ##################

    median_ds = xr.Dataset()
    impact_median = Impact(ANNUAL_WEATHER_FILE)
    gammas, spec = Gammas(GAMMAS_FILE)


    gammas_median = gammas.median()

    metadata['seed'] = 'median'
    metadata['year'] = 'baseline'

    gammas_min_path = GAMMAS_MIN_PATH.format(**metadata)


    #compute_baseline_median
    baseline_median_path = WRITE_PATH.format(**metadata)
    baseline_median = impact_baseline(gammas_median,spec, ANNUAL_WEATHER_FILE, gdp_covar_2015,clim_covar_2015, metadata, base_years, impact_function, baseline_median_path)

    #No Adaptation
    median_ds['no_adaptation'] = impact.compute(gammas_median, spec, ANNUAL_WEATHER_FILE, gdp_covar_2015, clim_covar_2015, baseline_median, gammas_min_path)

    #Income Adaptation
    median_ds['income_adaptation'] = impact.compute(gammas_median, spec, ANNUAL_WEATHER_FILE, gdp_covar, clim_covar_2015, baseline_median, gammas_min_path)

    #No Income Adaptation
    median_ds['no_income_adaptation'] = impact.compute(gammas_median, spec, ANNUAL_WEATHER_FILE, gdp_covar_2015, clim_covar, baseline_median, gammas_min_path)

    #Full Adaptation
    median_ds['full_adaptation'] = impact.compute(gammas_median, spec, ANNUAL_WEATHER_FILE, gdp_covar, clim_covar, baseline_median, gammas_min_path)

    #India impact
    gammas_india, spec_india = Gammas(GAMMAS_INDIA_FILE)

    gammas_india_median = gammas_india.median()
    median_ds['india'] = impact.compute(gammas_india_median, spec_india, ANNUAL_WEATHER_FILE, gdp_covar, clim_covar)

    #Goodmoney 
    median_ds['goodmoney'] = np.maximum(median_ds['full_adaptation'], median_ds['no_income_adaptation'])

    #India coomparison
    #Apply some comparison between a value in India's impact to one (or all of the other impacts)

    median_ds.attrs.update({k: str(v) for k,v in metadata.items()})

    write_path = WRITE_PATH.format(**metadata)

    if not os.path.isdir(os.path.dirname(write_path)):
                  os.makedirs(os.path.dirname(write_path))
                
    median_ds.to_netcdf(write_path)


    ##############
    # Compute MC #
    ##############

    if mc: 
        for seed in range(13):

            t_inner_1 = time.time()
            gammas_sample = gammas.sample(seed)

            metadata['seed'] = seed

            gammas_min_path = GAMMAS_MIN_PATH.format(**metadata)

            ds_mc = xr.Dataset()

            ####################
            # compute_baseline #
            ####################

            metadata['year'] = 'baseline'
            base_seed_path = WRITE_PATH.format(**metadata)

            t_base1 = time.time()
            seed_base_impact = impact_baseline(gammas_sample, spec, ANNUAL_WEATHER_FILE, gdp_covar_2015, clim_covar_2015, base_seed_path)

            t_base2 = time.time()
            logger.debug('Computing baseline for {} {} {} {}: {}'.format(scenario, econ_model, model, ssp, t_base2 - t_base1))


            #########################
            # compute no adaptation #
            #########################

            t_noadp1 = time.time()

            ds_mc['no_adaptation']  = impact.compute(gammas_sample, spec, clim_covar_2015, gdp_covar_2015, seed_base_impact, gammas_min_path)

            t_noadp2 = time.time()
            logger.debug('Computing no adaptiaion for {}: {}'.format(year, t_noadp2 - t_noadp1))

            #############################
            # compute income adaptation #
            #############################

            t_incadp1 = time.time()

            ds_mc['income_adaptation'] = impact.compute(gammas_sample, spec, clim_covar_2015, gdp_covar, seed_base_impact, gammas_min_path)

            t_incadp2 = time.time()
            logger.debug('Computing income only adaptiaion for {}: {}'.format(year, t_incadp2 - t_incadp1))

            ###########################
            # compute full adaptation #
            ###########################

            t_full1 = time.time()

            ds_mc['mortality_full_adaptation'] = impact.compute(gammas_sample, spec, clim_covar, gdp_covar, seed_base_impact, gammas_min_path)

            t_full2 = time.time()
            logger.debug('Computing full adaptiaion for {}: {}'.format(year, t_full2 - t_full1))

            ################################
            # compute no income adaptation #
            ################################

            t_noincome1 = time.time()

            ds_mc['no_income_adaptation'] = impact.compute(gammas_sample, spec, clim_covar, gdp_covar_2015, seed_base_impact, gammas_min_path)

            t_noincome2 = time.time()
            logger.debug('Computing no income adaptiaion for {}: {}'.format(year, t_noincome2 - t_noincome1))

            #######################
            # computing goodmoney #
            #######################

            t_goodmoney1 = time.time()
            ds_mc['goodmoney'] = np.maximum(ds_mc['mortality_full_adaptation'], ds_mc['no_income_adaptation'])
            t_goodmoney2 = time.time()
            logger.debug('Computing goodmoney for {}: {}'.format(year, t_goodmoney2 - t_goodmoney1))

            ###################
            # computing india #
            ###################
            gammas_india_sample = gammas_india.sample(seed)
            median_ds['india'] = impact.compute(gammas_india_sample, spec_india, ANNUAL_WEATHER_FILE, gdp_covar, clim_covar)


            logger.debug('Computing impact for {}'.format(year))
       

            impact.attrs.update({k:str(v) for k,v in metadata.items()})

            write_path = WRITE_PATH.format(**metadata)

            if not os.path.isdir(os.path.dirname(write_path)):
                  os.makedirs(os.path.dirname(write_path))
                
            impact.to_netcdf(write_path)

            t_inner_2 = time.time()
            logger.debug('Inner Loop time for {}: {}'.format(year, t_inner_2 - t_inner_1))

    t_outer2 = time.time()
    logger.debug('Computed impact for year {}: {}'.format(year, t_outer2 - t_outer1))


if __name__ == '__main__':
    mortality_annual()