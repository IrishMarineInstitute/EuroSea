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

def utc_to_local(time, tz):
    ''' Convert UTC time to local time '''

    time = datetime(time.year, time.month, time.day, time.hour, time.minute, 0, 0, pytz.UTC)
    return time.astimezone(pytz.timezone(tz))

def send_output(sub, clim, timezone,
        surface_series, surface_fig,
        z15_series, z15_fig,
        wind_series, wind_fig,
        wave_series, wave_fig,
        wind3h):
    
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
            'swh': np.array(sub.get('wave-height')),
            'swell': np.array(sub.get('swell-height')),
            'temp': np.array(sub.get('temp')),
            'tur':   np.array(sub.get('tur')),
            'O2':   np.array(sub.get('O2')),
    
            'latest_swh': f'%.2f' % round(sub.get('wave-height')[-1], 2),
            'latest_swell': f'%.2f' % round(sub.get('swell-height')[-1], 2),
            'latest_temperature': round(sub.get('temp')[-1], 1),
            'latest_turbidity': round(sub.get('tur')[-1], 1),
            'latest_oxygen': round(sub.get('O2')[-1], 1),

            'latest_surface_speed': int(round(sub.get('s-surface')[-1], 0)),
            'latest_15m_speed': int(round(sub.get('s-15m')[-1], 0)),
            'latest_surface_direction': int(round(sub.get('d-surface')[-1], 0)),
            'latest_15m_direction': int(round(sub.get('d-15m')[-1], 0)),

            'latest_wind_speed': int(round(sub.get('s-wind')[-1], 0)),
            'latest_wind_direction': int(round(sub.get('d-wind')[-1], 0)),

            'latest_wave_period': int(round(sub.get('s-wave')[-1], 0)),
            'latest_wave_direction': int(round(sub.get('d-wave')[-1], 0)),

            # Local SST climatology
            'time_c': time_c,
            'seas': seas,
            'pc90': pc90,
    
            # These variables are used for the wind-rose for latest 24-hour surface currents
            'DCP_rose_idate_surface': utc_to_local(surface_fig['idate'], timezone).strftime('%Y-%b-%d %H:%M'), 
            'DCP_rose_edate_surface': utc_to_local(surface_fig['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'DCP_rose_surface':       surface_fig['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour surface currents 
            'DCP_rose_time_surface': [utc_to_local(i, timezone) for i in surface_series['time']], # time
            'DCP_rose_speed_surface': np.array(surface_series['speed']),                        # speed (cm/s)
            'DCP_rose_direction_surface': np.array(surface_series['direction']),                # direction (Deg.M)

            # These variables are used for the wind-rose for latest 24-hour seabed currents
            'DCP_rose_idate_seabed': utc_to_local(z15_fig['idate'], timezone).strftime('%Y-%b-%d %H:%M'), 
            'DCP_rose_edate_seabed': utc_to_local(z15_fig['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'DCP_rose_seabed':       z15_fig['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour 15-meter depth currents 
            'DCP_rose_time_seabed': [utc_to_local(i, timezone) for i in z15_series['time']], # time
            'DCP_rose_speed_seabed': np.array(z15_series['speed']),                        # speed (cm/s)
            'DCP_rose_direction_seabed': np.array(z15_series['direction']),                # direction (Deg.M)

            # These variables are used for the wind-rose for latest 24-hour winds
            'wind_rose_idate': utc_to_local(wind_fig['idate'], timezone).strftime('%Y-%b-%d %H:%M'), 
            'wind_rose_edate': utc_to_local(wind_fig['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'wind_rose':       wind_fig['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour winds 
            'wind_rose_time': [utc_to_local(i, timezone) for i in wind_series['time']], # time
            'wind_rose_speed': np.array(wind_series['speed']),                        # speed (cm/s)
            'wind_rose_direction': np.array(wind_series['direction']),                # direction (Deg.M)

            # These variables are used for the wind-rose for latest 24-hour waves
            'wave_rose_idate': utc_to_local(wave_fig['idate'], timezone).strftime('%Y-%b-%d %H:%M'), 
            'wave_rose_edate': utc_to_local(wave_fig['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'wave_rose':       wave_fig['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour waves 
            'wave_rose_time': [utc_to_local(i, timezone) for i in wave_series['time']], # time
            'wave_rose_period': np.array(wave_series['speed']),                        # speed (cm/s)
            'wave_rose_direction': np.array(wave_series['direction']),                # direction (Deg.M)

            }

        outfile = '/data/pkl/BUOY-2.pkl'
        with open(outfile, 'wb') as f:
            dump(jsonize(BUOY), f)

    except Exception as err:
           exc_type, exc_obj, exc_tb = sys.exc_info()
           fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
           logger.info(f'ERROR MESSAGE: {str(err)}')
           logger.info(f'ERROR TYPE: {exc_type}') 
           logger.info(f'IN LINE: {exc_tb.tb_lineno}') 
