import numpy as np
from astropy.time import Time
from astropy.coordinates import AltAz
from aomuse.constants import location

# Procedure to get the fwhm at an arbitrary wavelength including
# aberrations introduced by MUSE.
def fwhm_from500nm_to_l(fwhm, l, muse_aberr=False):
    """
    function to correct the seeing by
    wavelenght
    """
    
    # Note that for now we only add 0.3" in quadrature
    if muse_aberr:
        return np.sqrt((fwhm*(500.0/l)**0.2)**2 + 0.35**2)
    else:
        return fwhm*(500.0/l)**0.2
    
def get_sparta_iq_los(coords_J2000, sparta, mass_dimm_glf, no_ao_gain=False):
    """
    function to compute IQ from the LOS LGS telemetry
    """
    try:
        # Martinez, Kolb, Sarazin, Tokovinin (2010, The Messenger 141, 5) 
        # originally provided by Tokovinin (2002, PASP 114, 1156) but 
        # corrected by Kolb (ESO Technical Report #12)
        #
        # Note that we also have two sections that can be used to determine
        # the exact date and time of the telemetry data. Together with the
        # RA, Dec and coordinates of Paranal we can get the exact airmass
        # of eac measurement. The SPARTA QC0 script uses all this info.
    
        times_atmos = Time(sparta['Sec'], format='unix')
        times_atmos.format='isot'
        airmass_atmos = []
        for obstime in times_atmos:
            current_coords_altaz = coords_J2000.transform_to(\
                                AltAz(obstime=obstime,location=location))
            z_atmos = current_coords_altaz.zen
            airmass_atmos = np.append(airmass_atmos, 1/np.cos(z_atmos))

        airmass = np.nanmedian(airmass_atmos)
    
        L0 = (np.mean(sparta["LGS1_L0"]) + np.mean(sparta["LGS2_L0"]) + \
              np.mean(sparta["LGS3_L0"]) + np.mean(sparta["LGS4_L0"]))/4.0
        R0 = (np.mean(sparta["LGS1_R0"]) + np.mean(sparta["LGS2_R0"]) + \
              np.mean(sparta["LGS3_R0"]) + np.mean(sparta["LGS4_R0"]))/4.0
        sparta_glf = (np.nanmean(sparta["LGS1_TUR_GND"]) + np.nanmean(sparta["LGS2_TUR_GND"]) + \
              np.nanmean(sparta["LGS3_TUR_GND"]) + np.nanmean(sparta["LGS4_TUR_GND"]))/4.0
    
        Fkolb = 1.0/(300.0*8.0/L0) - 1.0
    
        # Note: The model sets FWHMatm=0 if the argument of the square root becomes 
        # negative [1+FKolb⋅2.183⋅(r0/L0)0.356]<0 , which happens when the Fried 
        # parameter r0 reaches its threshold of rt=L0⋅[1/(2.183⋅FKolb)]1/0.356. For the
        # VLT and L0=46m , this corresponds to rt=5.4m.
        #
        if 1+Fkolb*2.183*(R0/L0)**0.356 <= 0.0:
            Fcorr = 0.0
        else:
            Fcorr = np.sqrt(1+Fkolb*2.183*(R0/L0)**0.356)

        sparta_seeing = 1.028*np.rad2deg(500.0e-9/R0)*3600.0
        #sparta_seeing = (np.mean(sparta["LGS1_SEEING"]) + np.mean(sparta["LGS2_SEEING"]) + \
           #np.mean(sparta["LGS3_SEEING"]) + np.mean(sparta["LGS4_SEEING"]))/4.0

        if no_ao_gain:
            expected_ao_gain = 1.0
        else:
            #expected_ao_gain = polynomial_ao_gain(sparta_glf)
            expected_ao_gain = polynomial_ao_gain(mass_dimm_glf)
    
        # what is the LHSi_FWHM_GAIN? we do not use it in Milli's QC0 script
        # sparta_ao_gain = (np.mean(sparta['LGS1_FWHM_GAIN']) + np.mean(sparta['LGS2_FWHM_GAIN']) + \
        #       np.mean(sparta['LGS3_FWHM_GAIN']) + np.mean(sparta['LGS4_FWHM_GAIN']))/4.0

        # print('sparta_seeing: ', sparta_seeing, 'Fcorr: ', Fcorr, 'sparta_ao_gain: ', sparta_ao_gain)
        #
        # Note that airmass is not used. If observation has a large range of airmasses
        # the simle averaging that we are using is not good. The muse_sparta_qc0 script 
        # uses the time stamp and ra, dec to get airmass of each sampled point.
        # This should be reviewed.
        #
        sparta_iq_los =  sparta_seeing*Fcorr/expected_ao_gain
    except Exception as e:
        print(f"{e}")
        sparta_iq_los =  0.0
    
    return sparta_iq_los

# This is the AO gain implemented in the QC0 script and
# in OT. The ETC uses the mean value.
#
def polynomial_ao_gain(x):
    return 1.09 + 0.42*x -1.98*x**2 + 2.95*x**3