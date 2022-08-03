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
        
        self.buoy = Deenish()
        
            
        ''' Remote-sensing SST '''
            
        # Multi-scale Ultra-high Resolution Sea Surface Temperature (MEaSUREs-MUR)
        
        url = 'https://thredds.jpl.nasa.gov/thredds/dodsC/OceanTemperature/MUR-JPL-L4-GLOB-v4.1.nc'
        
        self.sst_x, self.sst_y, self.sst_time, self.sst = read_mur(url)
            
                    
        ''' Download Northwest Shelf prediction for Deenish Island '''
        
        # Temperature
        self.time, self.time2d, self.temp, self.temp2d = read_nws(self, 'T')
        
        # Salinity
        _, _, self.salt, _ = read_nws(self, 'S')  
                    
        
        ''' Read SST climatology '''
        
        self.clim_x, self.clim_y, self.clim_time, self.seas, self.pc90, \
        self.Deenish_time, self.Deenish_seas, self.Deenish_pc90 = climatology(self, 'Climatology/MUR-Climatology.nc', -10.2122, 51.7431)
          
        if lon is not None and lat is not None:
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