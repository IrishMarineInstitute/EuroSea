from datetime import datetime
import pandas as pd
import numpy as np
from json import dumps

def jsonize(v):
    try:
        data = dumps(v) 
    except TypeError as ERR:
        if str(ERR) == 'Object of type datetime is not JSON serializable':
            value = [i.strftime('%Y-%m-%d %H:%M') for i in v]
            data = dumps(value)   
        elif str(ERR) == 'Object of type ndarray is not JSON serializable':
            data = dumps(v.tolist())
        elif str(ERR) == 'Object of type MaskedArray is not JSON serializable':
            data = dumps(v.tolist())
    return data


def fill_mhw(time, temp, time_c, pc90):
    ''' This function returns polygons to
        be filled with red color for MHW '''

    t1 = [i.timestamp() for i in time]
    t2 = [i.timestamp() for i in time_c]

    time = np.sort(np.concatenate([t1, t2]))

    y1 = np.interp(time, t1, temp)
    y2 = np.interp(time, t2, pc90)

    time = [datetime.fromtimestamp(i) for i in time]

    dataFrame = pd.DataFrame({'time': time,
                              'temp': y1,
                              'PC90': y2,
                              'label': y1 > y2,
                             }
    )

    dataFrame['group'] = dataFrame['label'].ne(dataFrame['label'].shift()).cumsum()
    dataFrame = dataFrame.groupby('group')
    DFS = []
    for name, data in dataFrame:
        DFS.append(data)

    MHW_times, MHW_temps = [], []

    for df in DFS:
        if any(df['label']):
            time = [i.astype('float') for i in np.array(df['time'])]
            temp = np.array(df['temp'])[-1::-1]
            PC90 = np.array(df['PC90'])

            time = time + time[-1::-1]

            time = [datetime.fromtimestamp(i/1000000000) for i in time]

            MHW_times.append(jsonize(time))
            MHW_temps.append(jsonize(np.hstack((PC90, temp))))

    return MHW_times, MHW_temps
