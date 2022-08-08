import numpy as np
import datetime
import Plot
from cmocean.cm import amp

def today_index_model_sat(platform, timedelta):
    '''
    Obtains the requested day and finds the corresponding index from the 
    model or the sst date.
    
    Parameters 
    ----------
    platform : np.ndarray
        Platform used to compute current or past day mhw info. Can either be from
        model or from satellite, if the info exists.
    timedelta: int
        Used to iterate over last days to find if there is a mhw ongoing, default = 0.

    Returns
    -------
    current_day_time_index: is the index from model/satellite days list of 
    the requested day.
    datetime_object: requested datetime

    '''
    
    day = datetime.date.today() + datetime.timedelta(timedelta)
    datetime_str = day.strftime('%m/%d/%y 09:%M')
    datetime_object = datetime.datetime.strptime(datetime_str, '%m/%d/%y %H:%M')
    datetime_object in platform
    current_day_time_index = np.where(platform==datetime_object)[0][0]
    #print(current_day_time_index)
    
    return current_day_time_index, datetime_object

def computing_mhw(platform, timedelta, index, date, dbo):
    '''
    Computes the marine heat waves and marine heat spikes for the requested day.

    Parameters
    ----------
    platform : numpy array
        It's the array of data either from satellite or from Model. Satellite
        is preferred over model.
    timedelta : int
        Days to add to the current date to compute the mhw for the specific day.
    index : int
        Time index of the requested day within platform array, used to compute mhw.
    date : datetime object
        Current day.
    dbo : self

    Returns
    -------
    mhw_matrix : numpy array
        Array of marine heat spikes.
    mhw_confirm : numpy array
        Array of marine heat waves, that is, marine heat spikes that last 5 or 
        more days.
    hgl_mhw : numpy array
        mhw_matrix * mhw_confirm, to retain obly the mhw regions.
    mhs_detected : bool
        True if marine heat spikes detected in the forecast window.
    mhw_detected : bool
        True if marine heat waves detected in the forecast window.

    '''
  
    # Selecting the climatic day that corresponds to the requested day
    climday_delta = timedelta - 1
    clim_day = date.timetuple().tm_yday - climday_delta
    
    #Selecting the mask from the requested day (should be always the same)
    masked = dbo.pc90.mask[clim_day,:,:]
    
    # Reading the sst
    req_day_sst = platform[index,:,:]
    
    X, Y = req_day_sst.shape
    
    req_day_sst_copy = np.zeros((X,Y))
    mhw_matrix = np.zeros((X,Y))
    mhw_confirm = np.zeros((X,Y))
    
    mhw_detected = False
    mhs_detected = False
    
    for i in range(0,X):
        for j in range(0,Y):
            req_day_sst_copy[i,j] = req_day_sst[i,j]
            
    for i in range(0,X):
        for j in range(0,Y):
            if masked[i,j] == True:
                mhw_matrix[i,j] = np.nan
                mhw_confirm[i,j] = np.nan
            elif req_day_sst_copy[i,j] > dbo.pc90[clim_day,i,j]:
                mhs_detected = True
                mhw_interval = req_day_sst_copy[i,j] - dbo.pc90[clim_day,i,j]
                mhw_matrix[i,j] = mhw_interval
                is_mhw = [True]
                
                for d in range(1,5):
                    if platform[index-d,i,j] > dbo.pc90[clim_day-d,i,j]:
                        is_mhw.append(True)
                    else:
                        is_mhw.append(False)
                
                if False not in is_mhw:
                    mhw_detected = True
                    mhw_confirm[i,j] = 1
                else:
                    mhw_confirm[i,j] = np.nan
            else:
                mhw_matrix[i,j] = 0
                mhw_confirm[i,j] = np.nan
    
    hgl_mhw = mhw_confirm * mhw_matrix
     
    return mhw_matrix, mhw_confirm, hgl_mhw, mhs_detected, mhw_detected
    
def mhw(time_delta,dbo):
    '''
    Chooses between satellite or model and computes marine heat events
    for the indicated amount of days.

    Parameters
    ----------
    time_delta : int
        Used to iterate over last days to find if there is a mhw ongoing.
    dbo : self

    Returns
    -------       
    mhs : numpy array
        Array of marine heat spikes.
    mhws : numpy array
        Array of marine heat waves, that is, marine heat spikes that last 5 or 
        more days.
    hgl_mhw : numpy array
        mhw_matrix * mhw_confirm, to retain obly the mhw regions.
    mhs_warn : bool
        True if marine heat spikes detected in the forecast window.
    mhw_warn : bool
        True if marine heat waves detected in the forecast window.

    '''

    requested_day = datetime.date.today() + datetime.timedelta(time_delta)
    datetime_str = requested_day.strftime('%m/%d/%y 9:%M')
    datetime_object = datetime.datetime.strptime(datetime_str, '%m/%d/%y %H:%M')
    
    if datetime_object in dbo.sst_time:
        print('Using Satellite SST data')
        platform = np.array(dbo.sst_time)
        sst_platform = dbo.sst
        index, date = today_index_model_sat(platform,time_delta)
        mhs,mhws, hgl_mhws, mhs_warn,mhw_warn = computing_mhw(sst_platform, time_delta, index, date,dbo)
        return mhs,mhws,hgl_mhws,mhs_warn,mhw_warn
    else:
        print('Using Model SST data')
        platform = np.array(dbo.time2d)
        sst_platform = dbo.temp2d_interp
        index, date = today_index_model_sat(platform,time_delta)
        mhs,mhws,hgl_mhws,mhs_warn,mhw_warn = computing_mhw(sst_platform, time_delta, index, date,dbo)
        return mhs,mhws,hgl_mhws,mhs_warn,mhw_warn
    
def mhw_processing(dbo):
    
    '''
    Puts previous functions together, visualize and warns about incoming heat events.
    '''
    
    mhw_detected = False
    n_days_frc_i = 0
    n_days_frc_f = 5
    today = datetime.date.today() + datetime.timedelta(n_days_frc_i)
    last_frc_day = datetime.date.today() + datetime.timedelta(n_days_frc_f)
    print('Computing marine heat events from {} to {}'.format(today,last_frc_day))
    
    for day in range(6):
        mhs,mhws,hgl_mhws,mhs_warn,mhw_warn = mhw(day,dbo)
        requested_day = datetime.date.today() + datetime.timedelta(day)
        print('Computing marine heat events for {}'.format(requested_day))
        
        Plot.plot2d('MHS {}'.format(requested_day), dbo.sst_x, dbo.sst_y, mhs, 0, 3, 
                          cmap=amp, units='', title='Marine Heat Spikes {}'.format(requested_day))
        Plot.plot2d('MHW {}'.format(requested_day), dbo.sst_x, dbo.sst_y, hgl_mhws, 0, 3, 
                          cmap=amp, units='', title='Marine Heat Waves {}'.format(requested_day))
        
        if mhw_detected == False:
            if mhw_warn == True:
                print('Marine Heat Wave detected within the 5-day forecast window')
                print('Starting on {}'.format(requested_day))
                mhw_detected = True
            else:
                if mhs_warn == True:
                    print('Marine Heat Spike detected within the 5-day forecast window')
                    print('Starting on {}'.format(requested_day))
                else:
                    print('No marine heat events detected within the 5-day forecast window')
        else:
            continue
        
        