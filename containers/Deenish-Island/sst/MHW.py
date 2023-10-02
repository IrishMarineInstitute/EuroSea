from netCDF4 import Dataset, num2date
import numpy as np

def MarineHeatWaves(clm):
    
    time_c, seas, pc90 = clm # Climatology

    with Dataset('/data/SST/OSTIA-MHW.nc', 'r') as nc:        
        # Read time
        time = num2date(nc.variables['time'][:], nc.variables['time'].units)
        # Read SST
        SST = nc.variables['analysed_sst'][:] - 273.15
        
    # Output initialization
    MHW, anm = np.empty_like(SST), np.empty_like(SST)    
        
    for j, T in enumerate(time):
        # Get SST 
        SST_j = SST[j, :, :]
        
        # Get day of year of selected date
        DOY = T.timetuple().tm_yday
        
        # Find time index in climatology
        i = np.where(time_c == DOY)[0][0]
        
        # Get climatology SST distribution for this day of the year
        seas_j = seas[i, :, :]
        
        # Get PCT. 90 distribution for this day of the year
        pc90_j = pc90[i, :, :]
        
        # Check whether SST is higher than PCT. 90
        MHW[j, :, :] = SST_j > pc90_j
        
        # Calculate anomaly (MHW intensity)
        anm[j, :, :] = SST_j - seas_j
        
    # Mask anomalies where SST is below PCT. 90 (no MHW)    
    anm[MHW == 0] = np.nan
    
    # Prepare output arrays (anomalies where there is an ongoing MHW)
    MHW = np.copy(anm[4::])
    
    C = -1    
    for index in range(4, len(time)): # This index is used for the extended
                                      # time period taking 4 days back in time.
                                      
        C += 1 # This index is used for the time period shown on the portal.
        
        # Take anomalies for this day
        this = MHW[C, :, :]
        
        # Take latest 5 days of anomalies
        last5days = anm[index-4:index+1]
        
        # Check where the anomaly is NaN (SST below PCT. 90, see masking above)
        isnan = np.isnan(last5days)
        
        # Find out where there is at least one NaN in the 5 days. 
        ANY = np.any(isnan, axis=0)
        
        # No MHW's in such points, since a MHW requires 
        # five consecutive days above PCT. 90 (no NaN).
        this[ANY == True] = np.nan
        
        # Add masked areas to the output MHW array
        MHW[C, :, :] = this
        
    MHW[np.isnan(MHW)] = 0.0 
    # Mask missing values
    # MHW = MHW.filled(0.0)

    return MHW
