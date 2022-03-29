from pony.orm import Database, Required, Optional, Json, LongStr, Set
from datetime import datetime

database = Database()
    
class Target(database.Entity):
    #   ----- Attributes -----

    target_name = Required(str, unique=True)  # Required: Cannot be None

    #   ----- Relations -----

    exposures = Set('Exposure')  # One target contains a set of exposures
    processed_exposure = Set('Processed_Exposure')

# Exposure table class
class Exposure(database.Entity):
    #   ----- Attributes -----

    observation_time = Required(datetime, unique=True)
    obs_id = Required(int, size=32, unsigned=True)
    insMode = Required(str)
    datacube_header = Optional(Json)
    raw_exposure_header = Optional(Json)
    raw_exposure_data = Optional(Json)
    raw_exposure_filename = Optional(str, unique=True)
    prm_filename = Optional(str, unique=True)
    pampelmuse_params = Optional(Json)
    sources = Optional(Json)
    pampelmuse_catalog = Optional(Json)
    raman_image_header = Optional(Json)
    maoppy_data = Optional(Json)

    #   ----- Sky parameters -----
    sky_condition_start_time = Optional(float)
    sky_condition_start = Optional(LongStr)
    sky_comment_start = Optional(LongStr)
    sky_condition_end_time = Optional(float)
    sky_condition_end = Optional(LongStr)
    sky_comment_end = Optional(LongStr)

    #   ----- Relations -----

    target = Required('Target')  # One exposure belongs to a target
    processed_exposure = Optional('Processed_Exposure')

class Processed_Exposure(database.Entity):
    observation_time = Required(datetime, unique=True)
    obs_id = Required(int, size=32, unsigned=True)
    insMode = Required(str)
    raw_filename = Optional(str, unique=True)
    # ------- Maybe some of those can be grouped in one field like atm params ------
    ngs_flux = Optional(float) # Not sure what data type it should be
    ttfree = Optional(bool)
    degraded = Optional(bool)
    glf = Optional(float)
    seeing = Optional(float)
    seeing_los = Optional(float)
    airMass = Optional(float)
    tau0 = Optional(float)
    # --------------------------------------------------------------
    num_sources = Optional(int, unsigned=True)
    sgs_data = Optional(Json) # sgs_data extension
    ag_data = Optional(Json) # ag_data extension
    sparta_cn2 = Optional(Json) # sparta_cn2 extension
    sparta_atm = Optional(Json) # sparta_atm extension
    psf_params = Optional(Json)
    sparta_iq_data = Optional(Json)
    sparta_iq_los_500nm = Optional(float)
    sparta_iq_los_500nm_nogain = Optional(float)
    
    # Relations
    
    target = Required('Target')  # One exposure belongs to a target
    exposure = Required('Exposure')

def create_conn(database, provider, host, user, passwd, db):
    #connect to the database
    database.bind(provider=provider, host=host, user=user, passwd=passwd, db=db)
    database.generate_mapping(create_tables = True)