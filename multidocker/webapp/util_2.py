from datetime import datetime, timedelta
from netCDF4 import MFDataset, num2date
from output_2 import send_output
from pickle import load
from pytz import timezone
from mhwfill import fill_mhw
from math import isnan
from glob import glob
import to_csv_func_2
import numpy as np
import vectors

def address_request(start, end, uv):
    ''' Subset in-situ data for the requested dates '''

    config = configuration()

    # Load historical buoy data
    f = '/data/buoy-2.pkl'
    with open(f, 'rb') as f:
        var = load(f)

    # Subset for the requested time period
    t0 = timezone('UTC').localize(datetime.strptime(start, '%Y-%m-%d'))
    t1 = timezone('UTC').localize(datetime.strptime(end,   '%Y-%m-%d'))
    if t0 > t1: 
        t0, t1 = t1, t0
        start, end = end, start
    t1 += timedelta(days=1)
    
    sub = subset(var, t0, t1)

    # Read climatology 
    clim = site_climatology(config['clim_site'], sub['time'])

    # Get MHW polygons
    MHW_times, MHW_temps = fill_mhw(sub['time'], sub['Temperature'], clim[0], clim[2])

    ''' Vectors '''
    vector =    {'Surface currents'   : 'surf',
                 'Mid-water currents' : 'mid',
                 'Seabed currents'    : 'seab'}
    D = {}

    date = timezone('UTC').localize(datetime.strptime(uv, '%Y-%m-%d'))
    for i in vector.keys():

        # Get vector data  
        var, u, v, t = vectors.vector_request(var, i, date) 

        if sum( [isnan(i) for i in u] ) == len(u): # No vector data
            vectores = 'false'; var, D, t = {}, {}, None; break
        else:
            vectores = 'true'

        # Get displacements
        D[vector[i] + '-x'], D[vector[i] + '-y'] = vectors.get_displacements(u, v, t, i)

        var.update(D)

        # Generate CSV
        to_csv_func_2.to_csv_uv_from_request(var, t, vector[i], start, end)
        

    ''' Temperature profiles '''
    try:
        # Get list of already downloaded TEMP3D NetCDF files
        files = sorted(glob('/data/pkl/TEMP3D-SITE2-*.nc'))    
        # Get file name of file matching requested start date
        file_start = '/data/pkl/TEMP3D-SITE2-' + start.replace('-', '') + '.nc'
        # Get file name of file matching requested end date
        file_end   = '/data/pkl/TEMP3D-SITE2-' + end.replace('-', '')   + '.nc'
        # Find indexes of required files
        index_start = files.index(file_start)
        index_end   = files.index(file_end) + 1
        # Subset list of file names for the requested period
        files = files[index_start : index_end]

        # Open aggregated NetCDF
        with MFDataset(files, aggdim='time') as nc:
            # Read time
            time = num2date(nc.variables['time'][:], nc.variables['time'].units) 
            # Read temperature profile
            temp = np.squeeze(nc.variables['thetao'][:])
        time = [datetime(i.year, i.month, i.day, i.hour) for i in time]

        # Generate CSV
        to_csv_func_2.to_csv_profile_from_request(time, temp, start, end)

        profile = 'true'

    except ValueError:
        # Well, NetCDF files may not have been downloaded yet. 
        # If so, don't plot the temperature profile.
        time, temp = [float('nan')], np.array([[float('nan')]])

        profile = 'false'


    ''' Output dictionary '''
    data = send_output(sub, var, D, clim, t, time, temp)        
    data['profile'] = profile
    data['vectores'] = vectores

    ''' Generate CSV files '''
    for i in ('temp', 'salt', 'tur', 'O2'):
        to_csv_func_2.to_csv_from_request(sub, i, start, end)

    return data, MHW_times, MHW_temps

def configuration():
    ''' Read secrets (configuration) file '''
    config = {}
    with open('config-2', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save as environment variable
            config[key] = val
    return config

def subset(buoy, t0, t1):
    ''' Subset buoy data for the requested time period '''
    
    # List of available times in the buoy dataset
    time = np.array(buoy['time'])
    
    # Find appropriate time indexes
    i0, i1 = np.argmin(abs(time - t0)), np.argmin(abs(time - t1)) + 1
    
    sub = {'time': buoy['time'][i0 : i1]}
    for i in buoy.keys():        
        # Subset each parameter for the requested time period
        sub[i] = buoy[i][i0 : i1]
        
    return sub

def site_climatology(infile, time):
    ''' Reads site climatology from local PICKLE file '''
    
    with open(infile, 'rb') as f:
        clim = load(f)
    
    t0, t1 = time[0] - timedelta(days=1), time[-1] + timedelta(days=8)
    
    time = []
    while t0 < t1:
        time.append(t0); t0 += timedelta(minutes=10)
    # Data from local climatology file    
    day_of_year, seasonal_cycle, PC90 = clim['time'], clim['seas'], clim['pc90']
    
    # Output initialization
    Time, Seas, Pc90 = [], [], []
    
    for t in time:        
        H, M = t.hour, t.minute            
        if H == 12 and not M:
            # Get day of year
            Day_Of_Year = t.timetuple().tm_yday
            # Find time index in local climatology file
            i = np.where(day_of_year == Day_Of_Year)[0][0]
            # Append to output arrays
            Time.append(t)
            Seas.append(seasonal_cycle[i])
            Pc90.append(PC90[i])
    
    return Time, Seas, Pc90

