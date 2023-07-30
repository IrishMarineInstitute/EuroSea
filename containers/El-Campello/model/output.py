from datetime import datetime
from pickle import dump
from json import dumps
from log import set_logger, now
import pytz

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

def send_output(FC, wave_rose_figure, wave_rose_series, wind_rose_figure, wind_rose_series, timezone):
    
    ''' Produce output PICKLE file to be sent to web app '''

    # Convert forecast times from UTC to local time
    wind_time_fc = [utc_to_local(i, timezone) for i in FC['wind_time_fc']]
    fc_sst_time       = [utc_to_local(i, timezone) for i in FC['sst'][0]]
    fc_wav_time     = [utc_to_local(i, timezone) for i in FC['Hs_fc'][0]]
    wave_rose_figure_idate = utc_to_local(wave_rose_figure['idate'], timezone).strftime('%Y-%b-%d %H:%M')
    wave_rose_figure_edate = utc_to_local(wave_rose_figure['edate'], timezone).strftime('%Y-%b-%d %H:%M')
    wave_rose_series_time = [utc_to_local(i, timezone) for i in wave_rose_series['time']]
    wind_rose_figure_idate = utc_to_local(wind_rose_figure['idate'], timezone).strftime('%Y-%b-%d %H:%M')
    wind_rose_figure_edate = utc_to_local(wind_rose_figure['edate'], timezone).strftime('%Y-%b-%d %H:%M')
    wind_rose_series_time = [utc_to_local(i, timezone) for i in wind_rose_series['time']]

    MODEL = {

        # Wind forecast
        'u_wind_fc': FC['u_wind_fc'],
        'v_wind_fc': FC['v_wind_fc'],
        'wind_time_fc': wind_time_fc,
        'wind_speed_fc': FC['wind_speed_fc'],
        
        # Temperature time
        'fc_sst_time': fc_sst_time,
        # Seawater temperature
        'fc_sst': FC['sst'][1],
 
        # Waves time     
        'fc_wav_time': fc_wav_time,
        # Significant Wave Height
        'fc_wav':      FC['Hs_fc'][1],
        # Secondary swell
        'fc_wav_sw2':      FC['Hs_sw2_fc'][1],
        
        # End time for waves
        'tw': FC['Hs_fc'][0][-1].strftime('%Y-%m-%d %H:%M'),
        # End time for temperature
        'tf': FC['sst'][0][-1].strftime('%Y-%m-%d %H:%M'),

        # Mean forecasted seawater temperature
        'mean_forecast_temperature': round(sum(FC['sst'][1])/len(FC['sst'][1]), 1),
        # Minimum forecasted seawater temperature
        'min_forecast_temperature': round(min(FC['sst'][1]), 1),
        # Maximum forecasted seawater temperature
        'max_forecast_temperature': round(max(FC['sst'][1]), 1),
        # Maximum forecasted significant wave height
        'forecast_max_swh': round(max(FC['Hs_fc'][1]), 2),
        # Maximum forecast secondary swell significant wave height
        'forecast_max_swh_sw2': round(max(FC['Hs_sw2_fc'][1]), 2),

        # Wind Wind Rose
        'fc_wind_rose_idate': wind_rose_figure_idate,
        'fc_wind_rose_edate': wind_rose_figure_edate,
        'fc_wind_rose':       wind_rose_figure['fig'],

        'fc_maximum_wind_speed': round(FC['maximum_wind_speed_fc'], 1),
        'associated_direction_wind': int(round(FC['associated_direction_wind'], 0)),

        'fc_wind_rose_time': wind_rose_series_time,
        'fc_wind_rose_period': wind_rose_series['speed'],
        'fc_wind_rose_direction': wind_rose_series['direction'],

         # Wave Wind Rose
        'fc_wave_rose_idate': wave_rose_figure_idate,
        'fc_wave_rose_edate': wave_rose_figure_edate, 
        'fc_wave_rose': wave_rose_figure['fig'],
 
        'shortest_period': round(FC['shortest_period'], 1),
        'associated_direction': int(round(FC['associated_direction'], 0)),
        
        'fc_wave_rose_time': wave_rose_series_time,
        'fc_wave_rose_period': wave_rose_series['period'],
        'fc_wave_rose_direction': wave_rose_series['direction'],
        }
   
    outfile = '/data/pkl/MODEL-2.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(MODEL), f)
