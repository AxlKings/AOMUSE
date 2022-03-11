from astropy import units as u
from astropy import coordinates

# Definition of the UT4 coordinates
latitude =  -24.6270*u.degree
longitude = -70.4040*u.degree  
altitude = 2648.0*u.meter 
location = coordinates.EarthLocation(lon=longitude,lat=latitude,height=altitude)