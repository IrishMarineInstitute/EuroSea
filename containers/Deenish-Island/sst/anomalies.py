import numpy as np

def Anomalies(sst, clm):
    ''' Calculate sea surface temperature anomalies '''

    time, SST = sst; # Actual sea surface temperature

    time_c, seas, pc90 = clm # Climatology

    # Output initialization
    anm = np.empty_like(SST)

    for j, T in enumerate(time):

        SST_j = SST[j, :, :]

        # Get day of year of selected date
        DOY = T.timetuple().tm_yday

        # Find time index in climatology
        i = np.where(time_c == DOY)[0][0]

        # Get climatology SST distribution for this day of the year    
        seas_j = seas[i, :, :]

        # Get SST anomaly as the difference between actual SST and climatology
        anm[j, :, :] = SST_j - seas_j

    return anm
