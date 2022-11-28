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

def suboxic(o2):
    return 1 if o2 < 70 else 0

def MHW():
    return 0

def send_output(sub, var, D, clim, timev, time3d, temp):
    ''' Produce output PICKLE file to be sent to web app '''
    # Get climatology
    time_c, seas, pc90 = clim

    # Get temperature profile
    T, N = temp.shape

    # Get time ranges
    t0 = sub['time'][0]
    t1 = sub['time'][-1]

    # Determine first x-axis tick
    for i in sub['time']:
        if not i.hour and not i.minute:
            break
    tick0 = i.strftime('%Y-%m-%d')

    if timev:
        timestamps = [i.timestamp() for i in timev]
        timestampsub = []; timetext = [];
        for i in timev:
            if ( not i.hour % 3 ) and ( not i.minute ) :
                timestampsub.append(i.timestamp())
                timetext.append(i.strftime('%d-%b %H:%M'))
    else:
        timestamps, timestampsub, timetext = None, None, None # No vector data

    BUOY = {
        # Buoy time
        'time': sub['time'],
        'tick0': tick0,
        't0': t0.strftime('%Y-%m-%d %H:%M'),
        'tf': t1.strftime('%Y-%m-%d %H:%M'),
        'timestamps': timestamps,
        'timestampsub' : timestampsub,
        'timetext': timetext,
        'fc_temp3d_time': time3d,

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

        # Local SST climatology
        'time_c': time_c,
        'seas': seas,
        'pc90': pc90,

        'MHW_Warning': MHW(),
        }

    if var:
        # vector data: surface
        BUOY['u0'] = var['u0']; BUOY['v0'] = var['v0']            
        # vector data: middle
        BUOY['umid'] = var['umid']; BUOY['vmid'] = var['vmid']            
        # vector data: bottom
        BUOY['ubot'] = var['ubot']; BUOY['vbot'] = var['vbot']            
        
    if D:
        # Displacements: surface
        BUOY['Dx0'] = D['surf-x']; BUOY['Dy0'] = D['surf-y'],            
        # Displacements: middle
        BUOY['Dxmid'] = D['mid-x']; BUOY['Dymid'] = D['mid-y']            
        # Displacements: bottom
        BUOY['Dxbot'] = D['seab-x']; BUOY['Dybot'] = D['seab-y']            

    for k in range(N):
        BUOY[f'fc_temp3d_{k}'] = temp[:, k]

    return jsonize(BUOY)
