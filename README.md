<h1 align="center">AO Muse</h1>

<p align="center">
    <em>
        AO Muse package
    </em>
</p>

> Axel Iván Reyes Orellana

This package allows the connection with a database of exposures to easy retrieval and processing.

# Contents
- [Installation](https://github.com/AxlKings/AOMUSE#installation)
- [Requirements](https://github.com/AxlKings/AOMUSE#requirements)
- [Before use](https://github.com/AxlKings/AOMUSE#before-execute)
- [Data Structure](https://github.com/AxlKings/AOMUSE#data-structure)
- [How to use](https://github.com/AxlKings/AOMUSE#how-to-use)
  - [Imports](https://github.com/AxlKings/AOMUSE#imports)
  - [Methods](https://github.com/AxlKings/AOMUSE#methods)

# Installation

Install using `pip`!

```sh
$ pip install aomuse
```
  
# Requirements
To use the package you need a database where your exposure data is stored, for example MariaDB:
- [MariaDB](https://mariadb.org/)

AO Muse library uses the following packages: 
- [PonyORM](https://ponyorm.org/)
- [PyMySQL](https://pymysql.readthedocs.io/en/latest/)
- [NumPy](https://numpy.org/)
- [Pandas](https://pandas.pydata.org)
- [AstroPy](https://www.astropy.org/)
- [Json](https://docs.python.org/3/library/json.html)


*For better understanding, the terms that are enclosed in curly brackets must be replaced with their corresponding values.*
# Before use

Before use its necessary a database where your exposure data is stored. If you have one already, you can skip this section.

For this tutorial, we will use a MariaDB database.

You will need the name of the DB, username and password for the connection.

To create the database you have to login first (you can do it as root):
```
mysql -u {user_name} -p 
```
Then you have to create an empty database:
```sql
CREATE DATABASE {database_name}; 
```
Create an user of the database:
```sql
CREATE USER '{username}'@'localhost' IDENTIFIED BY '{password}';
```
And finally grant privileges to the database user:
```sql
GRANT ALL PRIVILEGES ON {database_name}.* TO '{username}'@'localhost';
```

# Data Structure

The following code cells define the structure of the database entities (Targets, Exposures and Processed Exposures) and how Pony map the classes with the tables. This structure is mandatory to use the AO Muse Package.
```python
from pony.orm import *
```
```python
# Create a database object from Pony
db = Database()

# The classes inherit db.Entity from Pony
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
    processed_exposure = Optional('Processed_Exposure')

class Processed_Exposure(database.Entity):
    observation_time = Required(datetime, unique=True)
    obs_id = Required(int, size=32, unsigned=True)
    insMode = Required(str)
    raw_filename = Optional(str, unique=True)

    ngs_flux = Optional(float)
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
```

# How to use

## Imports

In order to use the package, you have to import the database object.

```python
from AOMUSE.db.Database import database
```

Then, define the following parameters to stablish the connection with the database.

```python
db_data = {
    "provider":{provider},
    "host":{ip}, 
    "user":{db_admin_username}, 
    "passwd":{db_admin_password}, 
    "db":{db_name}
}
```

If you are using MariaDB and localhost, then provider has to be "mysql" and host "127.0.0.1".

Now, you can stablish the connection creating an instance of muse_db class provided by the AO Muse Package, which receive the database imported earlier and the previous database parameters.

```python
from AOMUSE.ao.muse_db import muse_db
aomuse_db = muse_db(database, **db_data)
```

## Methods

The package also offers the following methods which process exposures data or returns a Pandas DataFrame with their corresponding data.

### muse_db.process()

Process and store all the exposures stored in the database. If processed data existed previosly, it is deleted first.

```python
aomuse_db.process()
```

### muse_db.get_exposures()

Return a DataFrame containing the metadata of the exposures and their corresponding exposure and processed exposure objects.

```python
exposures = aomuse_db.get_exposures()
exposures
```
<img src=https://media.discordapp.net/attachments/957192747620659250/957192761491193866/unknown.png>

### muse_db.get_processed_exposures()

Return a DataFrame containing the metadata of the processed exposures and their corresponding exposure and processed exposure objects.

```python
processed_exposures = aomuse_db.get_processed_exposures()
processed_exposures
```
<img src=https://media.discordapp.net/attachments/957192747620659250/957193210072019034/unknown.png>

### muse_db.get_processed_data()

Return a DataFrame containing some metadata and the processed data of exposures that are not tables or Jsons.

```python
processed_data = aomuse_db.get_processed_data()
processed_data
```
<img src=https://media.discordapp.net/attachments/957192747620659250/957193388975869992/unknown.png>

### muse_db.get_processed_data()

Return a DataFrame containing some metadata and the processed data of exposures that are tables or Jsons.

```python
processed_tables = aomuse_db.get_processed_tables()
processed_tables
```
<img src=https://media.discordapp.net/attachments/957192747620659250/957193565811920916/unknown.png>