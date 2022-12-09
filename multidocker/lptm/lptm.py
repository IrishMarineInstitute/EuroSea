from opendrift.readers import reader_global_landmask
from opendrift.models.oceandrift import OceanDrift 
from opendrift.readers import reader_ROMS_native

from netCDF4 import Dataset, num2date
from datetime import date, datetime, timedelta
from pickle import dump
from json import dumps
import numpy as np

def configuration():
    ''' Read secrets (configuration) file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save as environment variable
            config[key] = val
    return config

def get_coordinate(key, config):
    s = key.upper()
    try:
        v = config[key]
        return float(v)
    except KeyError:
        raise KeyError(f'No value has been provided for {s} in config file. Aborting...')
    except ValueError:
        raise ValueError(f'''Wrong value {v} has been provided for {s} in config file.
            'Please, make sure that the value provded is a valid number''')

def get_boundaries(config):
    keys, vals = ('west', 'east', 'south', 'north'), []    
    for k in keys:
        vals.append(get_coordinate(k, config))
    return vals

def jsonize(data):
    for k, v in data.items():
        if isinstance(v, str): continue
        try:
            data[k] = dumps(v) 
        except TypeError as ERR:
            if str(ERR) == 'Object of type datetime is not JSON serializable':
                value = [i.strftime('%Y-%m-%d %H:%M') for i in v]
                data[k] = dumps(value)   
            elif str(ERR) == 'Object of type ndarray is not JSON serializable':
                data[k] = dumps(v.tolist())
            elif str(ERR) == 'Object of type MaskedArray is not JSON serializable':
                data[k] = dumps(v.tolist())
    return data

def opendrift_run():
    ''' Run particle-tracking model '''
    
    config = configuration()

    # Start landmask 
    landmask = reader_global_landmask.Reader() 
   
    # Longitude end points of transects
    x0 = [float(i) for i in config['x0'].split(',')]
    x1 = [float(i) for i in config['x1'].split(',')]
    
    # Longitude end points of transects
    y0 = [float(i) for i in config['y0'].split(',')]
    y1 = [float(i) for i in config['y1'].split(',')]
    
    # Number of transects
    nlines = len(x0)
    
    # Number of floats        
    N = int(config['N'])
    
    # Release drifters for today, from 00:00 to 00:00 (+1) 
    hoy = date.today(); Y, M, D = hoy.year, hoy.month, hoy.day
    idate = datetime(Y, M, D); edate = idate + timedelta(days=1)
    	
    # Time step        
    step = timedelta(minutes=3)
    
    # Output frequency    
    NHIS = 20
    
    # Input ocean file(s)           
    his = 'http://milas.marine.ie/thredds/dodsC/IMI_ROMS_HYDRO/NEATLANTIC_NATIVE_2KM_40L_1H/AGGREGATE'
           
    OD = OceanDrift(loglevel=20, logfile='/log/app.log')    
    # Initialize ocean reader 
    ocean = reader_ROMS_native.Reader(his)
  
    # Add readers 
    OD.add_reader([landmask, ocean])
    
    # Allow a stranded drifter to go back to the water 
    OD.set_config('general:coastline_action', 'previous')
    # Add diffusion
    OD.set_config('drift:horizontal_diffusivity', .01)
    # Limit drifter age to 3 days 
    OD.set_config('drift:max_age_seconds', 3*86400)
        
    # Seed elements 
    for i in range(nlines):
        idate = datetime(Y, M, D);
        while idate < edate:
            OD.seed_cone(lon=[x0[i], x1[i]], 
                         lat=[y0[i], y1[i]],         # Seed along transect
                         number=N,                   # Number of elements per minute
                         radius=[0, 0],              # Radius for dispersion around transect
                         time=idate)                 # Initial and end date for particle release 
                        
            idate += timedelta(seconds=600)
    
    # Run 
    OD.run(end_time=ocean.end_time,                # Run until the latest available oceanic forecast
          time_step=step,                          # Time step
          time_step_output=NHIS*step,              # Output frequency
          outfile='/netcdf/LPTM.nc',               # Output NetCDF file name
          export_variables=['lon', 'lat', 'time'], # Output variables
          export_buffer_length=10)                 # Synchronize output file every 10 records
    
    return '/netcdf/LPTM.nc', nlines

def density(f, nlines):    
    ''' Get density of particles '''
    
    config = configuration()
    
    # Number of floats per transect 
    n = 144 * int(config['N']) 
    
    # Get geographical boundaries from configuration file
    west, east, south, north = get_boundaries(config)    
  
    K = -1 

    with Dataset(f, 'r') as nc:    
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        
        # Get total number of particles
        N = len(nc.variables['trajectory'][:])
        
        assert ( not N % n )

        D = np.zeros((6, 2, N))
               
        for i, t in enumerate(time):  
            if i == 0: continue
            H = t.hour
            if H % 12: continue
            K += 1                      
            # Read longitude and latitude for i-th time step
            while 1:
                try:
                    lon_t, lat_t = nc.variables['lon'][:, i], nc.variables['lat'][:, i]; break
                except RuntimeError:
                    continue
                        
            D[K, 0, :], D[K, 1, :] = lon_t, lat_t

    time = time[12::12]
    time = [datetime(i.year, i.month, i.day, i.hour) for i in time]

    LPTM = {'W': west, 'E': east, 'S': south, 'N': north} # Map boundaries
    for j in range(nlines):
        for i in range(len(time)):
            LPTM['TIME_'    + '%02d' % (12 * (i + 1))] = time[i].strftime('%Y-%m-%d %H:%M')
            LPTM['LON_' + '%02d' % (12 * (i + 1)) + '_' + str(j+1)] = D[i, 0, j*n:(j+1)*n]
            LPTM['LAT_' + '%02d' % (12 * (i + 1)) + '_' + str(j+1)] = D[i, 1, j*n:(j+1)*n]

    outfile = '/data/pkl/LPTM.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(LPTM), f)
                
if __name__ == '__main__':
    # Run OpenDrift
    f, n = opendrift_run()
    # Prepare output to website
    density(f, n)
