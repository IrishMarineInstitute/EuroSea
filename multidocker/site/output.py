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

def suboxic(o2):
    return 1 if o2 < 70 else 0

def MHW():
    return 0

def send_output(sub, D, clim, timev):
    ''' Produce output PICKLE file to be sent to web app '''
    # Get climatology
    time_c, seas, pc90 = clim

    # Get time ranges
    t0 = sub['time'][0]
    t1 = sub['time'][-1]

    # Determine first x-axis tick
    for i in sub['time']:
        if not i.hour and not i.minute:
            break
    tick0 = i.strftime('%Y-%m-%d')

    timestamps = [i.timestamp() for i in timev]
    timestampsub = []; timetext = [];
    for i in timev:
        if ( not i.hour % 3 ) and ( not i.minute ) :
            timestampsub.append(i.timestamp())
            timetext.append(i.strftime('%d-%b %H:%M'))

    BUOY = {
        # Buoy time
        'time': sub['time'],
        'tick0': tick0,
        't0': t0.strftime('%Y-%m-%d %H:%M'),
        't1': t1.strftime('%Y-%m-%d %H:%M'),
        'timestamps': timestamps,
        'timestampsub' : timestampsub,
        'timetext': timetext,
        
        # in-situ time series data
        'temp': sub['Temperature'],
        'salt': sub['Salinity'],
        'pH': sub['pH'],
        'O2': sub['Oxygen Saturation'],
        'RFU': sub['RFU'],

        'maxRFU': max(sub['RFU']) + 0.1,

        # Latest observations 
        'latest_temperature': round(sub['Temperature'][-1], 2),
        'latest_oxygen': round(sub['Oxygen Saturation'][-1], 2),
        'latest_salinity': round(sub['Salinity'][-1], 2),
        'latest_pH': round(sub['pH'][-1], 2),
        'latest_RFU': round(sub['RFU'][-1], 2),

        'SubO2': suboxic(round(sub['Oxygen Saturation'][-1], 2)),

        # vector data: surface
        'u0': sub['u0'], 'v0': sub['v0'],            
        # vector data: middle
        'umid': sub['umid'], 'vmid': sub['vmid'],            
        # vector data: bottom
        'ubot': sub['ubot'], 'vbot': sub['vbot'],            
        # vector data: winds
        'uwind': sub['uwind'], 'vwind': sub['vwind'],
        
        # Displacements: surface
        'Dx0': D['surf-x'], 'Dy0': D['surf-y'],            
        # Displacements: middle
        'Dxmid': D['midw-x'], 'Dymid': D['midw-y'],            
        # Displacements: bottom
        'Dxbot': D['seab-x'], 'Dybot': D['seab-y'],            
        # Displacements: winds
        'Dxwind': D['winds-x'], 'Dywind': D['winds-y'],            

        # Local SST climatology
        'time_c': time_c,
        'seas': seas,
        'pc90': pc90,

        'MHW_Warning': MHW(),
        }
    outfile = '/data/pkl/BUOY.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(BUOY), f)
