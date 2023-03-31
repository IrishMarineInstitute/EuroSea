from pickle import dump
from json import dumps
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

def send_output(FC, wave_rose_figure, wave_rose_series):
    
    ''' Produce output PICKLE file to be sent to web app '''

    MODEL = {
        
        # Temperature time
        'fc_sst_time': FC['sst'][0],
        # Seawater temperature
        'fc_sst': FC['sst'][1],
 
        # Waves time     
        'fc_wav_time': FC['Hs_fc'][0],
        # Significant Wave Height
        'fc_wav':      FC['Hs_fc'][1],
        # Secondary swell
        'fc_wav_sw2':      FC['Hs_sw2_fc'][1],
        
        # End time for waves
        'tw': FC['Hs_fc'][0][-1].strftime('%Y-%m-%d %H:%M'),
        # End time for temperature
        'tf': FC['sst'][0][-1].strftime('%Y-%m-%d %H:%M'),

        # Maximum forecasted seawater temperature
        'forecast_temperature': round(max(FC['sst'][1]), 1),
        # Maximum forecasted significant wave height
        'forecast_max_swh': round(max(FC['Hs_fc'][1]), 2),
        # Maximum forecast secondary swell significant wave height
        'forecast_max_swh_sw2': round(max(FC['Hs_sw2_fc'][1]), 2),

         # Wave Wind Rose
        'fc_wave_rose_idate': wave_rose_figure['idate'],
        'fc_wave_rose_edate': wave_rose_figure['edate'], 
        'fc_wave_rose': wave_rose_figure['fig'],
 
        'shortest_period': round(FC['shortest_period'], 1),
        'associated_direction': int(round(FC['associated_direction'], 0)),
        
        'fc_wave_rose_time': wave_rose_series['time'],
        'fc_wave_rose_period': wave_rose_series['period'],
        'fc_wave_rose_direction': wave_rose_series['direction'],
        }
   
    outfile = '/data/pkl/MODEL-2.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(MODEL), f)
