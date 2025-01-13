from pickle import dump
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

def send_output(FC):
    ''' Produce output PICKLE file to be sent to web app '''

    MODEL = {
        'fc_sst_time': FC['sst'][0],
        'fc_sst': FC['sst'][1],
 
        'tf': FC['sst'][0][-1].strftime('%Y-%m-%d %H:%M'),

        # End time for temperature
        'tf': FC['sst'][0][-1].strftime('%Y-%m-%d %H:%M'),

        # Mean forecasted seawater temperature
        'mean_forecast_temperature': round(sum(FC['sst'][1])/len(FC['sst'][1]), 1),
        # Minimum forecasted seawater temperature
        'min_forecast_temperature': round(min(FC['sst'][1]), 1),
        # Maximum forecasted seawater temperature
        'max_forecast_temperature': round(max(FC['sst'][1]), 1),
        }

    outfile = '/data/pkl/MODEL-1.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(MODEL), f)
