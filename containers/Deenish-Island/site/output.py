from pickle import dump
import pytz
from datetime import datetime
import sys
import os
from json import dumps
import numpy as np
from log import set_logger, now

logger = set_logger()

def jsonize(data):
    logger.info(f'{now()} OUTPUT: Starting JSONization of data dict')
    for k, v in data.items():
        if 'safe' in k: continue
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

def MHW():
    return 0

def transpose(DCP):
    arr = np.asarray(DCP)
    arr = arr.T
    return arr.tolist()

def utc_to_local(time, tz):
    ''' Convert UTC time to local time '''

    time = datetime(time.year, time.month, time.day, time.hour, time.minute, 0, 0, pytz.UTC)
    return time.astimezone(pytz.timezone(tz))
    

def send_output(sub, clim, surface_series, surface_fig, seabed_series, seabed_fig, timezone):
    
    try:
        # Get climatology
        time_c, seas, pc90 = clim
        # This is needed to jsonize the climatological time
        time_c = [datetime(i.year, i.month, i.day, i.hour).strftime('%Y-%m-%d %H:%M') for i in time_c]

        # Convert UTC time to local time 
        time = [utc_to_local(i, timezone) for i in sub.index]

        # Get time range
        t0, t1 = time[0], time[-1]

        # Determine first x-axis tick
        for i in time:
            if not i.hour and not i.minute:
                break
        tick0 = i.strftime('%Y-%m-%d')
    
        BUOY = {
            # Buoy time
            'time': time,
            'tick0': tick0,
            't0': t0.strftime('%Y-%m-%d %H:%M'),
            't1': t1.strftime('%Y-%m-%d %H:%M'),
    
            # in-situ time series data
            'temp': np.array(sub.get('temp')),
            'salt': np.array(sub.get('salt')),
            'pH':   np.array(sub.get('pH')),
            'O2':   np.array(sub.get('O2')),

            # y-axis limits for temperature
            'yaxismin': np.nanmin(np.array(sub.get('temp'))) - 0.1,
            'yaxismax': np.nanmax(np.array(sub.get('temp'))) + 0.1,
    
            'latest_temperature': round(sub.get('temp')[-1], 1),
            'latest_salinity': round(sub.get('salt')[-1], 1),
            'latest_pH': round(sub.get('pH')[-1], 2),
            'latest_oxygen': round(sub.get('O2')[-1], 1),

            'latest_surface_speed': round(sub.get('s-surface')[-1], 1),
            'latest_seabed_speed': round(sub.get('s-seabed')[-1], 1),
            'latest_surface_direction': round(sub.get('d-surface')[-1], 0),
            'latest_seabed_direction': round(sub.get('d-seabed')[-1], 0),

            # Local SST climatology
            'time_c': time_c,
            'seas': seas,
            'pc90': pc90,
    
            'MHW_Warning': MHW(),
    
            # These variables are used for the wind-rose for latest 24-hour surface currents
            'DCP_rose_idate_surface': utc_to_local(surface_fig['idate'], timezone).strftime('%Y-%b-%d %H:%M'), 
            'DCP_rose_edate_surface': utc_to_local(surface_fig['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'DCP_rose_surface':       surface_fig['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour surface currents 
            'DCP_rose_time_surface': [utc_to_local(i, timezone) for i in surface_series['time']], # time
            'DCP_rose_speed_surface': np.array(surface_series['speed']),                        # speed (cm/s)
            'DCP_rose_direction_surface': np.array(surface_series['direction']),                # direction (Deg.M)

            # These variables are used for the wind-rose for latest 24-hour seabed currents
            'DCP_rose_idate_seabed': utc_to_local(seabed_fig['idate'], timezone).strftime('%Y-%b-%d %H:%M'), 
            'DCP_rose_edate_seabed': utc_to_local(seabed_fig['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'DCP_rose_seabed':       seabed_fig['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour seabed currents 
            'DCP_rose_time_seabed': [utc_to_local(i, timezone) for i in seabed_series['time']], # time
            'DCP_rose_speed_seabed': np.array(seabed_series['speed']),                        # speed (cm/s)
            'DCP_rose_direction_seabed': np.array(seabed_series['direction']),                # direction (Deg.M)
            }

        outfile = '/data/pkl/BUOY-1.pkl'
        with open(outfile, 'wb') as f:
            dump(jsonize(BUOY), f)

    except Exception as err:
           exc_type, exc_obj, exc_tb = sys.exc_info()
           fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
           logger.info(f'ERROR MESSAGE: {str(err)}')
           logger.info(f'ERROR TYPE: {exc_type}') 
           logger.info(f'IN LINE: {exc_tb.tb_lineno}') 
