from pony.orm import *
from aomuse.db.Exposure import Exposure
from aomuse.db.Target import Target

db = Database()  

#connect to the database
db.bind('mysql', host = '127.0.0.1', user = 'aomuse', passwd = '#aomuse2020', db = 'newaomuse')
#db.bind('mysql', host = '127.0.0.1', user = 'aomuse', passwd = '#aomuse2020', db = 'aomuse')
#db.bind('mysql', host = '127.0.0.1', user = 'thtkra', passwd = 'test1', db = 'MUSEDB2')
db.generate_mapping(create_tables = True)