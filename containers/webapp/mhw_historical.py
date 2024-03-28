from netCDF4 import Dataset, num2date
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly
import numpy as np
import json
import glob
import os

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

def datenum2datetime(datenum):
    return np.array([datetime.fromordinal(int(i)) + timedelta(days=i%1) for i in datenum])

def plot_mhw(longitude, latitude, time, SST, years, climatology, PCT10, PCT90, min_y, max_y,
        idates=None, edates=None, idatesCold=None, edatesCold=None, buoy=None):
    ''' Plot figure '''
            
    fig = go.Figure()
    
    # Plot buoy data, if needed 
    if buoy is not None:
        buoyY, timeByYear, insitu, buoyname = buoy
        for year, t, temp in zip(buoyY, timeByYear, insitu):
            temp[temp > max_y] = np.nan # Mask abnormal values
            temp[temp < min_y] = np.nan # Mask abnormal values
            visible = [True if year == buoyY[-1] else False][0]
            fig.add_trace(go.Scatter(
                          name=f'Buoy {year}', showlegend=True, visible=visible,
                          mode="lines", x=t, y=temp,
                          line=dict(width=1.5, color='#0000ff')
                      ))
    else:
        buoyname = ''
   
    for year, sst in zip(years, SST):
        # Plot SST (gray, always seen regardless of the slider position)
        fig.add_trace(go.Scatter(
                      name=str(year), hoverinfo="none",
                      mode="lines", x=time, y=sst, showlegend=False,
                      line=dict(width=0.5, color='#808080')
                  ))        
         
        visible = [True if year == years[-1] else False][0]
        # Plot SST (black, only one per year, updates depending on the slider)
        fig.add_trace(go.Scatter(
                      name=f'Year {year}', showlegend=True, visible=visible,
                      mode="lines", x=time, y=sst,
                      line=dict(width=1.5, color='#000000')
                  ))
    
    # Plot seasonal cycle
    fig.add_trace(go.Scatter(
                  name="climatology", showlegend=True,
                  mode="lines", x=time, y=climatology,
                  line=dict(width=1.5, color='#008000')
              ))
    
    # Plot PCT. 10
    fig.add_trace(go.Scatter(
                  name="PCT. 10", showlegend=True,
                  mode="lines", x=time, y=PCT10,
                  line=dict(width=1.5, color='#00ffff')
              ))
    
    # Plot PCT. 90
    fig.add_trace(go.Scatter(
                  name="PCT. 90", showlegend=True,
                  mode="lines", x=time, y=PCT90,
                  line=dict(width=1.5, color='#ff0000')
              ))
    
    if idates is not None:
        # Plot MHWs
        for i, (t0, t1) in enumerate(zip(idates, edates)):
            t0, t1 = datetime.strptime(t0, '%Y-%m-%d'), datetime.strptime(t1, '%Y-%m-%d')
            year0, year1 = t0.year, t1.year
            # Get MHW dates as strings
            str0 = (t0-timedelta(hours=24)).strftime('2020-%m-%d')
            str1 = t1.strftime('2020-%m-%d')
            
            visible = [True if year1 == years[-1] else False][0]
            if year0 == year1:             
                fig.add_trace(go.Scatter(
                    name=f'MHW-{year0}-{i}', showlegend=False, visible=visible,
                    x=[str0, str0, str1, str1, str0],
                    y=[min_y-1, max_y+1, max_y+1, min_y-1, min_y-1],
                    fill="toself", fillcolor='rgba(220, 20, 60, 0.25)',
                    line=dict(width=0.25, color='rgba(220, 20, 60, 0.25)')))
                
            elif year1 - year0 == 1:
                fig.add_trace(go.Scatter(
                    name=f'MHW-{year0}-{i}', showlegend=False, visible=False,
                    x=[str0, str0, f'2020-12-31', f'2020-12-31', str0],
                    y=[min_y-1, max_y+1, max_y+1, min_y-1, min_y-1],
                    fill="toself", fillcolor='rgba(220, 20, 60, 0.25)',
                    line=dict(width=0.25, color='rgba(220, 20, 60, 0.25)')))
                
                fig.add_trace(go.Scatter(
                    name=f'MHW-{year1}-{i}', showlegend=False, visible=visible,
                    x=[f'2020-01-01', f'2020-01-01', str1, str1, f'2020-01-01'],
                    y=[min_y-1, max_y+1, max_y+1, min_y-1, min_y-1],
                    fill="toself", fillcolor='rgba(220, 20, 60, 0.25)',
                    line=dict(width=0.25, color='rgba(220, 20, 60, 0.25)')))
            
            else:
                raise RuntimeError('Marine Heat Wave spanning multiple years???')        
    
    if idatesCold is not None:
        # Plot MHWs
        for i, (t0, t1) in enumerate(zip(idatesCold, edatesCold)):
            t0, t1 = datetime.strptime(t0, '%Y-%m-%d'), datetime.strptime(t1, '%Y-%m-%d')
            year0, year1 = t0.year, t1.year
            # Get MHW dates as strings
            str0 = (t0-timedelta(hours=24)).strftime('2020-%m-%d')
            str1 = t1.strftime('2020-%m-%d')
            
            visible = [True if year1 == years[-1] else False][0]
            if year0 == year1:             
                fig.add_trace(go.Scatter(
                    name=f'CS-{year0}-{i}', showlegend=False, visible=visible,
                    x=[str0, str0, str1, str1, str0],
                    y=[min_y-1, max_y+1, max_y+1, min_y-1, min_y-1],
                    fill="toself", fillcolor='rgba(0, 123, 167, 0.25)',
                    line=dict(width=0.25, color='rgba(0, 123, 167, 0.25)')))
                
            elif year1 - year0 == 1:
                fig.add_trace(go.Scatter(
                    name=f'CS-{year0}-{i}', showlegend=False, visible=False,
                    x=[str0, str0, f'2020-12-31', f'2020-12-31', str0],
                    y=[min_y-1, max_y+1, max_y+1, min_y-1, min_y-1],
                    fill="toself", fillcolor='rgba(0, 123, 167, 0.25)',
                    line=dict(width=0.25, color='rgba(0, 123, 167, 0.25)')))
                
                fig.add_trace(go.Scatter(
                    name=f'CS-{year1}-{i}', showlegend=False, visible=visible,
                    x=[f'2020-01-01', f'2020-01-01', str1, str1, f'2020-01-01'],
                    y=[min_y-1, max_y+1, max_y+1, min_y-1, min_y-1],
                    fill="toself", fillcolor='rgba(0, 123, 167, 0.25)',
                    line=dict(width=0.25, color='rgba(0, 123, 167, 0.25)')))
            
            else:
                raise RuntimeError('Cold Spell spanning multiple years???')        
    
    fig.update_layout(title=f'OSTIA SST %.3fºN %.3fºW %s' % (latitude, abs(longitude), buoyname),
                      title_x=0.5,
                      font=dict(family="Calibri", size=18),
                      yaxis_title='°C',
                      yaxis_tickformat='.1f',
                      xaxis_tickvals=[f'2020-%02d-01' % M for M in range(1, 13)],
                      xaxis_tickformat='%B',
                      xaxis_range=[time[0], time[-1]],
                      yaxis_range=[min_y, max_y],
                      )
    
    # Create and add slider
    steps = []
    for i in years:
        # Show all traces
        step = dict(
            method='restyle',
            args=['visible', [True] * len(fig.data)],
            label=str(i),
        )
        
        for j, trace in enumerate(fig.data):
            name = trace.name
            if name.startswith('B') and int(name[-4::]) != i:
                step['args'][1][j] = False
            if name.startswith('Y') and int(name[-4::]) != i:
                step['args'][1][j] = False
            if name.startswith('MHW-') and int(name[4:8]) != i:
                step['args'][1][j] = False
            if name.startswith('CS-') and int(name[3:7]) != i:
                step['args'][1][j] = False
    
        # Add step to step list
        steps.append(step)

    sliders = [dict(
        active=len(years)-1,
        currentvalue={"prefix": "", "xanchor": "center"},
        pad={"t": 15},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders
    )
       
    fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return fig

def cleancsv():
    ''' Remove old CSV files from temporary folder '''

    files = glob.glob('/tmp/*.csv')
    if len(files) > 100:
        for f in files:
            os.remove(f)

def sst2csv(lon, lat, time, sst):
    ''' Write CSV of SST time series '''

    # Set CSV file name
    filename = f'/tmp/csv-sst-%.3fN-%.3fW.csv' % (lat, abs(lon))

    with open(filename, 'w') as f:
        # Write header
        f.write('Date,SST (ºC)\n')
        # Write data line by line
        for t, temp in zip(time, sst):
            f.write(f'%s,%.2f\n' % (t.strftime('%Y-%m-%d'), temp))

    return filename

def clim2csv(lon, lat, time, clim, pc10, pc90):
    ''' Write CSV of climatology '''

    # Set CSV file name
    filename = f'/tmp/csv-clim-%.3fN-%.3fW.csv' % (lat, abs(lon))

    with open(filename, 'w') as f:
        # Write header
        f.write('Day,PCT.10 (ºC),mean (ºC),PCT.90 (ºC)\n')
        # Write data line by line
        for t, pct10, avg, pct90 in zip(time, pc10, clim, pc90):
            f.write(f'%s,%.2f,%.2f,%.2f\n' % (datetime.strptime(t, '%Y-%m-%d').strftime('%d-%b'),
                pct10, avg, pct90))

    return filename

def mhw2csv(lon, lat, T0, T1, D, I, categ, mode='hot'):
    ''' Write CSV of MHWs '''

    # Set CSV file name
    if mode == 'hot':
        filename = f'/tmp/csv-mhw-%.3fN-%.3fW.csv' % (lat, abs(lon))
    elif mode == 'cold':
        filename = f'/tmp/csv-cs-%.3fN-%.3fW.csv' % (lat, abs(lon))

    with open(filename, 'w') as f:
        # Write header
        f.write('Event ID,start,end,duration (days),intensity (ºC),category\n')
        # Write data line by line
        for j, (t0, t1, d, i, c) in enumerate(zip(T0, T1, D, I, categ)):
            f.write(f'%03d,%s,%s,%d,%.2f,%d\n' % (j, t0, t1, d, i, c))

    return filename

def process_extreme_events(file, lonGrid, latGrid, mode='hot'):
    ''' Process extreme events from Hobday container '''
    
    one = np.array([1])
    
    with Dataset(file, 'r') as nc:
        
        # Read longitude
        lon = nc.variables['longitude'][:]        
        # Read latitude
        lat = nc.variables['latitude'][:]        
        # Read start times
        t0 = nc.variables['idate'][:]        
        # Read end times
        t1 = nc.variables['edate'][:]
        # Read duration
        duration = nc.variables['duration'][:]
        # Read intensity
        intensity = nc.variables['intensity'][:]
        # Read category
        categ = nc.variables['category'][:]
        
    # Get indexes of events occurring at the selected site
    I = np.where( np.logical_and(
        abs(lon - lonGrid) < 0.005,
        abs(lat - latGrid) < 0.005 ) ) [0]
    
    if not np.array_equal(one, np.unique(I[1::] - I[0:-1])):
        raise RuntimeError('Point is on land')
        
    # Subset
    t0, t1 = t0[I], t1[I]
    duration = duration[I]
    intensity = intensity[I]
    categ = categ[I]

    # Convert datetimes to strings
    t0 = [datetime.fromtimestamp(i).strftime('%Y-%m-%d') for i in t0]
    t1 = [datetime.fromtimestamp(i).strftime('%Y-%m-%d') for i in t1]
    
    # Write CSV of marine heat waves
    if mode == 'hot':
        csvfile = mhw2csv(lonGrid, latGrid, t0, t1, duration, intensity, categ)
    elif mode == 'cold':
        csvfile = mhw2csv(lonGrid, latGrid, t0, t1, 
                duration, intensity, categ, mode='cold')

    return t0, t1, csvfile

def mhw_historical(lon, lat, display_mhw, display_cs, buoy):

    cleancsv()
    
    ''' Read configuration options '''
    config = configuration()
    
    ''' Read buoy series, if needed '''
    buoydata, csvinsitu = None, None
    if buoy:
        ncname, varname = buoy
        # Set buoy name
        buoyname = ncname.replace('-', ' ')
        # Set CSV file name
        csvinsitu = f'/data/csv/{ncname}.csv'
        # Set NetCDF full path
        ncname = f'/data/netcdf/{ncname}.nc'
        # Open NetCDF (downloaded from ERDDAP)
        with Dataset(ncname, 'r') as nc:
            # Read buoy time
            tbuoy = num2date(nc.variables['time'][:],
                    nc.variables['time'].units)
            # Read buoy seawater temperature
            insitu = nc.variables[varname][:]
            # Mask missing values
            insitu[insitu <= 0] = np.nan

        ''' Divide buoy data by years '''
        # Get the year from each time in buoy series
        buoyYears = np.array([i.year for i in tbuoy])
        # Refer all times to 2020, as 2020 is the only year in the x-axis
        tbuoy = np.array([i.strftime('2020-%m-%d %H:%M') for i in tbuoy])
        # Get a list of the different years in the series
        buoyY = np.unique(buoyYears)
        # Separate in-situ temperature for each year in the series
        insitu = [insitu[buoyYears == i] for i in buoyY]
        # Separate buoy time for each year in the series
        timeByYear = [tbuoy[buoyYears == i] for i in buoyY]

        #          Pass the following to the plotting function:
        # years of buoy data, in-situ temperature and buoy name
        buoydata = (buoyY, timeByYear, insitu, f'({buoyname})')

    ''' Read SST '''
    agg = config.get('sstnc')
    with Dataset(agg, 'r') as nc:
        # Read longitude
        x = nc.variables['longitude'][:]
        idx = np.argmin(abs(x - lon))
        # Read latitude
        y = nc.variables['latitude'][:]
        idy = np.argmin(abs(y - lat))
        # Read time
        t = nc.variables['time']
        t = num2date(t[:], t.units)
        # Read SST
        sst = nc.variables['analysed_sst'][:, idy, idx] - 273.15 # Kelvin to Celsius
        
    if sum(np.isnan(sst)) == len(sst):
        raise RuntimeError('Point is on land')
        
    # Get longitude and latitude on grid
    lonGrid, latGrid = x[idx], y[idy]
    
    # Write CSV of SST series
    csvsst = sst2csv(lonGrid, latGrid, t, sst)
    
    ''' Divide by years '''
    years = np.array([i.year for i in t])
    Y = np.unique(years)
    SST = [sst[years == i] for i in Y]
    
    ''' Read climatology '''
    clm = config.get('climnc')
    with Dataset(clm, 'r') as nc:
        # Read climatology
        seas = nc.variables['seas'][:, idy, idx]
        # Read PCT90
        pc90 = nc.variables['PCT90'][:, idy, idx]
        # Read PCT10
        pc10 = nc.variables['PCT10'][:, idy, idx]
        
    # Get the 29-Feb climatological value for a leap year
    leap = .5 * (seas[58] + seas[59])
    seas = np.hstack((seas[0:59], leap, seas[59::]))
    leap = .5 * (pc90[58] + pc90[59])
    pc90 = np.hstack((pc90[0:59], leap, pc90[59::]))
    leap = .5 * (pc10[58] + pc10[59])
    pc10 = np.hstack((pc10[0:59], leap, pc10[59::]))
    
    ''' Read MHWs '''
    if display_mhw:

        t0, t1, csvmhw = process_extreme_events(config.get('mhwnc'),
                lonGrid, latGrid) 
        
    else:
        t0, t1, csvmhw = None, None, None
            
    ''' Read Cold Spells '''
    if display_cs:
        
        t0cold, t1cold, csvcs = process_extreme_events(config.get('coldnc'),
                lonGrid, latGrid, mode='cold') 

    else:
        t0cold, t1cold, csvcs = None, None, None

    ''' Set x-axis: the days in a leap year '''
    idate, edate = datetime(2020, 1, 1), datetime(2021, 1, 1)
    time = []
    while idate < edate:
        time.append(idate.strftime('%Y-%m-%d'))
        idate += timedelta(days=1)
        
    # Write CSV of climatology
    csvclim = clim2csv(lonGrid, latGrid, time, seas, pc10, pc90)

    ''' Get y-axis range '''
    min_y, max_y = float(config.get('min_y')), float(config.get('max_y'))
        
    ''' Plot '''
    figure = plot_mhw(lonGrid, latGrid, time, SST, Y, seas, pc10, pc90, 
            min_y, max_y, idates=t0, edates=t1, idatesCold=t0cold, edatesCold=t1cold,
            buoy=buoydata)

    return figure, csvsst, csvclim, csvmhw, csvcs, csvinsitu
