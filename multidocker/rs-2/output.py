from pickle import dump
from netCDF4 import Dataset, num2date
from datetime import datetime
from json import dumps
from log import set_logger, now

logger = set_logger()

def jsonize(data):
    logger.info(f'{now()} OUTPUT: Starting JSONization of data dict')
    for k, v in data.items():
        logger.info(f'   {now()} JSON {k}')
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
            else:
                logger.info(f'   {now()} WARNING: Could not jsonize {k} due to {str(ERR)}')
    return data

def send_output(lon, lat, SST, coast):
    ''' Produce output PICKLE file to be sent to web app '''

    # Get SST
    lon_sst, lat_sst, time_sst, SST, ANOM, MHW = SST

    # Get SST color range
    average = SST.mean()
    sst_colorange_min, sst_colorange_max = average - 2, average + 2

    ''' Read wave forecast ''' 
    with Dataset('/netcdf/waves/FORECAST/wave-forecast.nc', 'r') as nc:

        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)    

        # Read latitude and longitude
        latitude, longitude = nc.variables['latitude'][:], nc.variables['longitude'][:]

        # Read wave height 
        waves = nc.variables['VHM0'][:]

    time = [datetime(i.year, i.month, i.day, i.hour) for i in time]

    RS = {
        # Buoy coordinates
        'lon': lon, 'lat': lat,

        # Coastline
        'lon_coast': coast['lon_coast'],
        'lat_coast': coast['lat_coast'],
 
        # SST colorbar range
        'sst_colorange_min': sst_colorange_min,
        'sst_colorange_max': sst_colorange_max,

        # SST
        'lon_sst': lon_sst,
        'lat_sst': lat_sst,
        'time_sst': time_sst.strftime('%d-%b-%Y'),
        'SST': SST,
        'ANOM': ANOM,
        'MHW': MHW,

        # Waves
        'longitude': longitude, 
        'latitude': latitude,
        }

    for i in range(len(time)):
        RS['time_%03d' % i] = time[i].strftime('%Y-%b-%d %H:%M')
        RS['wave_%03d' % i] = waves[i, :, :]

    outfile = '/data/pkl/RS-2.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(RS), f)
