from ecmwf.opendata import Client
from datetime import datetime, timedelta
from get_direction import get_direction
import pygrib
from pprint import pformat
import numpy as np
import re
import os

def get_ecmwf_time(grb):
    ''' Get datetime from GRIB layer '''
    
    abc = pformat(grb); numbers = re.findall('[0-9]+', abc)[-2:]
    # Base time is the last number in the string
    time = datetime.strptime(numbers[1], '%Y%m%d%H%M')
    # Hours since base time is the second-to-last number in the string
    delta = timedelta(hours=int(numbers[0]))
    # Return time for this layer
    return time + delta    

def ECMWF(config):
    
    outdir = '/data/ECMWF/'
    if not ( os.path.isdir(outdir) ):
        os.mkdir(outdir)
    target = '/data/ECMWF/data.grib2'
            
    client = Client()
    # Download ECMWF winds for three days
    client.retrieve(param=["10u", "10v"], 
                    target=target, 
                    step=[i for i in range(0, 75, 3)])

   # Open GRIB2 file
    grbs = pygrib.open(target)
    
    grbs.seek(0)
       
    # Get u
    U10 = grbs.select(name='10 metre U wind component')
    
    # Get v
    V10 = grbs.select(name='10 metre V wind component')
        
    # Get mooring coordinates from configuration file
    lon, lat = float(config['lon']), float(config['lat'])
    
    # Output initialization
    U, V, time = [], [], []
    
    for u, v in zip(U10, V10):
        # Get time for this layer
        u_time, v_time = get_ecmwf_time(u), get_ecmwf_time(v)
        # Check both times are the same
        try:
            assert(u_time == v_time)
        except AssertionError:
            raise RuntimeError('ECMWF (u, v) wind components: times do not match!')
        time.append(u_time)
            
        # Get data from layer
        u_field, y, x = u.data()
        v_field, y, x = v.data()
        
        # Get indexes in ECMWF grid nearest to mooring
        x = x[0, :]; idx = nearest(x, lon)        
        y = y[:, 0]; idy = nearest(y, lat)
        
        # Convert from m/s to km/h
        U.append(3.6*u_field[idy, idx])
        V.append(3.6*v_field[idy, idx])

    # Calculate speed
    speed = [(u**2 + v**2)**.5 for u, v in zip(U, V)]
    # Calculate direction
    direction = [get_direction(u, v, 'FROM') for u, v in zip(U, V)]
        
    return U, V, time, speed, direction

def nearest(lista, valor):
    return np.argmin(abs(lista - valor))
