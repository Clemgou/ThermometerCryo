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

# ====== Material : R = f(T) ====== #

def PT100_RvsT(T, **kwargs):
    '''
    * For PT100 alone.
    * Defined for all the Temperature range. Although, when T is bellow 30 K, the
      resistance takes negative values.
    '''
    a = kwargs.pop('a',   6.690566222875814e-9)
    b = kwargs.pop('b', - 6.954505159584381e-5)
    c = kwargs.pop('c',   0.4291105897341029  )
    d = kwargs.pop('d', -13.360797686195307   )
    # ---  --- #
    return a*T**3 + b*T**2 + c*T + d

def C100_RvsT(T):
    '''
    * Returns a scalar or an array, depending of the type of the arguments
    * Resistance function defined only above 1K. Bellow, the resistance diverges,
      we thus set it to 1e6 Ohms by default.
    '''
    T_ = np.array(T, ndmin=1)
    R  = np.ones(T_.shape)*1e6 # 1e6 is the default R value when T<1 K.
    # ---  --- #
    R[T_>1] = 37.4 + 42.8* np.exp( ((T_[T_>1] - 0.43)/42.8)**(-0.476))
    R       = R.real
    # ---  --- #
    return R[0] if R.size == 1 else R

def RuO2_RvsT(T, **kwargs):
    '''
    * Resistance of a resistor made of RuO2 material.
    * Defined for all the Temperature range.
    '''
    a     = kwargs.pop('a'    ,   0.01                )
    R0    = kwargs.pop('R0'   , 864.3237440617243     )
    T0    = kwargs.pop('T0'   ,   0.8839588539497837  )
    alpha = kwargs.pop('alpha',  -0.33621556108985157 ) # -1/2.9742823228005086
    # ---  --- #
    T_ = np.array(T, ndmin=1)
    R  = np.ones(T_.shape)*1e6
    # ---
    R       = R0 * np.exp( ((T_ + a)/T0)**alpha )
    R       = R.real
    # ---  --- #
    return R[0] if R.size == 1 else R

# ====== function T --> R ====== #

def ThermoBT_RvsT(T):
    '''
    * Combination of resistance thermometer.
    * Pt100 + C100 + RuO2
    '''
    return    1./ ( 1/C100_RvsT(T)+1/RuO2_RvsT(T)) + PT100_RvsT(T) ;

def ThermoHT_RvsT(T):
    '''
    * Combination of resistance thermometer.
    * Pt100 + C100
    '''
    return 1.01625*C100_RvsT(T)+PT100_RvsT(T)

# ====== function R --> T ====== #

def ThermoBT_TvsR(R):
    '''
    * Returns a scalar or an array, depending of the type of the arguments
    * For mobile BM BT RuO2 C100 PT100, (a utiliser uniquement a basse
      temperature pour les thermometres mobiles)
    * Seulement utile pour faire une conversion rapide, sans optimize.newton
    '''
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # ---  --- #
    thrs_idx1    = R_< 1464.4
    thrs_idx2    = R_>=1464.4
    T[thrs_idx1] = 13.9942*(np.log(R_[thrs_idx1]/116.928)**(-1.09771)) - 3.54293
    T[thrs_idx2] = 3.01749*(np.log(R_[thrs_idx2]/436.589)**(-3.53959)) - 0.0219203
    # ---  --- #
    return T[0] if T.size == 1 else T

def ThermoNICO_TvsR(R):
    '''
    * Returns a scalar or an array, depending of the type of the arguments
    * For Thermo NICO
    '''
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # ---  --- #
    T[R_<=1000] = 0.0215*(20000/R_[R_<=1000])**1.7
    # ---  --- #
    return T[0] if T.size == 1 else T

def ThermoNICOCAL_TvsR(R):
    '''
    * Returns a scalar or an array, depending of the type of the arguments
    * For Thermo NICO
    '''
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # ---  --- #
    T[:] = 300
    # ---
    cond = (16607.40 < R_)
    T[cond] = 0.02*(18100/R_[cond])**(1/0.4)
    # ---
    cond = (13568.60 < R_) & (R_ <= 16607.4)
    T[cond] = 0.03*(15100/R_[cond]) ** (1/0.5)
    # ---
    cond = ( 4966.46 < R_) & (R_ <= 13568.6)
    T[cond] = 0.04*(13000/R_[cond]) ** (1/0.58)
    # ---
    cond = ( 2521.26 < R_) & (R_ <= 4966.46)
    T[cond] =  0.4*( 3600/R_[cond]) ** (1/0.5)
    # ---
    cond = ( 1540.54 < R_) & (R_  <= 2521.26)
    T[cond] =  1.5*( 2100/R_[cond]) ** (1/0.3)
    # ---
    cond = ( 1204.76 < R_ )& (R_ <= 1540.54)
    T[cond] =   10*( 1330/R_[cond]) ** (1/0.17)
    # ---
    cond = ( 1000.00 < R_) & (R_ <= 1204.76)
    T[cond] =   30*( 1150/R_[cond]) ** (1/0.09)
    # ---  --- #
    return T[0] if T.size == 1 else T

def PT100_TvsR(R):
    '''
    * Fonction de conversion de la PT100 R->T
    '''
    return 33 + 2.25686*R + 0.00208613*R**2 - 3.81907e-6*R**3

def C100_TvsR(R):
    '''
    * Returns a scalar or an array, depending of the type of the arguments
    * Carefull, diverges to infinity arround R=80.1 Ohms.
    '''
    R_ = np.array(R, ndmin=1)
    T  = np.ones(R_.shape) * 0.7651522 # default value when R>1e6 Ohm
    # ---  --- #
    thrs_idx1    = R_ < 1000000
    T[thrs_idx1] = 0.43 + 42.8*( np.log((R_[thrs_idx1]-37.4)/42.8) )**(-1/0.476)
    # ---  --- #
    return T[0] if T.size == 1 else T

# ====== revser function depending on >70 K ====== #

def ThermoBT_TvsR_root(R, above70K=False, **kwargs):
    '''
    * For "Mobile BT"
    * Reference BT RuO2 C100 PT100, (pour le moment, ne l'utiliser qu'a haute temperature)
    * scipy.optimize.newton( func, x0, *args, **kwargs), find the root of the function
      'func(x)', while beginning at an initiate x0, close to the actual zero.
    '''
    verbose = kwargs.pop('verbose', False)
    T_dflt  = kwargs.pop('T_dflt' , None) # [K]
    # ---  --- #
    R_      = np.array(R, ndmin=1)
    T       = np.zeros(R_.shape)
    # ---  --- #
    for i,r in enumerate(R_):
        try:
            T[i] = scipy.optimize.newton( (lambda T:ThermoBT_RvsT(T)-r) , 200 if above70K else 0.02)
        except RuntimeError:
            print('RuntimeError in ThermoBTTvsR_reverse: no value found with scipy.optimize.newton.') if verbose else None
            T[i] = T_dflt
    # ---  --- #
    return T[0] if T.size == 1 else T

def ThermoHT_TvsR_root(R, above70K=False, **kwargs):
    '''
    * For "Mobile HT"
    * Reference HT C100-PT100
    * scipy.optimize.newton( func, x0, *args, **kwargs), find the root of the function
      'func(x)', while beginning at an initiate x0, close to the actual zero.
    '''
    verbose = kwargs.pop('verbose', False)
    T_dflt  = kwargs.pop('T_dflt' , None) # [K]
    # ---  --- #
    R_      = np.array(R, ndmin=1)
    T       = np.zeros(R_.shape)
    # ---  --- #
    for i,r in enumerate(R_):
        try:
            T[i] = scipy.optimize.newton( (lambda T:ThermoHT_RvsT(T)-r) , 200 if above70K else 2)
        except RuntimeError:
            print('RuntimeError in ThermoHTRvsT_reverse: no value found with scipy.optimize.newton.') if verbose else None
            T[i] = T_dflt
    # ---  --- #
    return T[0] if T.size == 1 else T

def ThermoBT_TvsR_spln(R, above70K=False, **kwargs):
    '''
    * Inverse of ThermoBT_RvsT, in order to get the temperature from a resistance measurement.
      However, one must take the distinction between the part above 70 K, and the one bellow 70K.
    * Without any analytical inverse function, the evaluation of T=func(R) is made using approximation
      cubic spline functions, defines in specific range of R. It commes from a manual optimisation, and
      the good enough spline coefficient are stored in the function.
    * The spline optimisation has been made using cubicSpline_coeff_computing.
    '''
    verbose  = kwargs.pop('verbose', False)
    dR_bnd   = kwargs.pop('dR_bnd' , 1e-5) # [Ohm]
    # --- Spline coefficient and domain definition --- #
    spln_dic = {
        0 : {'above70K':True , 'boundary': [ThermoBT_RvsT(7e1), 137.43235776204997], 'coeff': (70.0, 22.52365474990894, -6.9770467433559284, 0.8742043290186831)},
        1 : {'above70K':True , 'boundary': [137.43235776204997, 200.98685724080576], 'coeff': (100.0, 4.766682114127137, -0.04579688972296893, 0.00031957563563563733)},
        2 : {'above70K':True , 'boundary': [200.98685724080576, 435.85541705435446], 'coeff': (300.0, 2.8157229834824213, 0.00013794515044629046, 2.397764032829255e-06)},
        3 : {'above70K':True , 'boundary': [435.85541705435446, 4090.247318593811 ], 'coeff': (1000.0, 3.2822226189393215, -3.633959540639026e-05, -5.141557734090797e-08)},
        4 : {'above70K':False, 'boundary': [ThermoBT_RvsT(7e1), 134.09501041298557], 'coeff': (70.0, -309.14808022234035, 39455.93555381805, -1965549.9973341406)},
        5 : {'above70K':False, 'boundary': [134.09501041298557, 134.1912335225398 ], 'coeff': (69.0, -69.79751530978243, 683.9821465446398, -2937.1689978712166)},
        6 : {'above70K':False, 'boundary': [134.1912335225398, 134.61880261470728 ], 'coeff': (66.0, -19.75248316910303, 29.32324139567444, -24.501473836976256)},
        7 : {'above70K':False, 'boundary': [134.61880261470728, 136.5008817453887 ], 'coeff': (61.0, -8.114794733567383, 2.7162611322203483, -0.5023313955667926)},
        8 : {'above70K':False, 'boundary': [136.5008817453887, 144.34985840396163 ], 'coeff': (52.0, -3.2284656949032393, 0.28175447078524485, -0.012444975728843245)},
        9 : {'above70K':False, 'boundary': [144.34985840396163, 164.85858143908155], 'coeff': (38.0, -1.1055689151400592, 0.033743005718536195, -0.0005238459754895229)},
        10: {'above70K':False, 'boundary': [164.85858143908155, 221.29467734671675], 'coeff': (25.0, -0.38251798281257127, 0.004999813612340653, -2.9689707617719814e-05)},
        11: {'above70K':False, 'boundary': [221.29467734671675, 333.69256212664845], 'coeff': (14.0, -0.10186615027810998, 0.0006394690872973255, -1.8515066294783854e-06)},
        12: {'above70K':False, 'boundary': [333.69256212664845, 518.3387557892462 ], 'coeff': (8.0, -0.02828803471755293, 9.36815790651613e-05, -1.5419626481484084e-07)},
        13: {'above70K':False, 'boundary': [518.3387557892462, 895.3730377547383  ], 'coeff': (5.0, -0.009463743398995247, 1.6166815445787894e-05, -1.362076413593773e-08)},
        14: {'above70K':False, 'boundary': [895.3730377547383, ThermoBT_RvsT(1e0) ], 'coeff': (3.0, -0.0030816291312388147, 2.30140128889834e-06, -8.351750508849628e-10)},
        15: {'above70K':False, 'boundary': [ThermoBT_RvsT(1e0), 2857.215303444065 ], 'coeff': (1.0, -0.001403090273183254, 1.360737411081143e-06, -6.306275276488724e-10)},
        16: {'above70K':False, 'boundary': [2857.215303444065 , 4233.24990567035  ], 'coeff': (0.5, -0.0004398413920480902, 2.503027512871836e-07, -6.091160370287172e-11)},
        17: {'above70K':False, 'boundary': [4233.24990567035  , 7393.954522712528 ], 'coeff': (0.21, -9.654104187203177e-05, 2.7399044169510914e-08, -3.1220365644014624e-12)},
        18: {'above70K':False, 'boundary': [7393.954522712528 , 14441.30260446487 ], 'coeff': (0.08, -1.6696735059732812e-05, 2.137936093789363e-09, -1.100352259007167e-13)},
        19: {'above70K':False, 'boundary': [14441.30260446487 , 29899.177715334856], 'coeff': (0.03, -2.8662308097586417e-06, 1.5707126658763552e-10, -3.5807105027714794e-15)},
        20: {'above70K':False, 'boundary': [29899.177715334856, 63950.41097093372 ], 'coeff': (0.01, -5.382182297889829e-07, 1.204188705294153e-11, -1.1740583816654862e-16)},
    }
    # ---  --- #
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # --- Set out of range default values
    T[R_>ThermoBT_RvsT(1e+4)] += 1e4*above70K
    T[R_>ThermoBT_RvsT(1e-3)] += 1e-3*(not above70K)
    T[R_<ThermoBT_RvsT(7e+1)]  = np.nan
    # --- Computing T from splines
    for spl_key in spln_dic:
        R_b     = spln_dic[spl_key]['boundary']
        a,b,c,d = spln_dic[spl_key]['coeff']
        # ---
        idx_g   = np.where(R_b[0]-dR_bnd<=R_)[0]
        idx_l   = np.where(R_<=R_b[1]+dR_bnd)[0]
        idx     = list(set(idx_g).intersection(set(idx_l)))
        # ---
        T[idx] += (a + b*(R_[idx]-R_b[0])**1 + c*(R_[idx]-R_b[0])**2 + d*(R_[idx]-R_b[0])**3) * int(spln_dic[spl_key]['above70K']==above70K)
    # ---  --- #
    return T[0] if T.size == 1 else T

def ThermoHT_TvsR_spln(R, above70K=False, **kwargs):
    '''
    * Inverse of ThermoHT_RvsT, in order to get the temperature from a resistance measurement.
      However, one must take the distinction between the part above 70 K, and the one bellow 70K.
    * Without any analytical inverse function, the evaluation of T=func(R) is made using approximation
      cubic spline functions, defines in specific range of R. It commes from a manual optimisation, and
      the good enough spline coefficient are stored in the function.
    * The spline optimisation has been made using cubicSpline_coeff_computing.
    '''
    verbose  = kwargs.pop('verbose', False)
    dR_bnd   = kwargs.pop('dR_bnd' , 1e-5) # [Ohm]
    T_thrs   = kwargs.pop('T_thrs' ,78.88)
    # --- Spline coefficient and domain definition --- #
    spln_dic = {
        0 : {'above70K':True , 'boundary': [ThermoHT_RvsT(78.88),  150.61524966725247], 'coeff': (78.87, 56.1844528190399, -115.21650595296315, 92.91011161676585)},
        1 : {'above70K':True , 'boundary': [ 150.61524966725247 ,  151.78900178948638], 'coeff': (90.0, 9.803150644715748, -0.9541498222969034, -0.11869751514322234)},
        2 : {'above70K':True , 'boundary': [ 151.78900178948638 ,  178.07012929774106], 'coeff': (100.0, 6.44617832053299, -0.17477612688316743, 0.002826341030047476)},
        3 : {'above70K':True , 'boundary': [ 178.07012929774106 ,  349.907262631601  ], 'coeff': (200.0, 3.0852288333006377, -0.0026543562764718516, 9.503525585446059e-06)},
        4 : {'above70K':True , 'boundary': [ 349.907262631601   ,  445.274437748751  ], 'coeff': (700.0, 3.0317556045995855, 0.000969502342940667, 2.366398942705002e-06)},
        5 : {'above70K':True , 'boundary': [ 445.274437748751   , 1442.1881228478064 ], 'coeff': (1000.0, 3.3104272074809544, 0.003208419044933503, -2.0073843666710245e-06)},
        6 : {'above70K':True , 'boundary': [1442.1881228478064  , ThermoHT_RvsT(1e4) ], 'coeff': (5500.0, 3.538239255543073, -0.0011155413449810807, 1.5858861298707488e-07)},
        7 : {'above70K':False, 'boundary': [ThermoHT_RvsT(78.88),    150.63460484496625], 'coeff': (78.89, -49.68664219148569, 98.12112288640778, -74.13358972012989)},
        8 : {'above70K':False, 'boundary': [  150.63460484496625,    152.08990434374232], 'coeff': (69.0, -6.996422594399698, 0.9709034007228218, 0.04075605632432042)},
        9 : {'above70K':False, 'boundary': [  152.08990434374232,    166.90080016951902], 'coeff': (61.0, -3.459361554206645, 0.20552366262672184, -0.005185654321098554)},
        10: {'above70K':False, 'boundary': [  166.90080016951902,    195.3079427383702 ], 'coeff': (38.0, -0.7325487027356796, 0.01299398006621569, -0.00011673918843419716)},
        11: {'above70K':False, 'boundary': [  195.3079427383702 ,    275.4114419501825 ], 'coeff': (25.0, -0.2605281681704082, 0.0022282978159015687, -8.616538071755353e-06)},
        12: {'above70K':False, 'boundary': [  275.4114419501825 ,    453.72525498106404], 'coeff': (14.0, -0.06518297122915089, 0.00025748929720128286, -4.5224409957563403e-07)},
        13: {'above70K':False, 'boundary': [  453.72525498106404,    817.5436713623418 ], 'coeff': (8.0, -0.015373704581517638, 2.8043857128286924e-05, -2.3231713819859912e-08)},
        14: {'above70K':False, 'boundary': [  817.5436713623418 ,   1998.6568610417357 ], 'coeff': (5.0, -0.0038667687689848936, 2.8542271727440443e-06, -8.585591732787398e-10)},
        15: {'above70K':False, 'boundary': [ 1998.6568610417357 ,   5433.732919117695  ], 'coeff': (3.0, -0.0006492945639255994, 1.6059978003971705e-07, -1.6398000404073262e-11)},
        16: {'above70K':False, 'boundary': [ 5433.732919117695  ,  18759.700620748117  ], 'coeff': (2.0, -0.00011146840690453101, 7.938633457490856e-09, -2.2156844989306396e-13)},
        17: {'above70K':False, 'boundary': [18759.700620748117  ,  60276.239081227555  ], 'coeff': (1.4, -1.5172329659141793e-05, 2.86508463044623e-10, -2.290840867286958e-15)},
        18: {'above70K':False, 'boundary': [60276.239081227555  ,ThermoHT_RvsT(1e0+dR_bnd)], 'coeff': (1.1, -2.598913621689561e-06, 5.380814434880268e-12, 1.0165656652245034e-16)},
    }
    # ---  --- #
    R_ = np.array(R, ndmin=1)
    T  = np.zeros(R_.shape)
    # --- Set out of range default values
    T[R_>ThermoHT_RvsT(1e+4)  ] += 1e4*above70K
    T[R_>ThermoHT_RvsT(1e0 )  ] += 1e-3*(not above70K)
    T[R_<ThermoHT_RvsT(T_thrs)]  = np.nan
    # --- Computing T from splines
    for spl_key in spln_dic:
        R_b     = spln_dic[spl_key]['boundary']
        a,b,c,d = spln_dic[spl_key]['coeff']
        # ---
        idx_g   = np.where(R_b[0]-dR_bnd<=R_)[0]
        idx_l   = np.where(R_<=R_b[1]+dR_bnd)[0]
        idx     = list(set(idx_g).intersection(set(idx_l)))
        # ---
        T[idx] += (a + b*(R_[idx]-R_b[0])**1 + c*(R_[idx]-R_b[0])**2 + d*(R_[idx]-R_b[0])**3) * int(spln_dic[spl_key]['above70K']==above70K)
    # ---  --- #
    return T[0] if T.size == 1 else T











# ====== old version ====== #

"""
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
"""

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
