import xarray as xr, pandas as pd, numpy as np
from mortality import Mortality_Polynomial
from csvv import Gammas
from impact import Impact
import time



def test_this():

	t1  = time.time()
	g = Gammas('/global/scratch/jsimcock/data_files/covars/global_interaction_Tmean-POLY-4-AgeSpec.csvv')
	gdp = xr.open_dataset('/global/scratch/jsimcock/data_files/covars/ssp_kernel_13_gdppc/SSP1/high/2015/0.1.0.nc')
	climtas = xr.open_dataset('/global/scratch/jsimcock/data_files/covars/climate/hierid/popwt/tas_kernel_30/rcp45/ACCESS1-0/2015/0.1.1.nc4')
	gdp = gdp.rename({'gdppc': 'loggdppc'})
	climtas = climtas.rename({'tas':'climtas'})


	path = '/global/scratch/mdelgado/projection/gcp/climate/hierid/popwt/daily/{pred}/rcp85/ACCESS1-0/2015/1.5.nc4'
	t_star_path = '/global/scratch/jsimcock/data_files/covars/t_star_median.nc'

	gammas = g.median()

	m = Mortality_Polynomial(path, gammas.prednames.values)
	betas = m._compute_betas(gammas, [gdp, climtas])


	#a, b, c, d, e = m.compute(gammas, gdp, climtas, min_max_boundary=[10,25], t_star_write_path=t_star_path) 


	t2 = time.time()

	print(t2-t1)

	return m.weather, betas



if __name__=='__main__':
	test_this()                                       



a.sel(predname='tas')*b.sel(prednames='tas') + 
a.sel(predname='tas-poly-2')*b.sel(prednames='tas-poly-2') + 
a.sel(predname='tas-poly-3')*b.sel(prednames='tas-poly-3') + 
a.sel(predname='tas-poly-4')*b.sel(prednames='tas-poly-4')