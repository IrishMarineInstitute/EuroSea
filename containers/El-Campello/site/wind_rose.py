import plotly.express as px
import plotly
import numpy as np
import json
import pandas as pd

def wind_dir_speed_freq(wind_rose_data, boundary_lower_speed, boundary_higher_speed, boundary_lower_direction, boundary_higher_direction):
    
    ''' mask for wind speed column '''
    log_mask_speed = (wind_rose_data[:,0] >= boundary_lower_speed) & (wind_rose_data[:,0] < boundary_higher_speed)
    
    ''' mask for wind direction '''
    log_mask_direction = (wind_rose_data[:,1] >= boundary_lower_direction) & (wind_rose_data[:,1] < boundary_higher_direction)
    
    ''' Application of the filter on the wind_rose_data array '''
    return wind_rose_data[log_mask_speed & log_mask_direction]

def wind_rose(time, wind_rose_data, vartype):
    
    ''' 
        This function returns a JSON object representing a wind rose figure.
        The input "wind_rose_data" must be an Nx2 Numpy array with speed on
        the left and direction on the right. "vartype" is either 'wind',
        'currents', or 'wave'.
    '''

    ''' Return time interval for wind rose title '''
    idate = time[0]
    edate = time[-1]
    
    wind_rose_df = pd.DataFrame(np.zeros((16*9, 3)), index = None, columns = ('direction', 'strength', 'frequency'))
    
    ''' Set direction bins '''
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    directions_deg = np.array([0, 22.5, 45, 72.5, 90, 112.5, 135, 157.5, 180, 202.5, 225, 247.5, 270, 292.5, 315, 337.5])
    
    ''' Set speed bins '''
    if vartype == 'wind':
        speed_bins = ['0-5 km/h', '6-11 km/h', '12-19 km/h', '20-28 km/h', 
                      '29-38 km/h', '39-49 km/h', '50-61 km/h', '62-74 km/h', '>74 km/h']
        
    elif vartype == 'currents':
        speed_bins = ['0-10 cm/s', '10-20 cm/s', '20-25 cm/s', '25-30 cm/s', 
                      '30-35 cm/s', '35-40 cm/s', '40-45 cm/s', '45-50 cm/s', '>50 cm/s']

    elif vartype == 'wave':
        speed_bins = ['0-2 s', '2-3 s', '3-4 s', '4-5 s', '5-6 s',
                        '6-7 s', '7-8 s', '8-9 s', '>9 s']

    
    ''' Filling in the dataframe with directions and speed bins '''
    wind_rose_df.direction = directions * 9
    wind_rose_df.strength = np.repeat(speed_bins, 16)
    
    idx = pd.MultiIndex.from_product([speed_bins,
                                      directions_deg],
                                     names=['wind_speed_bins', 'wind_direction_bins'])
    col = ['frequency']
    frequencies_df = pd.DataFrame(0, idx, col)
    
    ''' Distance between the centre of the bin and its edge '''
    step = 11.25
    
    ''' converting data between 348.75 and 360 to negative '''
    for i in range(len(wind_rose_data)):
        if directions_deg[-1] + step <= wind_rose_data[i,1] and wind_rose_data[i,1] < 360:
            wind_rose_data[i,1] = wind_rose_data[i,1] - 360
    
    ''' Determining the direction bins '''
    bin_edges_dir = directions_deg - step
    bin_edges_dir = np.append(bin_edges_dir, [directions_deg[-1]+step]) 
        
    ''' Determining speed bins ( the last bin is 50 as above those speeds the outliers were removed for the measurements) '''
    if vartype == 'wind':
        threshold_outlier_rm = 200
        bin_edges_speed = np.array([0, 5.5, 11.5, 19.5, 28.5, 38.5, 49.5, 61.5, 74.5, threshold_outlier_rm])
        
    elif vartype == 'currents':
        threshold_outlier_rm = 200
        bin_edges_speed = np.array([0, 10, 20, 25, 30, 35, 40, 45, 50, threshold_outlier_rm])

    elif vartype == 'wave':
        threshold_outlier_rm = 300 
        bin_edges_speed = np.array([0, 2, 3, 4, 5, 6, 7, 8, 9, threshold_outlier_rm])
    
    frequencies = np.array([])
    ''' Loop selecting given bins and calculating frequencies '''
    for i in range(len(bin_edges_speed)-1):
        for j in range(len(bin_edges_dir)-1):
            bin_contents = wind_dir_speed_freq(wind_rose_data, bin_edges_speed[i], bin_edges_speed[i+1], bin_edges_dir[j], bin_edges_dir[j+1])
            
            # applying the filtering function for every bin and checking the number of measurements
            bin_size = len(bin_contents)
            frequency = bin_size/len(wind_rose_data)
            
            #obtaining the final frequencies of bin
            frequencies = np.append(frequencies, frequency)
    
    ''' Updating the frequencies dataframe '''
    frequencies_df.frequency = frequencies*100 # [%]
    
    ''' This is a "strength", "frequency", "direction" data frame '''
    wind_rose_df.frequency = frequencies*100 # [%]
        
    ''' Use Plotly to produce wind rose from data frame '''
    if vartype == 'wind':
        BEAUFORT = ['#AEF1F9', '#96F7DC', '#96F7B4', 
                    '#6FF46F', '#73ED12', '#A4ED12', 
                    '#DAED12', '#EDC212', '#ED8F12'] 
       
        fig = px.bar_polar(wind_rose_df, r="frequency", theta="direction",
                        color="strength", template="plotly_dark",
                        color_discrete_sequence=BEAUFORT)
    else:
        fig = px.bar_polar(wind_rose_df, r="frequency", theta="direction",
                        color="strength", template="plotly_dark",
                        color_discrete_sequence= px.colors.sequential.Plasma_r)
    
    return idate, edate, json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
