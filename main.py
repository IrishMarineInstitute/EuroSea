import Plot
from CA import CA
from SST import read_mur
from NWSHELF import read_nws
from Climatology import climatology
from Deenish import Deenish, SWAN
from Interpolate import nws2mur
from LPTM import LPTM
import mhw
import warnings
import os
import _thread
import threading

warnings.filterwarnings('ignore')

def raw_input_with_timeout(prompt, timeout=10.0):
      
    timer = threading.Timer(timeout, _thread.interrupt_main)
    astring = None
    try:
        timer.start()
        astring = input(prompt)
    except KeyboardInterrupt:
        pass
    timer.cancel()
    return astring

class Deenish_Buoy_Observatory:
    
    def __init__(self, lon, lat):
        
        ''' Run particle-tracking model '''
        while 1:
            answer = raw_input_with_timeout('Run particle-tracking model? (Takes several minutes...) [y/n]')
            if ( answer.lower() == 'y' ) or not answer:
                LPTM(); break
            elif answer.lower() == 'n':
                break
            else:
                print("\nInvalid input. Please enter either 'y' or 'n'\n")
            
                
        ''' Get chlorophyll anomaly '''
        while 1:
            OUT = CA()
            if not OUT: 
                continue 
            else:
                self.x_chl, self.y_chl, self.time_chl, self.chl, self.anom = OUT
                break
            
        
        ''' Download from Deenish Island buoy '''
             
        self.buoy, self.swan = Deenish(), SWAN()        
        
            
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
        
        
        ''' Compute Marine Heat events '''
        
        if not os.path.isdir('IMAGES'):
            os.mkdir('IMAGES')
            
        mhw.mhw_processing(self)
              
        
        ''' Plot '''
        
        # Latest MUR-SST map
        Plot.Plot_SST(self)
        # Plot.Plot_anom(self)
                
        # Chlorophyll
        Plot.Plot_chla(self)
        Plot.Plot_chla_anom(self)
        
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
                           
        # Deenish Island SWAN wave forecast
        Plot.Plot_SWAN(self)
        
def main(lon=None, lat=None):
    
    return Deenish_Buoy_Observatory(lon, lat)        
        
if __name__ == '__main__':
    
    # Point selection for temperature series and MHW prediction
    lon, lat = -9, 51
    
    DBO = main(lon, lat)