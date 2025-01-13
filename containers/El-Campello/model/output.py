from datetime import datetime
from pickle import dump
from json import dumps
from log import set_logger, now
import numpy as np
import pandas as pd
import pytz

logger = set_logger()

def dates_in_table(time):    
    ''' Return the dates existing in list TIME (both in English and Spanish)
        and the number of times each date appears in the list '''  
        
    # Convert dates to format Weekday Day Month
    dates = np.array([i.strftime('%a %d %B') for i in time])
    
    # Get a list of the dates existing in list
    EN = pd.unique(dates).tolist()
    
    # Find out how many times each date exists in list
    C = [np.count_nonzero(dates==i) for i in EN]; C = [str(i) for i in C]
    
    # Translate to Spanish    
    translator = {'Mon': 'Lunes', 'Tue': 'Martes', 'Wed': 'Miércoles', 'Thu': 'Jueves',
                'Fri': 'Viernes', 'Sat': 'Sábado', 'Sun': 'Domingo', 'January': 'Enero',
                'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril', 'May': 'Mayo',
                'June': 'Junio', 'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'}
    
    ES = []
    for i in EN:
        for word in translator.items():
            en, es = word[0], word[1]
            i = i.replace(en, es)
        ES.append(i)
        
    return EN, ES, C

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
        
        # Waves time     
        'fc_wav_time': fc_wav_time,
        # Significant Wave Height
        'fc_wav':      FC['Hs_fc'][1],
        # Secondary swell
        'fc_wav_sw2':      FC['Hs_sw2_fc'][1],
        
        # End time for waves
        'tw': FC['Hs_fc'][0][-1].strftime('%Y-%m-%d %H:%M'),

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
   
    MODEL = jsonize(MODEL)
    
    # Update September 2023. Add forecast time and Significant Wave
    # Height as lists (no JSON) for the scrollable table.
    items = []; dates = []

    for i, j in zip(fc_wav_time, FC['Hs_fc'][1]):

        # Set warning color
        if j > 3:
            color = '#FF0000' # Red warning 
        elif j > 2:
            color = '#FC6A03' # Orange warning 
        elif j > 0:
            color = '#39E75F' # No warning
        else:
            color = '#9E9E9E' # No data

        items.append( dict(time=i.strftime('%H:%M'), swh='%.2f' % j, color=color) )

    MODEL['wave_forecast_table'] = items

    EN, ES, C = dates_in_table(fc_wav_time)

    items = [];
    for i, j, k in zip(EN, ES, C):
        items.append( dict(dates=i, fechas=j, counter=k ) )
    MODEL['wave_forecast_dates']= items

    outfile = '/data/pkl/MODEL-2.pkl'
    with open(outfile, 'wb') as f:
        dump(MODEL, f)
