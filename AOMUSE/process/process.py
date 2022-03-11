from pony.orm import *
from aomuse.db.Exposure import Exposure
from aomuse.db.Target import Target
from aomuse.db.Database import db
import pandas as pd
import json
from astropy import units as u
from astropy.coordinates import SkyCoord
from aomuse.utils.preprocess import get_sparta_iq_los, fwhm_from500nm_to_l
import numpy as np

exposures = select(e for e in Exposure)

dfExpos = {}
dfExpos['sparta_iq_los_500nm'] = []
dfExpos['sparta_iq_los_500nm_nogain'] = []
dfExpos['sparta_iq_data'] = []
dfExpos['psf_params'] = []
dfExpos['observation_time'] = []
dfExpos['obs_id'] = []
dfExpos['insMode'] = []
dfExpos['target'] = []
dfExpos['exposures'] = []
dfExpos['raw'] = []
dfExpos['ngs_flux'] = []
dfExpos['ttfree'] = []
dfExpos['degraded'] = []
dfExpos['glf'] = []
dfExpos['seeing'] = []
dfExpos['airMass'] = []
dfExpos['seeing_los'] = []
dfExpos['tau0'] = []
dfExpos['sources'] = []
dfExpos['sgs_data'] = []
dfExpos['ag_data'] = []
dfExpos['sparta_cn2'] = []
dfExpos['sparta_atm'] = []
#To count how many exposures have  a bad fit in them
parsNaN = 0
allStars = 0
for expo in exposures:
    #json return dictionaries
    #data contains the headers of different type of files (raw and reduced)
    try:
        primary = json.loads(expo.datacube_header)
    except Exception as e:
        #print(f"{e}")
        print("Exposure skipped")
        print("datacube_header =", expo.datacube_header, "(Probably empty string)")
        single_exposures_skipped += 1
        continue
        
    try:
        data = json.loads(expo.raw_exposure_data)
    except Exception as e:
        #print(f"{e}")
        print("Exposure skipped")
        print("raw_exposure_data =", expo.raw_exposure_data, "(Probably empty string)")
        raw_exposures_skipped += 1
        continue
    
    
    #stars contain the info of the sources used on the PampelMUSE fit
    try:
        stars = json.loads(expo.sources)
    except Exception as e:
        #print(f"{e}")
        print("Exposure skipped")
        print("sources =", expo.sources, "(Probably empty string)")
        stars_skipped += 1
        continue
    
    #psfparams has the PampelMUSE polyfit parameters
    psfParams = json.loads(expo.pampelmuse_params)
    dfPars = pd.DataFrame(psfParams)
    #check if all is good
    if(not(dfPars.isnull().values.any())):
        #filename
        dfExpos['observation_time'].append(expo.observation_time)
        dfExpos['obs_id'].append(expo.obs_id)
        dfExpos['insMode'].append(expo.insMode)
        dfExpos['target'].append(expo.target.target_name)
        dfExpos['exposures'].append(expo.prm_filename)
        dfExpos['raw'].append(expo.raw_exposure_filename)
        #print(len(stars))
        dfStars = {}
        for star in stars.items():
            dfStar = pd.DataFrame(star[1])
            if(not(dfStar.isnull().values.any())):
                dfStars[star[0]] = dfStar 
        if(dfStars == {}):
            #print(f"{expo.singleFile} bad sources")
            allStars += 1
            continue
        pars = star[1].keys()
        #ngs_flux is not available for WFM
        dfExpos['ngs_flux'].append(-1)
        
        # we check whether we are in tt free mode
        # HIERARCH ESO AOS TT LOOP ST = T / Tip-tilt loop status
        if not bool(primary['ESO AOS TT LOOP ST']):
            dfExpos['ttfree'].append(1)
        else:
            dfExpos['ttfree'].append(0)
            
        # We check weather we are in degraded mode
        # HIERARCH ESO AOS LGS1 DET GAIN = 100 / Detector gain of the LGSi
        # HIERARCH ESO LGS1 LASR1 OPMODE = 3 / Operational mode : Normal, Maintenance,Serv
        # HIERARCH ESO LGS1 LASR1 REPUMPER ST = T / True when the re-pumper is active.
        # HIERARCH ESO LGS1 LASR1 SWSIM = F / If T, function is software simulated.
        # HIERARCH ESO LGS1 LASR1 POWER = 22.321 / Laser power.
        # HIERARCH ESO LGS1 SHUT1 ST = T / Shutter open.
        #dfExpos['degraded'] = 0
        try:
            all_lasers_on = not bool(primary['ESO LGS1 LASR1 SWSIM']) and \
                            not bool(primary['ESO LGS2 LASR2 SWSIM']) and \
                            not bool(primary['ESO LGS3 LASR3 SWSIM']) and \
                            not bool(primary['ESO LGS4 LASR4 SWSIM'])
            if not all_lasers_on:
                dfExpos['degraded'].append(1)
            else:
                dfExpos['degraded'].append(0)
        except:
            dfExpos['degraded'].append(-1)
        #ground layer fraction
        mass_dimm_glf = primary['ESO OCS SGS ASM GL900 AVG']
        dfExpos["glf"].append(mass_dimm_glf)

        # Equatorial coordinates of the observation
        ra = primary['RA']*u.degree
        dec = primary['DEC']*u.degree
        coords_J2000 = SkyCoord(ra,dec)
        
        air_mass = (primary['ESO TEL AIRM START'] + primary['ESO TEL AIRM END'])/2.0
        dimm_seeing = (primary['ESO TEL AMBI FWHM START'] + primary['ESO TEL AMBI FWHM END'])/2.0
        dfExpos['seeing'].append(dimm_seeing)
        dfExpos['airMass'].append(air_mass)
        #correct seeing for airmass
        dfExpos['seeing_los'].append(dimm_seeing*air_mass**(3./5.))
    
        #coherence time
        dfExpos['tau0'].append(primary['ESO TEL AMBI TAU0'])
        
        #fwhm for different wavelenght ranges, i call them u,v and i just cause they go from blue to infrared
        
        #number of sources in the PPMUSE input catalogue
        dfExpos['sources'].append(len(stars))
        
        # Slow Guidance System, SGS, data
        dfExpos['sgs_data'].append(data['SGS_DATA'])
        
        # Telescope Guide probe data
        dfExpos['ag_data'].append(data['AG_DATA'])
    
        if 'SPARTA_CN2_DATA' in data and \
           'SPARTA_ATM_DATA' in data and \
            not bool(primary['ESO AOS TT LOOP ST']):
            sparta_iq_data = {}
            
            dfExpos['sparta_cn2'].append(data['SPARTA_CN2_DATA'])
            dfExpos['sparta_atm'].append(data['SPARTA_ATM_DATA'])

            # we add in quadrature the contributions of GALACSI and MUSE
            # For MUSE I use the IQ vs wavelength in the Performance Report 
            # which was better than the TLRs:
            # 0.37" for 480-600 nm
            # 0.29" for 600-800 nm
            # 0.29" for 800-930 nm
            #
            try:
                sparta_iq_los_500nm = get_sparta_iq_los(coords_J2000, data['SPARTA_ATM_DATA'], mass_dimm_glf)
                dfExpos['sparta_iq_los_500nm'].append(sparta_iq_los_500nm)
            except Exception as e:
                print(f"{e}")
                dfExpos['sparta_iq_los_500nm'].append(0.0)
            skip_i = []
            psf_params = {}
            
            wavelength = psfParams["wavelength"]
            windows = range(0, len(wavelength), int(len(wavelength)/10))
            key = f"wavelength_means"
            wavelength_means = []
            for i in range(len(windows)-1):
                if(wavelength[windows[i]] > 576 and wavelength[windows[i]] < 605 or wavelength[windows[i+1]] > 576 and wavelength[windows[i+1]] < 605):
                    skip_i.append(i)
                    continue
                mean = np.mean([wavelength[windows[i]], wavelength[windows[i+1]]])
                wavelength_means.append(mean)
            psf_params["wavelength"] = wavelength_means
            sparta_iq_data[key] = wavelength_means
            for par_name in psfParams.keys():
                if(par_name == "wavelength"):
                    continue
                param = psfParams[par_name]
                if(par_name not in dfExpos):
                    dfExpos[par_name] = []
                dfExpos[par_name].append(param)

                windows = range(0, len(param), int(len(param)/10))
                key = f"{par_name}_means"
                if(key not in dfExpos):
                    dfExpos[key] = []
                means = []
                for i in range(len(windows)-1):
                    if(i in skip_i):
                        continue
                    mean = np.mean([param[windows[i]], param[windows[i+1]]])
                    means.append(mean)
                psf_params[key] = means
            dfExpos['psf_params'].append(psf_params)
            ra = primary['RA']*u.degree
            dec = primary['DEC']*u.degree
            coords_J2000 = SkyCoord(ra,dec)
            mass_dimm_glf = primary['ESO OCS SGS ASM GL900 AVG']
            sparta_iq_los_500nm = get_sparta_iq_los(coords_J2000, data['SPARTA_ATM_DATA'], mass_dimm_glf)
            sparta_iq_los_500nm_nogain = get_sparta_iq_los(coords_J2000, data['SPARTA_ATM_DATA'], mass_dimm_glf, True)
            dfExpos['sparta_iq_los_500nm'].append(sparta_iq_los_500nm)
            dfExpos['sparta_iq_los_500nm_nogain'].append(sparta_iq_los_500nm_nogain)
            l = []
            l_nogain = []
            for wavelength in wavelength_means:
                l.append(fwhm_from500nm_to_l(sparta_iq_los_500nm, wavelength, True))
                l_nogain.append(fwhm_from500nm_to_l(sparta_iq_los_500nm_nogain, wavelength, True))
            sparta_iq_data["sparta_iq_l"] = l
            sparta_iq_data["sparta_iq_l_nogain"] = l_nogain
            dfExpos['sparta_iq_data'].append(sparta_iq_data)
        else:
            dfExpos['sparta_cn2'].append(None)
            dfExpos['sparta_atm'].append(None)
            dfExpos['psf_params'].append(None)

            dfExpos['sparta_iq_los_500nm'].append(None)
            dfExpos['sparta_iq_los_500nm_nogain'].append(None)
            dfExpos['sparta_iq_data'].append(None)