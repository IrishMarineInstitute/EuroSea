from datetime import datetime, timedelta
from netCDF4 import Dataset, num2date
from slider import Slider
from math import nan
import numpy as np
import pickle
import json

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

def get_ostia_times():
    ''' Get list of available times in SST database for the calendar widgets '''

    config = configuration()

    # Local historical database and climatology
    dataset = config.get('sstnc')

    with Dataset(dataset, 'r') as nc:
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        # Conver to datetime 
        time = [datetime(i.year, i.month, i.day) for i in time]

    return time[-1].strftime('%Y-%m-%d'), time

def OSTIA(date, request):
    ''' Read SST local database for user-selected date '''
    datestr=date
    date = datetime.strptime(date, '%Y-%m-%d')

    config = configuration()

    if not request == 'sst':
        # Read climatology
        clim  = climatology(config.get('climnc'))

    with Dataset(config.get('sstnc'), 'r') as nc:
        # Read coordinates
        lon, lat = nc.variables['longitude'][:], nc.variables['latitude'][:]
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        # Convert time to datetime
        time = np.array([datetime(i.year, i.month, i.day) for i in time])
        # Find time index of requested date
        w = np.argmin(abs(time - date))
        if not np.equal(time[w], date):
            raise RuntimeError(f'Could not find requested date in SST database {datestr}')

        # Read SST for requested date. Convert to Celsius
        SST = nc.variables['analysed_sst'][w, :, :] - 273.15

        if request == 'mhw':
            sstmhw = nc.variables['analysed_sst'][w-4:w+1, :, :] - 273.15

    SST = SST.filled(nan)

    if not request == 'sst':
        # Calculate SST anomalies
        ANM = Anomalies(date, SST, clim)

    if request == 'mhw':
        # Get Marine Heat Wave intensity
        marineHeatWaves = MarineHeatWaves(date, clim, sstmhw, ANM)

    # Fix data type
    lon, lat = np.round(lon.astype(np.float64), 3), np.round(lat.astype(np.float64), 3)
    SST = np.round(SST.astype(np.float64), 1)

    # Get buoy locations
    x_buoy, y_buoy = json.loads(config['lon']), json.loads(config['lat'])

    # Read coastline
    with open(config['coastfile'], 'rb') as f:
        coast = pickle.load(f)
        x_coast, y_coast = coast['longitude'], coast['latitude']

    # Read contour
    with open(config['bathymetry'], 'rb') as f:
        bathymetry = pickle.load(f)
        x_bathy, y_bathy = bathymetry['longitude'], bathymetry['latitude']

    if request == 'sst':
        colorscale = 'Portland'
        tickvals = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        contours=dict(start=8, end=20, size=1)
        fig = Slider(lon, lat, date, SST, (x_coast, y_coast), (x_buoy, y_buoy),
            (x_bathy, y_bathy), colorscale, tickvals, contours)

    elif request == 'anm':
        colorscale = 'RdBu_r'
        tickvals = [-3, -2, -1, 0, 1, 2, 3]
        contours=dict(start=-3, end=3, size=.25)
        fig = Slider(lon, lat, date, ANM, (x_coast, y_coast), (x_buoy, y_buoy),
            (x_bathy, y_bathy), colorscale, tickvals, contours)

    elif request == 'mhw':
        colorscale = 'Reds'
        tickvals = [0, 1, 2, 3]
        contours=dict(start=0, end=3, size=.25)
        fig = Slider(lon, lat, date, marineHeatWaves, (x_coast, y_coast), (x_buoy, y_buoy),
            (x_bathy, y_bathy), colorscale, tickvals, contours)

    return fig, time.tolist()
    
def climatology(file):
    ''' Read climatology from NetCDF file '''
       
    with Dataset(file, 'r') as nc:
        time = nc.variables['time'][:]
        # Read seasonal cycle (climatology)
        seas = nc.variables['seas'][:]
        # Read 90-th percentile (MHW threshold)
        pc90 = nc.variables['PCT90'][:]

    return time, seas, pc90

def Anomalies(t, sst, clim):
    ''' Calculate sea surface temperature anomalies '''

    time_c, seas, pc90 = clim # Climatology

    DOY = min(t.timetuple().tm_yday, 365) # Get day of year

    i = np.where(time_c == DOY)[0][0] # Time index in climatology

    ANM = sst - seas[i, :, :] # Calculate anomaly

    return np.round(ANM.astype(np.float64), 1)

def MarineHeatWaves(t, clm, SST, ANM):
    
    time_c, seas, pc90 = clm # Climatology
    # Mask land masses
    SST = SST.filled(nan)

    for i in range(5):
        j = i + 1
        # Check temperature j days before 
        sst = SST[-j, :, :]
        # Get date i days ago
        time = t - timedelta(days=i)
        # Get day of year...
        DOY = min(time.timetuple().tm_yday, 365)
        # ... to know time index in climatlogy...
        idx = np.where(time_c == DOY)[0][0]
        # ... and compare temperature against PCT.90
        w = sst > pc90[idx, :, :]
        # Mask anomalies where SST is below PCT. 90 (no MHW) 
        ANM[w == 0] = np.nan
    
    ANM[np.isnan(ANM)] = 0.0 

    return np.round(ANM.astype(np.float64), 1)
