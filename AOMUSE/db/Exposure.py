from pony.orm import *

db = Database()    

# Exposure table class
class Exposure(db.Entity):
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
    psf_table = Optional(Json)
    pampelmuse_catalog = Optional(Json)
    raman_image_header = Optional(Json)

    #   ----- Sky parameters -----
    sky_condition_start_time = Optional(float)
    sky_condition_start = Optional(LongStr)
    sky_comment_start = Optional(LongStr)
    sky_condition_end_time = Optional(float)
    sky_condition_end = Optional(LongStr)
    sky_comment_end = Optional(LongStr)

    #   ----- Relations -----

    target = Required('Target')  # One exposure belongs to a target
    #processed_exposure = Optional('Processed_Exposure')