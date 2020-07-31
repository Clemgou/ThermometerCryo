# -*- coding: utf-8 -*-
#bash! /bin/env/python

##############################################################################################################
# IMPORTATION
##############################################################################################################

from __future__ import division
import numpy as np

##############################################################################################################
# FUNCTION
##############################################################################################################

def ThermoBTTvsR(R):
    '''
    Returns a scalar or an array, depending of the type of the arguments
    '''
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # ---  --- #
    thrs_idx1    = R_<1464.4
    thrs_idx2    = R_>=1464.4
    T[thrs_idx1] = 13.9942*(np.log(R_[thrs_idx1]/116.928)**(-1.09771)) - 3.54293
    T[thrs_idx2] = 3.01749*(np.log(R_[thrs_idx2]/436.589)**(-3.53959)) - 0.0219203
    # ---  --- #
    return T[0] if T.size == 1 else T

def ThermoNICOTvsR(R):
    '''
    Returns a scalar or an array, depending of the type of the arguments
    '''
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # ---  --- #
    T[R_<=1000] = 0.0215*(20000/R_[R_<=1000])**1.7
    # ---  --- #
    return T[0] if T.size == 1 else T

def ThermoNICOCALTvsR(R):
    '''
    Returns a scalar or an array, depending of the type of the arguments
    '''
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # ---  --- #
    T[:] = 300
    # ---
    cond = 16607.4 < R_
    T[cond] = 0.02*(18100/R)**(1/0.4)
    # ---
    cond = 13568.6 < R_ <= 16607.4
    T[cond] = 0.03*(15100/R_[cond]) ** (1/0.5)
    # ---
    cond = 4966.46 < R_ <= 13568.6
    T[cond] = 0.04*(13000/R_[cond]) ** (1/0.58)
    # ---
    cond =  2521.26 < R_ <= 4966.46
    T[cond] =  0.4*( 3600/R_[cond]) ** (1/0.5)
    # ---
    cond =  1540.54 < R_ <= 2521.26
    T[cond] =  1.5*( 2100/R_[cond]) ** (1/0.3)
    # ---
    cond =  1204.76 < R_ <= 1540.54
    T[cond] =   10*( 1330/R_[cond]) ** (1/0.17)
    # ---
    cond =  1000 < R_ <= 1204.76
    T[cond] =   30*( 1150/R_[cond]) ** (1/0.09)
    # ---  --- #
    return T[0] if T.size == 1 else T

def C100RvsT(T):
    '''
    Returns a scalar or an array, depending of the type of the arguments
    '''
    T_ = np.array(T, ndmin=1)
    R  = np.ones(T_.shape)*1e6
    # ---  --- #
    R[T_>1] = 37.4 + 42.8* np.exp( ((T_[T_>1] - 0.43)/42.8)**(-0.476))
    R       = R.real
    # ---  --- #
    return R[0] if R.size == 1 else R

def PT100TvsR(R): # fonction de conversion de la PT100 R->T
    return 33 + 2.25686*R + 0.00208613*R**2 - 3.81907e-6*R**3;

def PT100RvsT(T):
    return -13.360797686195307 + 0.4291105897341029* T -  0.00006954505159584381* T**2 + 6.690566222875814e-9 * T**3;

def RuO2RvsT(T):
   return 864.3237440617243 * np.exp(((T + 0.01)/0.8839588539497837)**(-1/ 2.9742823228005086))

def ThermoBTRvsT(T):
    return    1./ ( 1/C100RvsT(T)+1/RuO2RvsT(T)) + PT100RvsT(T) ;

def ThermoHTRvsT(T):
    return 1.01625*C100RvsT(T)+PT100RvsT(T)

# ====== old version ====== #

'''
def ThermoBTTvsR(R):
   if (R < 1464.4):
      return 13.9942*(np.log(R/116.928)**(-1.09771)) - 3.54293
   else:
      return 3.01749*(np.log(R/436.589)**(-3.53959)) - 0.0219203
'''

'''
def ThermoNICOTvsR(R):
   if (R>1000):
      return 0.0215*(20000/R)**1.7
   else:
      return 0
'''

'''
def C100RvsT (T):
   if  T > 1:
      result = 37.4 + 42.8* np.exp( ((T - 0.43)/42.8)**(-0.476))     # le +5 est rajoute a la main avec mathematica pour faire coller les temperature 100K/4K a 300K
      return result.real;
   else :
      return 1e6;
'''

'''
def ThermoNICOCALTvsR(R):
	if (R>16607.4):
		return 0.02*(18100/R)**(1/0.4)
	else:
		if (R>13568.6):
			return 0.03*(15100/R) ** (1/0.5)
		else:
			if (R>4966.46):
				return 0.04*(13000/R) ** (1/0.58)
			else:
				if (R>2521.26):
					return 0.4*(3600/R) ** (1/0.5)
				else:
					if (R>1540.54):
						return 1.5*(2100/R) ** (1/0.3)
					else:
						if (R>1204.76):
							return 10*(1330/R) ** (1/0.17)
						else:
							if (R>1000):
								return 30*(1150/R) ** (1/0.09)
							else:
								return 300
'''

##############################################################################################################
# MAIN
##############################################################################################################

if  __name__=="__main__":
    print('STARTING: Thermometer')
    print('FINNISHED')
