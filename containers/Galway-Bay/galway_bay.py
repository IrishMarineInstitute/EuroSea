from netCDF4 import Dataset, num2date
from datetime import datetime
from pickle import dump
from json import dumps
import numpy as np
from log import set_logger, now

logger = set_logger()

west, south, north = -9.09, 53.12, 53.23
# Killeenaran coordinates
lat, lon = 53.19783333333333, -8.942277777777779

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

def galway_bay():
    
    url = 'http://milas.marine.ie/thredds/dodsC/IMI_ROMS_HYDRO/GALWAY_BAY_NATIVE_70M_8L_1H/COMBINED_AGGREGATION'
    
    ahora = datetime.now(); today = datetime(ahora.year, ahora.month, ahora.day)
    
    with Dataset(url) as nc:
        # Read longitude
        x = nc.variables['lon_rho'][0, :]
        idx0 = np.argmin(abs(x - west))
        idxK = np.argmin(abs(x - lon))
        x = x[idx0::]
        # Read latitude
        y = nc.variables['lat_rho'][:, 0]
        idy0 = np.argmin(abs(y - south))
        idy1 = np.argmin(abs(y - north))
        idyK = np.argmin(abs(y - lat))
        y = y[idy0:idy1]
        # Read time 
        time = num2date(nc.variables['ocean_time'][:], 
                        nc.variables['ocean_time'].units)
        
        time = [datetime(i.year, i.month, i.day, i.hour) for i in time]
        
        today = time.index(today)
        
        time_forecast = time[today::]
        # Read surface temperature forecast
        logger.info(f'{now()} Reading SST...')
        sst = nc.variables['temp'][today::, -1, idy0 : idy1, idx0::].filled(float('nan'))
        # Read seabed temperature forecast
        logger.info(f'{now()} Reading SBT...')
        sbt = nc.variables['temp'][today::,  0, idy0 : idy1, idx0::].filled(float('nan'))
        # Read surface salinity forecast
        logger.info(f'{now()} Reading SSS...')
        sss = nc.variables['salt'][today::, -1, idy0 : idy1, idx0::].filled(float('nan'))
        # Read seabed salinity forecast
        logger.info(f'{now()} Reading SBS...')
        sbs = nc.variables['salt'][today::,  0, idy0 : idy1, idx0::].filled(float('nan'))
        
        ahora = datetime.now(); ahora = datetime(ahora.year, ahora.month, ahora.day, ahora.hour)
        
        hour_index = time.index(ahora) + 1
        
        # Read surface temperature series at Killeenaran
        sstK = nc.variables['temp'][0:hour_index, -1, idyK, idxK]
        sstK_FC = nc.variables['temp'][hour_index::, -1, idyK, idxK]
        # Read seabed temperature series at Killeenaran
        sbtK = nc.variables['temp'][0:hour_index,  0, idyK, idxK]
        sbtK_FC = nc.variables['temp'][hour_index::, 0, idyK, idxK]
        # Read surface salinity series at Killeenaran
        sssK = nc.variables['salt'][0:hour_index, -1, idyK, idxK]
        sssK_FC = nc.variables['salt'][hour_index::, -1, idyK, idxK]
        # Read seabed salinity series at Killeenaran
        sbsK = nc.variables['salt'][0:hour_index,  0, idyK, idxK]
        sbsK_FC = nc.variables['salt'][hour_index::, 0, idyK, idxK]
        
        # Read sea level at Killeenaran
        zeta = nc.variables['zeta'][0:hour_index, idyK, idxK]
        zeta_FC = nc.variables['zeta'][hour_index::, idyK, idxK]
        
    GALWAY = {
        
        'lon': x, 'lat': y, 'ahora': ahora.strftime('%Y-%b-%d %H:%M'),
                
        'sstK': sstK, 'sssK': sssK, 'sbtK': sbtK, 'sbsK': sbsK, 'zeta': zeta,
        'sstK_FC': sstK_FC, 'sssK_FC': sssK_FC, 'sbtK_FC': sbtK_FC, 'sbsK_FC': sbsK_FC, 'zeta_FC': zeta_FC,
        
        'latest_temperature_surface': '%.1f' % round(sstK[-1], 1),
        'latest_temperature_seabed':  '%.1f' % round(sbtK[-1], 1),
        'maximum_temperature_forecast_surface': '%.1f' % round(max(sstK_FC), 1),
        'minimum_temperature_forecast_surface': '%.1f' % round( min(sstK_FC), 1),
        'maximum_temperature_forecast_seabed': '%.1f' % round(max(sbtK_FC), 1),
        'minimum_temperature_forecast_seabed': '%.1f' % round(min(sbtK_FC), 1),
        
        'latest_salinity_surface': '%.1f' % round(sssK[-1], 1),
        'latest_salinity_seabed':  '%.1f' % round(sbsK[-1], 1),
        'maximum_salinity_forecast_surface': '%.1f' % round(max(sssK_FC), 1),
        'minimum_salinity_forecast_surface': '%.1f' % round(min(sssK_FC), 1),
        'maximum_salinity_forecast_seabed': '%.1f' % round(max(sbsK_FC), 1),
        'minimum_salinity_forecast_seabed': '%.1f' % round( min(sbsK_FC), 1),
        
        't0': time[0].strftime('%Y-%m-%d %H:%M'),
        't1': time[-1].strftime('%Y-%m-%d %H:%M'),        
        
        'time_hindcast': time[0:hour_index],
        'time_forecast': time[hour_index::]
                
        }
    
    T, M, L = sss.shape
    
    for i in range(T):
        GALWAY['time_%02d' % i] = time_forecast[i].strftime('%Y-%b-%d %H:%M')
        GALWAY['sst_%02d' % i] = sst[i, :, :]
        GALWAY['sbt_%02d' % i] = sbt[i, :, :]
        GALWAY['sss_%02d' % i] = sss[i, :, :]
        GALWAY['sbs_%02d' % i] = sbs[i, :, :]
        
    outfile = '/data/pkl/GALWAY.pkl'
    with open(outfile, 'wb') as f:
        dump(jsonize(GALWAY), f)

if __name__ == '__main__':
    galway_bay()
