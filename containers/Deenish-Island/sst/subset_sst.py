from netCDF4 import Dataset

def subset_sst():
    ''' The file downloaded from Copernicus is for Marine Heat Wave analysis,
        and contains N + 4 days. Here, subset the NetCDF to show only N days
        of SST and SST anomaly. '''
    
    with Dataset('/data/SST/OSTIA-MHW.nc', 'r') as nc:
        # Read coordinates
        lon, lat = nc.variables['lon'][:], nc.variables['lat'][:]
        # Read time
        time = nc.variables['time'][:]
        # Read SST
        SST = nc.variables['analysed_sst'][:]
        
    # Subset
    time, SST = time[4::], SST[4::, :, :]
    
    # Create new NetCDF for SST and anomaly visualization
    with Dataset('/data/SST/OSTIA.nc', 'w') as nc:
        
        ''' Create dimensions '''
        nc.createDimension('lon', len(lon))
        nc.createDimension('lat', len(lat))
        nc.createDimension('time', len(time))
        
        ''' Longitude '''
        lonvar = nc.createVariable('lon', 'f4', dimensions=('lon'))
        lonvar.standard_name = 'longitude'
        lonvar.units = 'degree_east'     
        lonvar[:] = lon
        
        ''' Latitude '''
        latvar = nc.createVariable('lat', 'f4', dimensions=('lat'))
        latvar.standard_name = 'latitude'
        latvar.units = 'degree_north'  
        latvar[:] = lat
        
        ''' Time '''
        timevar = nc.createVariable('time', 'i4', dimensions=('time'))
        timevar.standard_name = 'time'
        timevar.units = 'seconds since 1981-01-01 00:00:00'
        timevar[:] = time
        
        ''' SST '''
        sst = nc.createVariable('analysed_sst', 'f4', dimensions=('time', 'lat', 'lon'))        
        sst.standard_name = 'ssea_surface_foundation_temperature'
        sst.long_name = 'analysed sea surface temperature'
        sst.units = 'kelvin'
        sst[:] = SST
