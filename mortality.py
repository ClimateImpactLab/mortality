from impact import Impact
from mins import minimize_polynomial
import xarray as xr
import numpy as np
import os

class Mortality_Polynomial(Impact):
	'''
	Mortality specific 
	'''

	min_function = staticmethod(minimize_polynomial)

	def impact_function(self, betas, weather):
		'''
		computes the dot product of betas and annual weather by outcome group

		'''
		#slick
		impact = (betas*weather).sum(dim='prednames')
		
		#verbose
		# impact =  (betas.sel(prednames='tas')*weather['tas'] + 
  #               betas.sel(prednames='tas-poly-2')*weather['tas-poly-2'] + 
  #               betas.sel(prednames='tas-poly-3')*weather['tas-poly-3'] + 
  #               betas.sel(prednames='tas-poly-4')*weather['tas-poly-4'])

		return impact

	# def compute_t_star(self, betas, min_max_boundary):

	# 	return minimize_polynomial(betas, min_max_boundary)
  		


