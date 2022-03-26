from pony.orm import *
from AOMUSE.db.Database import Exposure, Processed_Exposure, create_conn
import pandas as pd
import json
from astropy import units as u
from astropy.coordinates import SkyCoord
from AOMUSE.utils.preprocess import get_sparta_iq_los, fwhm_from500nm_to_l
import numpy as np

class muse_db():

    def __init__(self, database, provider, host, user, passwd, db):
        create_conn(database, provider=provider, host=host, user=user, passwd=passwd, db=db)

    def process(self):
        pes = select(pe for pe in Processed_Exposure)
        pes.delete()
        exposures = select(e for e in Exposure)

        #To count how many exposures have  a bad fit in them
        allStars = 0
        for expo in exposures:
            dfExpos = {}
            #json return dictionaries
            #data contains the headers of different type of files (raw and reduced)
            try:
                primary = json.loads(expo.datacube_header)
            except Exception as e:
                print("Exposure skipped")
                print("datacube_header =", expo.datacube_header, "(Probably empty string)")
                single_exposures_skipped += 1
                continue
                
            try:
                data = json.loads(expo.raw_exposure_data)
            except Exception as e:
                print("Exposure skipped")
                print("raw_exposure_data =", expo.raw_exposure_data, "(Probably empty string)")
                raw_exposures_skipped += 1
                continue
            
            
            #stars contain the info of the sources used on the PampelMUSE fit
            try:
                stars = json.loads(expo.sources)
            except Exception as e:
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
                dfExpos['observation_time'] = expo.observation_time
                dfExpos['obs_id'] = expo.obs_id
                dfExpos['insMode'] = expo.insMode
                dfExpos['target'] = expo.target
                dfExpos['exposure'] = expo
                dfExpos['raw_filename'] = expo.raw_exposure_filename
                dfStars = {}
                for star in stars.items():
                    dfStar = pd.DataFrame(star[1])
                    if(not(dfStar.isnull().values.any())):
                        dfStars[star[0]] = dfStar 
                if(dfStars == {}):
                    allStars += 1
                    continue
                #ngs_flux is not available for WFM
                dfExpos['ngs_flux'] = -1
                
                # we check whether we are in tt free mode
                # HIERARCH ESO AOS TT LOOP ST = T / Tip-tilt loop status
                if not bool(primary['ESO AOS TT LOOP ST']):
                    dfExpos['ttfree'] = 1
                else:
                    dfExpos['ttfree'] = 0
                try:
                    all_lasers_on = not bool(primary['ESO LGS1 LASR1 SWSIM']) and \
                                    not bool(primary['ESO LGS2 LASR2 SWSIM']) and \
                                    not bool(primary['ESO LGS3 LASR3 SWSIM']) and \
                                    not bool(primary['ESO LGS4 LASR4 SWSIM'])
                    if not all_lasers_on:
                        dfExpos['degraded'] = 1
                    else:
                        dfExpos['degraded'] = 0
                except:
                    dfExpos['degraded'] = -1
                #ground layer fraction
                mass_dimm_glf = primary['ESO OCS SGS ASM GL900 AVG']
                dfExpos["glf"] = mass_dimm_glf

                # Equatorial coordinates of the observation
                ra = primary['RA']*u.degree
                dec = primary['DEC']*u.degree
                coords_J2000 = SkyCoord(ra,dec)
                
                air_mass = (primary['ESO TEL AIRM START'] + primary['ESO TEL AIRM END'])/2.0
                dimm_seeing = (primary['ESO TEL AMBI FWHM START'] + primary['ESO TEL AMBI FWHM END'])/2.0
                dfExpos['seeing'] = dimm_seeing
                dfExpos['airMass'] = air_mass
                #correct seeing for airmass
                dfExpos['seeing_los'] = dimm_seeing*air_mass**(3./5.)
            
                #coherence time
                dfExpos['tau0'] = primary['ESO TEL AMBI TAU0']
                
                #fwhm for different wavelenght ranges, i call them u,v and i just cause they go from blue to infrared
                
                #number of sources in the PPMUSE input catalogue
                dfExpos['num_sources'] = len(stars)
                
                # Slow Guidance System, SGS, data
                dfExpos['sgs_data'] = data['SGS_DATA']
                
                # Telescope Guide probe data
                dfExpos['ag_data'] = data['AG_DATA']
            
                if 'SPARTA_CN2_DATA' in data and \
                'SPARTA_ATM_DATA' in data and \
                    not bool(primary['ESO AOS TT LOOP ST']):
                    sparta_iq_data = {}
                    
                    dfExpos['sparta_cn2'] = data['SPARTA_CN2_DATA']
                    dfExpos['sparta_atm'] = data['SPARTA_ATM_DATA']

                    # we add in quadrature the contributions of GALACSI and MUSE
                    # For MUSE I use the IQ vs wavelength in the Performance Report 
                    # which was better than the TLRs:
                    # 0.37" for 480-600 nm
                    # 0.29" for 600-800 nm
                    # 0.29" for 800-930 nm
                    #
                    try:
                        sparta_iq_los_500nm = get_sparta_iq_los(coords_J2000, data['SPARTA_ATM_DATA'], mass_dimm_glf)
                        dfExpos['sparta_iq_los_500nm'] = sparta_iq_los_500nm
                    except Exception as e:
                        print(f"{e}")
                        dfExpos['sparta_iq_los_500nm'] = 0.0
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

                        windows = range(0, len(param), int(len(param)/10))
                        key = f"{par_name}_means"
                        means = []
                        for i in range(len(windows)-1):
                            if(i in skip_i):
                                continue
                            mean = np.mean([param[windows[i]], param[windows[i+1]]])
                            means.append(mean)
                        psf_params[key] = means
                    dfExpos['psf_params'] = psf_params
                    ra = primary['RA']*u.degree
                    dec = primary['DEC']*u.degree
                    coords_J2000 = SkyCoord(ra,dec)
                    mass_dimm_glf = primary['ESO OCS SGS ASM GL900 AVG']
                    sparta_iq_los_500nm = get_sparta_iq_los(coords_J2000, data['SPARTA_ATM_DATA'], mass_dimm_glf)
                    sparta_iq_los_500nm_nogain = get_sparta_iq_los(coords_J2000, data['SPARTA_ATM_DATA'], mass_dimm_glf, True)
                    dfExpos['sparta_iq_los_500nm'] = sparta_iq_los_500nm
                    dfExpos['sparta_iq_los_500nm_nogain'] = sparta_iq_los_500nm_nogain
                    l = []
                    l_nogain = []
                    for wavelength in wavelength_means:
                        l.append(fwhm_from500nm_to_l(sparta_iq_los_500nm, wavelength, True))
                        l_nogain.append(fwhm_from500nm_to_l(sparta_iq_los_500nm_nogain, wavelength, True))
                    sparta_iq_data["sparta_iq_l"] = l
                    sparta_iq_data["sparta_iq_l_nogain"] = l_nogain
                    dfExpos['sparta_iq_data'] = sparta_iq_data
                keys = []
                for key, value in dfExpos.items():
                    if(value is None):
                        keys.append(key)
                for key in keys:
                    del dfExpos[key]
                Processed_Exposure(**dfExpos)

    def get_exposures(self):
        es = select(e for e in Exposure)
        data = []
        columns = [
            "observation_time", "target", "obs_id", "insMode", 
            "raw_filename", "prm_filename", 
            "exposure", "processed_exposure"
        ]
        for e in es:
            data.append([e.observation_time, e.target.target_name, e.obs_id, e.insMode, 
                        e.raw_exposure_filename, e.prm_filename, 
                        e, e.processed_exposure
                        ])
        df = pd.DataFrame(data, columns=columns)
        return df

    def get_processed_exposures(self):
        pes = select(pe for pe in Processed_Exposure)
        data = []
        columns = [
            "observation_time", "target", "obs_id", "insMode", 
            "raw_filename", "exposure", "processed_exposure"
        ]
        for pe in pes:
            data.append([pe.observation_time, pe.target.target_name, pe.obs_id, pe.insMode, 
                        pe.raw_filename, pe.exposure, pe
                        ])
        df = pd.DataFrame(data, columns=columns)
        return df

    def get_processed_data(self):
        pes = select(pe for pe in Processed_Exposure)
        data = []
        columns = [
            "observation_time", "obs_id", "insMode", "raw_filename",
            "ngs_flux", "ttfree", "degraded", "glf", "seeing",
            "seeing_los", "airMass", "tau0", "num_sources",
            "sparta_iq_los_500nm", "sparta_iq_los_500nm_nogain"
        ]
        for pe in pes:
            data.append([pe.observation_time, pe.obs_id, pe.insMode, pe.raw_filename,
                        pe.ngs_flux, pe.ttfree, pe.degraded, pe.glf, pe.seeing,
                        pe.seeing_los, pe.airMass, pe.tau0, pe.num_sources,
                        pe.sparta_iq_los_500nm, pe.sparta_iq_los_500nm_nogain
                        ])
        df = pd.DataFrame(data, columns=columns)
        return df

    def get_processed_tables(self):
        pes = select(pe for pe in Processed_Exposure)
        tables = []
        columns = ["observation_time", "target", "obs_id", "insMode", 
            "sgs_data", "ag_data", "sparta_cn2", "sparta_atm", "psf_params", "sparta_iq_data"]

        for pe in pes:
            sgs_data = pd.DataFrame(pe.sgs_data)
            ag_data = pd.DataFrame(pe.ag_data)
            sparta_cn2 = pd.DataFrame(pe.sparta_cn2)
            sparta_atm = pd.DataFrame(pe.sparta_atm)
            psf_params = pd.DataFrame(pe.psf_params)
            sparta_iq_data = pd.DataFrame(pe.sparta_iq_data)
            tables.append([pe.observation_time, pe.target.target_name, pe.obs_id, pe.insMode, 
                        sgs_data, ag_data, sparta_cn2, sparta_atm, psf_params, sparta_iq_data])
        df = pd.DataFrame(tables, columns=columns)
        return df

    