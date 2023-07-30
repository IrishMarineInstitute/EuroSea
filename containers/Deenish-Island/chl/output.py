from pickle import dump
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

def send_output(lon, lat, colour, coast):
    ''' Produce output PICKLE file to be sent to web app '''

    # Get oceancolour
    lon_o, lat_o, time_o, CHL = colour

    RS = {
 
        }

    outfile = '/data/pkl/RS.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(RS), f)
