import Plot
from SST import read_mur
from NWSHELF import read_nws
from Climatology import climatology
from Deenish import Deenish
from Interpolate import nws2mur
import warnings
import os

warnings.filterwarnings('ignore')

class Deenish_Buoy_Observatory:
    
    def __init__(self, lon, lat):
        
        ''' Download from Deenish Island buoy '''
        
        # This returns a dictionary with the time and measurements from the
        #     Deenish buoy for the last month. Parameters included here are 
        #     temperature, salinity, oxygen, RFU and pH.
        #
        # The name of the fields in this dictionary are "time", "temp", "salt", 
        # "pH", "chl" and "DOX". For example, temperature data from the buoy
        # can be accessed as "self.buoy['temp']
        
        self.buoy = Deenish()
        
            
        ''' Remote-sensing SST '''
            
        # Multi-scale Ultra-high Resolution Sea Surface Temperature (MEaSUREs-MUR)
        
        url = 'https://thredds.jpl.nasa.gov/thredds/dodsC/OceanTemperature/MUR-JPL-L4-GLOB-v4.1.nc'
        
        # This downloads remote-sensing SST data from the MEaSUREs-MUR product.
        # The output of this function is:
        #
        # a -  sst_x     (L x 1)    NumPy array with longitude of SST grid
        #
        # b -  sst_y     (M x 1)    NumPy array with latitude of SST grid
        # 
        # c -  sst_time  (T x 1)    NumPy array with SST time (daily at 9 a.m for MUR)
        #
        # d -  sst       A 3-D array (T x M x L) with SST data in Celsius
        
        self.sst_x, self.sst_y, self.sst_time, self.sst = read_mur(url)
            
                    
        ''' Download Northwest Shelf prediction for Deenish Island '''
        
        # Temperature. This downloads temperature data from the Northwest Shelf
        # model. Model data is used for forecasting. The output is:
        #
        # a -  time    This is the time from the model for Deenish buoy. The
        #              buoy sends data every 10 minutes, so here model data for
        #              the buoy is downloaded at the highest temporal resolution
        #              available (1 hour)
        # 
        # b -  time2d  This is the time from the model that matches the remote-
        #              sensing SST observations. So, time here is daily at 9 a.m.
        #              It is 2-D because it covers the whole Southwest of Ireland,
        #              
        # c -  temp    Model temperature for Deenish site. It is a time series
        #              with same length as the time (a) above.
        #
        # d -  temp2d  2-D model temperature but for the whole Southwest of Ireland.
        #              The time record corresponding to this array is time2d (b)
        #              above. The longitude and latitude dimensions are different
        #              to those of the satellite product. This array is interpo-
        #              lated to the satellite grid later in the code.
        
        self.time, self.time2d, self.temp, self.temp2d = read_nws(self, 'T')
        
        # Salinity. Model salinity for the Deenish site. 
        _, _, self.salt, _ = read_nws(self, 'S')  
                    
        
        ''' Read SST climatology '''
        
        # A pre-built climatology is available as a NetCDF file. This function
        # returns:
        #
        # a -  clim_x     (L x 1)    NumPy array with longitude of climatology grid
        #                            Should be the same as the SST longitude.
        #
        # b -  clim_y     (M x 1)    NumPy array with latitude of climatology grid.
        #                            Should be the same as the SST latitude.
        # 
        # c -  clim_time  (T x 1)    NumPy array with climatology time. Numbers from
        #                            1 to 365 to store the climatology and MHW  
        #                            threhsold for each day of the year.
        #
        # d - seas    (T x M x L)    NumPy array with seasonal cycle: the multi-
        #                            year mean for each day of the year.
        #
        # e - pc90    (T x M x L)    90-th percentile threshold for MHW detection
        #
        # This function also returns the time, seasonal cycle, and 90-th percentile
        # threshold at the indicated coordinates        
                
        # Get climatology and threshold for the SW of Ireland and Deenish site
        self.clim_x, self.clim_y, self.clim_time, self.seas, self.pc90, \
        self.Deenish_time, self.Deenish_seas, self.Deenish_pc90 = climatology(self, 'Climatology/MUR-Climatology.nc', -10.2122, 51.7431)
          
        if lon is not None and lat is not None:
            # Get climatology and threshold for the site requested by user (lon, lat)
            _, _, _, _, _, self.u_time, self.u_seas, self.u_pc90 = \
                climatology(self, 'Climatology/MUR-Climatology.nc', lon, lat)
            
        
        ''' Interpolate model data to satellite grid '''
                       
        self.temp2d_interp = nws2mur(self)
                
        
        ''' Plot '''
        
        if not os.path.isdir('IMAGES'):
            os.mkdir('IMAGES')
        
        # Latest MUR-SST map
        Plot.Plot_SST(self)
        Plot.Plot_anom(self)
                
        params = list(self.buoy); params.remove('time'); params.remove('temp')
        
        # Deenish Island single y-axis time series plots
        Plot.Plot_Deenish_temperature(self, self.buoy['temp'])
        for i in params:
            Plot.Plot_Deenish(self, i)  
        
        # Deenish Island double y-axis time series plots
        pairs = [(x, y) for idx, x in enumerate(params) 
                 for y in params[idx + 1: ]]        
        for i in pairs:
            Plot.Plot_Deenish_YY(self, i[0], i[1])
        
        if lon is not None and lat is not None:
            Plot.Plot_Selection(self, lon, lat)
        
def main(lon=None, lat=None):
    
    return Deenish_Buoy_Observatory(lon, lat)        
        
if __name__ == '__main__':
    
    # Point selection for temperature series and MHW prediction
    lon, lat = -9, 51
    
    DBO = main(lon, lat)