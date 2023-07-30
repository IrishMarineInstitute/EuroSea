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

def suboxic(o2):
    return 1 if o2 < 70 else 0

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
    

def send_output(sub, clim, DCPS, wind_rose_figure, wave_rose_figure, wave_rose_series,
    DCP_rose_figure_surface, DCP_rose_figure_seabed, DCP_rose_series_surface, DCP_rose_series_seabed,
    timezone): # 23-06-2023 The code now handles time zone transformations to display the time
                 # on the website in the right time zone. The time zone is specified by the user
                 # in the configuration file. Use strings as "Europe/Madrid" or "Europe/Dublin".
    
    try:
        ''' Produce output PICKLE file to be sent to web app '''
        # Get climatology
        time_c, seas, pc90 = clim
    
        # Convert UTC time to local time 
        sub['time'] = [utc_to_local(i, timezone) for i in sub['time']]

        # Get time ranges
        t0 = sub['time'][0]
        t1 = sub['time'][-1]

        # Determine first x-axis tick
        for i in sub['time']:
            if not i.hour and not i.minute:
                break
        tick0 = i.strftime('%Y-%m-%d')
    
        # Get wind direction as integer
        try:
            wind_direction = int(round(sub['Wind Direction'][-1], 0))
        except ValueError:
            wind_direction = np.nan
            
        # Get wave direction as integer
        try:
            wave_direction = int(round(sub['Wave Peak Direction'][-1], 0))
        except ValueError:
            wave_direction = np.nan

        # Get surface current direction as integer
        try:
            surface_current_direction = int(round(sub['DCP dir'][-1][0], 0))
        except ValueError:
            surface_current_direction = np.nan

        # Get 15-meter depth current direction as integer
        try:
            seabed_current_direction = int(round(sub['DCP dir'][-1][11], 0))
        except ValueError:
            seabed_current_direction = np.nan



        BUOY = {
            # Buoy time
            'time': sub['time'],
            'tick0': tick0,
            't0': t0.strftime('%Y-%m-%d %H:%M'),
            't1': t1.strftime('%Y-%m-%d %H:%M'),
    
    
            # DCPS depths [m]
            'DCPS': DCPS,
            
            # in-situ time series data
            'temp': sub['Temperature'],
            'TUR': sub['TUR'],
            'O2': sub['Oxygen Saturation'],
    
             # Wave data
            'Significant_Wave_Height_Hm0': sub['Significant Wave Height Hm0'],
            'Wave_Height_Swell_Hm0': sub['Wave Height Swell Hm0'],
    
            'maxTUR': max(sub['TUR']) + 1,
    
            'latest_temperature': round(sub['Temperature'][-1], 1),
    
            'latest_oxygen': round(sub['Oxygen Saturation'][-1], 1),
    
            'latest_TUR': round(sub['TUR'][-1], 1),
    
            'wind_speed_csv_export': sub['Wind Speed'],
            'wind_direction_csv_export': sub['Wind Direction'],
    
            'L_Wind_Speed': round(sub['Wind Speed'][-1], 1),
            'L_Wind_Direction': wind_direction,

            'wind_time_3h': sub['time_3h_series'],
            'wind_speed' : sub['wind_speed_3h_series'],
            'wind_direction': sub['wind_direction_3h_series'],
            'u-wind': sub['u-wind_3h_series'],
            'v-wind': sub['v-wind_3h_series'],
    
            'L_Significant_Wave_Height_Hm0': round(sub['Significant Wave Height Hm0'][-1], 2),
            'L_Wave_Peak_Direction': wave_direction,
            'L_Wave_Peak_Period': round(sub['Wave Peak Period'][-1], 1),
            'L_Wave_Height_Swell_Hm0': round(sub['Wave Height Swell Hm0'][-1], 2),
    
            'SubO2': suboxic(round(sub['Oxygen Saturation'][-1], 2)),
    
            # Local SST climatology
            'time_c': time_c,
            'seas': seas,
            'pc90': pc90,
    
            'MHW_Warning': MHW(),
    
            #'DCP_dir': sub['DCP dir'],
    
            'DCP_time': sub['time'][-144::],
            'DCP_speed': transpose(sub['DCP speed'][-144::]),

            # These variables are used for the wind-rose for latest 24-hour surface currents
            'DCP_rose_idate_surface': utc_to_local(DCP_rose_figure_surface['idate'], timezone).strftime('%Y-%b-%d %H:%M'), # The idate is used in the title
            'DCP_rose_edate_surface': utc_to_local(DCP_rose_figure_surface['edate'], timezone).strftime('%Y-%b-%d %H:%M'), # The edate is used in the title
            'DCP_rose_surface':       DCP_rose_figure_surface['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour surface currents 
            'DCP_rose_time_surface': [utc_to_local(i, timezone) for i in DCP_rose_series_surface['time']], # time
            'DCP_rose_speed_surface': DCP_rose_series_surface['speed'],                        # speed (cm/s)
            'DCP_rose_direction_surface': DCP_rose_series_surface['direction'],                # direction (Deg.M)

            # These provide the latest reading of surface current speed and direction
            'L_DCP_speed_surface': round(sub['DCP speed'][-1][0], 1),                          # speed (cm/s)
            'L_DCP_direction_surface': surface_current_direction,                              # direction (Deg.M)

    
            # These variables are used for the wind-rose for latest 24-hour seabed currents
            'DCP_rose_idate_seabed': utc_to_local(DCP_rose_figure_seabed['idate'], timezone).strftime('%Y-%b-%d %H:%M'), # The idate is used in the title
            'DCP_rose_edate_seabed': utc_to_local(DCP_rose_figure_seabed['edate'], timezone).strftime('%Y-%b-%d %H:%M'), # The edate is used in the title
            'DCP_rose_seabed':       DCP_rose_figure_seabed['fig'],   # This is a plotly.ex figure
            
            # These variables are used for the CSV export of latest 24-hour seabed currents 
            'DCP_rose_time_seabed': [utc_to_local(i, timezone) for i in DCP_rose_series_seabed['time']],  # time
            'DCP_rose_speed_seabed': DCP_rose_series_seabed['speed'],                        # speed (cm/s)
            'DCP_rose_direction_seabed': DCP_rose_series_seabed['direction'],                # direction (Deg.M)

            # These provide the latest reading of 15-meter depth current speed and direction
            'L_DCP_speed_seabed': round(sub['DCP speed'][-1][11], 1),                        # speed (cm/s)
            'L_DCP_direction_seabed': seabed_current_direction,                              # direction (Deg.M)


            'wind_rose_idate': utc_to_local(wind_rose_figure['idate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'wind_rose_edate': utc_to_local(wind_rose_figure['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'wind_rose': wind_rose_figure['fig'],
    
            'wave_rose_idate': utc_to_local(wave_rose_figure['idate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'wave_rose_edate': utc_to_local(wave_rose_figure['edate'], timezone).strftime('%Y-%b-%d %H:%M'),
            'wave_rose': wave_rose_figure['fig'],
    
            'wave_rose_time': [utc_to_local(i, timezone) for i in wave_rose_series['time']],
            'wave_rose_period': wave_rose_series['period'],
            'wave_rose_direction': wave_rose_series['direction'],
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
