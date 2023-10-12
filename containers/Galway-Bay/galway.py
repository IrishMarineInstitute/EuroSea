from geopy.distance import geodesic as GD
from netCDF4 import Dataset, num2date
from datetime import datetime
from scipy import interpolate
import numpy as np
import pytz
from pickle import dump
from log import set_logger, now

logger = set_logger()

def configuration():
    ''' Read secrets (configuration) file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save as environment variable
            config[key] = val
    return config


def get_UTC_time(timezone, minute=False):
    ''' Convert local time to UTC '''
    
    # Get local time zone
    local = pytz.UTC # pytz.timezone(timezone)
    # Current time (naive)
    now = datetime.now()    
    
    if minute:
        # Current time (naive) to minute precision
        naive = datetime(now.year, now.month, now.day, now.hour, now.minute)       
    else:
        # Current time (naive) only to hour precision
        naive = datetime(now.year, now.month, now.day, now.hour)       
        
    # Localize current time in local time zone
    local_dt = local.localize(naive, is_dst=None)
    # Convert to UTC
    return local_dt.astimezone(pytz.utc)


def reader():
    ''' Read Galway Bay model sea level time series at the 
        indicated site (LAT, LON) '''
        
    url = 'http://milas.marine.ie/thredds/dodsC/IMI_ROMS_HYDRO/GALWAY_BAY_NATIVE_70M_8L_1H/AGGREGATE'
    
    with Dataset(url) as nc:
        # Read longitude
        x = nc.variables['lon_rho'][:]
        # Read latitude
        y = nc.variables['lat_rho'][:]
        # Read sea level
        logger.info(f'{now()} Reading sea level...')
        zeta = nc.variables['zeta'][:] + 3.0 # add offset
        # Read mask
        logger.info(f'{now()} Reading mask...')
        mask = nc.variables['wetdry_mask_rho'][:]
        # Read time
        time = num2date(nc.variables['ocean_time'][:],
                        nc.variables['ocean_time'].units)
        # Read surface temperature
        logger.info(f'{now()} Reading surface temperature...')
        surface_temperature = nc.variables['temp'][:, -1, :, :]
        # Read seabed temperature
        logger.info(f'{now()} Reading seabed temperature...')
        seabed_temperature = nc.variables['temp'][:, 0, :, :]
        # Read surface temperature
        logger.info(f'{now()} Reading surface salinity...')
        surface_salinity = nc.variables['salt'][:, -1, :, :]
        # Read seabed temperature
        logger.info(f'{now()} Reading seabed salinity...')
        seabed_salinity = nc.variables['salt'][:, 0, :, :]
        logger.info(f'{now()} Finished reading from Galway Bay THREDDS...')
        
    # Set time as UTC
    time = [datetime(i.year, i.month, i.day, i.hour, 0, 0, 0, pytz.UTC) for i in time]
        
    return x, y, time, mask, zeta, surface_temperature, \
        seabed_temperature, surface_salinity, seabed_salinity


def find_nearest_indexes(x, y, lon, lat):     
    ''' Find indexes in ROMS grid nearest to LAT, LON location '''
    
    xlist, ylist = x[0, :], y[:, 0]
    # Find nearest indexes to LAT, LON
    idx, idy = np.argmin(abs(xlist - lon)), np.argmin(abs(ylist - lat))
    
    return idx, idy


def land_mask_areas(mask):
    ''' Given the wet & dry land mask, return an M x L array where:
        '0.0' are land areas, 
        '0.5' are intertidal areas, 
        '1.0' are sea areas '''
    
    T, _, _ = mask.shape
    
    sea = np.sum(mask, axis=0) == T    
    tidal = np.logical_and(np.sum(mask, axis=0) > 0, np.sum(mask, axis=0) < T)
    
    return  sea + 0.5 * tidal


def test_sea_level_series(zeta):
    ''' Check that the sea level series in unaffected by a drying out (i.e. its
        shape is that of a normal tidal signal, without flat values) '''
    
    k = 0.05 # [m]
    
    T = len(zeta)
    
    for i in range(T - 2):
        # Get three consecutive values
        z0, z1, z2 = zeta[i : i+3]
        # Compute differences
        d0, d1, d2 = abs(z1-z0), abs(z2-z1), abs(z2-z0)
        
        if (d0 < k) and (d1 < k) and (d2 < k): # Sea level series is flat!
            return False # The sea level series is not adequate
        
    return True # Good sea level series


def find_nearest_indexes_at_sea(x, y, lon, lat, areas, zeta):
    ''' For a LAT, LON site on an intertidal flat, find the closest grid node
        at sea (i.e, a site that never dries out even during low tide) '''
        
    M, L = areas.shape
    
    idx, idy, distance, level = [], [], [], []
    
    for i in range(L):
        for j in range(M):
            if areas[j, i] == 1.0:
                latitude, longitude = y[j, i], x[j, i]
                # Get distance
                D = GD((lat, lon), (latitude, longitude)).km
                
                idx.append(i); idy.append(j); distance.append(D)
                # Append sea level time series
                level.append(zeta[:, j, i])
    
    
    indices = sorted(range(len(distance)), key=lambda k: distance[k])
    distance = [distance[i] for i in indices]
    idx = [idx[i] for i in indices]
    idy = [idy[i] for i in indices]
    series = [level[i] for i in indices]
    
    for i, j, D, z in zip(idx, idy, distance, series):
        if test_sea_level_series(z):
            return i, j, D, z
        
        
def minute_interpolation(time, tide):
    ''' Interpolate hourly sea level time series to minute frequency '''
    
    # Convert time to UNIX time stamps (seconds since 1970-01-01)
    # This is needed because the scipy interpolating function cannot handle
    # datetime objects as the independent variable.
    timestamps = np.array([i.timestamp() for i in time])
    
    # Create cubic interpolator
    F = interpolate.CubicSpline(timestamps, tide)
    
    # List of time stamps to interpolate to (every minute)
    tq = np.arange(timestamps[0], timestamps[-1] + 60, 60)
        
    # Interpolate
    tideq = np.array([F(t) for t in tq])

    # What is the current index in this new time list? Convert back to datetime
    tq = [datetime.utcfromtimestamp(i) for i in tq]
    # Add the time zone information (UTC)
    tq = [i.replace(tzinfo=pytz.utc) for i in tq]
    
    return tq, tideq


def tidal_times(time, tide):
    ''' Find next high and low tide times and magnitudes '''
    
    low, high = None, None
    
    # Get current trend: flood (+) or ebb (-)
    trend = tide[1] - tide[0]
    
    T = len(time)
    
    for i in range(T - 1):
        change = tide[i + 1] - tide[i]
        
        if change * trend < 0: 
            if trend < 0: # low tide
                low, low_time = tide[i], time[i]
            else: # high tide
                high, high_time = tide[i], time[i]
                
        if isinstance(low, float) and isinstance(high, float):
            break
        
        trend = change
        
    return low, low_time, high, high_time


def to_string(values, wetdry, timezone):
    ''' Convert numbers and times to strings. Convert current values to "DRY" 
    if "DRY" is the current status of the tide '''
    
    local = pytz.timezone(timezone)
    
    GALWAY = {}
    
    for key, val in values.items():
        if ( 'wet' in key ) and ( not wetdry ):
            GALWAY[key] = 'DRY'
        else:
            if isinstance(val, np.float32) or isinstance(val, np.float64):
                GALWAY[key] = f'%.1f' % val
            elif isinstance(val, datetime):
                time = val.astimezone(local)                
                GALWAY[key] = time.strftime('%a %d %H:%M')
            else:
                GALWAY[key] = val
 
    return GALWAY

def decdeg2dms(dd):
    ''' Convert decimal degrees to DMS '''

    mnt,sec = divmod(abs(dd)*3600, 60)
    deg,mnt = divmod(mnt, 60)
    return f'''%02dº%02d%s%.1f"''' % (deg, mnt, '´', sec)

def main():
    
    logger.info(f'{now()} Starting GALWAY-BAY operations...')

    ''' Read configuration '''
    config = configuration()

    ''' Get local time as UTC '''
    UTC = get_UTC_time(config.get('timezone'), minute=True)
        
    ''' Get current time to be displayed on the website '''
    webtime=UTC.astimezone(pytz.timezone(config.get('timezone')))
    
    ''' Get local time as UTC '''
    UTC = get_UTC_time(config.get('timezone'))

    ''' Get site name(s) '''
    names = config.get('name')
    
    ''' Get site coordinates '''
    lon, lat = float(config.get('lon')), float(config.get('lat'))
    # Convert to DMS 
    lonstr, latstr = decdeg2dms(lon), decdeg2dms(lat)
     
    ''' Read Galway Bay model '''
    logger.info(f'{now()} Reading from Galway Bay THREDDS...')
    x, y, time, mask, zeta, ST, BT, SS, BS = reader()
    
    ''' Find nearest indexes in grid '''
    # Current time index
    tindex = time.index(UTC)    
    # Nearest spatial (LAT, LON) indexes
    idx, idy = find_nearest_indexes(x, y, lon, lat)   
    
    ''' Get time series for the LAT, LON site '''
    tide   = zeta[:, idy, idx] # sea level 
    wetdry = mask[:, idy, idx] # Wet & Dry status
    ST = ST[:, idy, idx] # Surface temperature
    BT = BT[:, idy, idx] # Bottom temperature
    SS = SS[:, idy, idx] # Surface salinity
    BS = BS[:, idy, idx] # Bottom salinity
    
    ''' GET CURRENT STATUS '''   
    WET_DRY   = wetdry[tindex]
    surface_temperature = ST[tindex]
    bottom_temperature  = BT[tindex]
    surface_salinity    = SS[tindex]
    bottom_salinity     = BS[tindex]
    
    ''' Get forecasts '''
    TF  = time[tindex::] # Forecast time
    STF = ST[tindex::] # Surface Temperature Forecast
    BTF = BT[tindex::] # Bottom Temperature Forecast
    SSF = SS[tindex::] # Surface Salinity Forecast
    BSF = BS[tindex::] # Bottom Salinity Forecast
    
    ''' Get forecast minima and maxima '''
    minSTF, maxSTF = min(STF), max(STF)
    minBTF, maxBTF = min(BTF), max(BTF)
    minSSF, maxSSF = min(SSF), max(SSF)
    minBSF, maxBSF = min(BSF), max(BSF)
    
    ''' Get indexes of minima and maxima '''
    minSTFi, maxSTFi = np.argmin(STF), np.argmax(STF)
    minBTFi, maxBTFi = np.argmin(BTF), np.argmax(BTF)
    minSSFi, maxSSFi = np.argmin(SSF), np.argmax(SSF)
    minBSFi, maxBSFi = np.argmin(BSF), np.argmax(BSF)
    
    ''' Get times of minima and maxima '''
    minSTFt, maxSTFt = TF[minSTFi], TF[maxSTFi]
    minBTFt, maxBTFt = TF[minBTFi], TF[maxBTFi]
    minSSFt, maxSSFt = TF[minSSFi], TF[maxSSFi]
    minBSFt, maxBSFt = TF[minBSFi], TF[maxBSFi]
        
    ''' Get thermal status (heating or cooling) '''
    change = ST[tindex+1] - surface_temperature
    if change > 0:
        surface_heat = 'heating'
    else:
        surface_heat = 'cooling'
        
    change = BT[tindex+1] - bottom_temperature
    if change > 0:
        bottom_heat = 'heating'
    else:
        bottom_heat = 'cooling'        
        
    ''' Get haline status (saltier or fresher) '''
    change = SS[tindex+1] - surface_salinity
    if change > 0:
        surface_saltrend = 'saltier'
    else:
        surface_saltrend = 'fresher'
        
    change = BS[tindex+1] - bottom_salinity
    if change > 0:
        bottom_saltrend = 'saltier'
    else:
        bottom_saltrend = 'fresher'        
    
    # Examine mask. Differentiate betweeen land (0.0) areas, intertidal (0.5)
    # areas and sea (1.0) areas. Why? The selected LAT, LON site may be in an
    # intertidal area, where it is not easy to identify the exact time of the
    # next low tide. The objective of the code below is to (1) indentify the
    # nearest grid node where the tidal signal behaves "adequately" (i.e., no
    # drying out); (2) extract the sea level series for that site. This time
    # series will then be used to idenfity the time of low tide. 
    areas = land_mask_areas(mask)
    
    ''' Check if site is either land (0.0), intertidal (0.5) or sea (1.0).
        If needed, get sea level series from a neighbouring location which 
        never dries out '''
    tipo = areas[idy, idx]
    if tipo == 0.0: # Point is on land. Wrong site. Change LAT, LON
        raise RuntimeError('Point is on land')
    elif tipo == 0.5: # Point is in an intertidal flat
        # Find nearest indexes at sea. Get seea level series
        logger.info(f'{now()} Finding nearest indexes at sea...')
        idxS, idyS, D, tideS = find_nearest_indexes_at_sea(x, y, lon, lat, areas, zeta)
    elif tipo == 1.0: # Point is at land
        tideS = tide
        
    ''' Interpolate to minute frequency. This is to determine the next high (or
    low) tide with enough precision '''
    logger.info(f'{now()} Interpolating sea level time series to minute frequency...')
    time, tide = minute_interpolation(time, tideS)
    
    ''' Get local time as UTC '''
    UTC = get_UTC_time(config.get('timezone'), minute=True)
    # Current time index
    tindex = time.index(UTC)    
    
    ''' Get current sea level '''
    SEA_LEVEL = tide[tindex]
    
    ''' Find next high and low tide times and values '''
    logger.info(f'{now()} Finding next high and low tides...')
    low, low_time, high, high_time = \
        tidal_times(time[tindex::], tide[tindex::])
        
    ''' Find tidal status: flood or ebb '''
    change = tide[tindex+1] - SEA_LEVEL
    if change > 0:
        STATUS, tide1extreme, tide2extreme = 'flood', 'HIGH', 'LOW'
        # Set next high tide
        tide1extremeValue, tide1extremeTime = high, high_time
        # Set next low tide
        tide2extremeValue, tide2extremeTime = low, low_time
    else:
        STATUS, tide1extreme, tide2extreme = 'ebb', 'LOW', 'HIGH'
        # Set next high tide
        tide2extremeValue, tide2extremeTime = high, high_time
        # Set next low tide
        tide1extremeValue, tide1extremeTime = low, low_time
        
    ''' Prepare output '''
    logger.info(f'{now()} Preparing output dictionary...')
    values = dict(tidewet=SEA_LEVEL, time=webtime,
        names=names, lon=lonstr, lat=latstr,
        STwet=surface_temperature, BTwet=bottom_temperature,
        SSwet=surface_salinity, BSwet=bottom_salinity,
        minSTF=minSTF, maxSTF=maxSTF, minBTF=minBTF, maxBTF=maxBTF,
        minSSF=minSSF, maxSSF=maxSSF, minBSF=minBSF, maxBSF=maxBSF,
        minSTFt=minSTFt, maxSTFt=maxSTFt, minBTFt=minBTFt, maxBTFt=maxBTFt,
        minSSFt=minSSFt, maxSSFt=maxSSFt, minBSFt=minBSFt, maxBSFt=maxBSFt,
        tide1extreme=tide1extreme, tide2extreme=tide2extreme,
        tide1extremeValue=tide1extremeValue, tide1extremeTime=tide1extremeTime,
        tide2extremeValue=tide2extremeValue, tide2extremeTime=tide2extremeTime,
        STATUS=STATUS, surface_heat=surface_heat, bottom_heat=bottom_heat, 
        surface_saltrend=surface_saltrend, bottom_saltrend=bottom_saltrend,
                  )
    logger.info(f'{now()} Converting variables to string...')
    GALWAY = to_string(values, WET_DRY, config.get('timezone'))
    
    outfile = '/data/pkl/GALWAY.pkl'
    with open(outfile, 'wb') as f:
        dump(GALWAY, f)

    logger.info(f'{now()} FINISHED...')
        
if __name__ == '__main__':   
  GALWAY =  main()
