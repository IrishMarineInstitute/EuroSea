from pickle import dump
from datetime import datetime
from json import dumps

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

def send_output(lon, lat, SST, coast):
    ''' Produce output PICKLE file to be sent to web app '''

    # Get SST
    lon_sst, lat_sst, time_sst, SST, ANOM, MHW = SST

    # Get oceancolour
    #lon_o, lat_o, time_o, CHL, CHL_ANOM = colour

    RS = {
        # Buoy coordinates
        'lon': lon, 'lat': lat,

        # Coastline
        'lon_coast': coast['lon_coast'],
        'lat_coast': coast['lat_coast'],

        # SST
        'lon_sst': lon_sst,
        'lat_sst': lat_sst,
        'time_sst': time_sst.strftime('%d-%b-%Y'),
        'SST': SST,
        'ANOM': ANOM,
        'MHW': MHW,

        # CHL
        #'lon_o': lon_o,
        #'lat_o': lat_o,
        #'time_o': time_o.strftime('%d-%b-%Y'),
        #'CHL': CHL,
        #'CHL_ANOM': CHL_ANOM,
        }

    return jsonize(RS)
