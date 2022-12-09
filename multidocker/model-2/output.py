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

    # Get temperature profile
    temp = FC['temp3d'][1]; T, N = temp.shape

    MODEL = {
        'fc_sst_time': FC['sst'][0],
        'fc_sst': FC['sst'][1],
 
        'fc_sss_time': FC['sss'][0],
        'fc_sss': FC['sss'][1],
 
        'tf': FC['sst'][0][-1].strftime('%Y-%m-%d %H:%M'),

        'fc_temp3d_time': FC['temp3d'][0],

        'forecast_temperature': round(max(FC['sst'][1]), 2),
        }

    for k in range(N):
        MODEL[f'fc_temp3d_{k}'] = temp[:, k]
    outfile = '/data/pkl/MODEL-2.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(MODEL), f)
