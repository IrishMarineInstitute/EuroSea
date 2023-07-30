from numpy import nanmax, array
from json import dumps

def jsonize(data):
    for k, v in data.items():
        if isinstance(v, str): continue
        if isinstance(v, tuple): v = v[0]
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

def send_output(sub):
    ''' Produce output PICKLE file to be sent to web app '''

    # Get time ranges
    t0 = sub['time'][0]
    t1 = sub['time'][-1]

    # Determine first x-axis tick
    for i in sub['time']:
        if not i.hour and not i.minute:
            break
    tick0 = i.strftime('%Y-%m-%d')

    BUOY = {
        # Buoy time
        'time': sub['time'],
        'tick0': tick0,
        't0': t0.strftime('%Y-%m-%d %H:%M'),
        'tf': t1.strftime('%Y-%m-%d %H:%M'),

        'maxTUR': nanmax(array(sub['TUR'])) + 1,
        }

    for i in sub.keys():
        if ' ' in i:
            new_key = i.replace(' ', '_')
        else:
            new_key = i
        BUOY[new_key] = sub[i]

    return jsonize(BUOY)
