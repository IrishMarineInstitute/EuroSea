import Plot
from SST import read_mur
from NWSHELF import read_nws
from Climatology import climatology
from Deenish import Deenish
from Interpolate import nws2mur
import mhw
import warnings
import os

warnings.filterwarnings('ignore')

class Deenish_Buoy_Observatory:
    
    def __init__(self, lon, lat):
        
        ''' Download from Deenish Island buoy '''
        
        # self.buoy es un diccionario con los datos descargados de la boya.
        # Se puede acceder a cada variable como self.buoy['time'], self.buoy[´temp´]
        # self.['time'], 'temp': [], 'salt': [], 'pH': [], 'chl':  [], 'DOX':  [] 
        self.buoy = Deenish()
        
            
        ''' Remote-sensing SST '''
            
        # Multi-scale Ultra-high Resolution Sea Surface Temperature (MEaSUREs-MUR)
        
        url = 'https://thredds.jpl.nasa.gov/thredds/dodsC/OceanTemperature/MUR-JPL-L4-GLOB-v4.1.nc'
        
        # longitude, latitud, tiempo y temperatura del satelite
        # se pueden ver las dimensions con .shape
        self.sst_x, self.sst_y, self.sst_time, self.sst = read_mur(url)
            
                    
        ''' Download Northwest Shelf prediction for Deenish Island '''
        
        # Temperature
        
        # para el modelo, se ha decargado: 
        # 1. El tiempo para la boya. Como la boya tiene datos cada 10 minutos,
        # en el modelo se ha descargado con la maxima resolucion temporal disponible: 1 hora
        # el tiempo para la boya del modelo es self.time
        
        # 2. El tiempo del modelo, pero para comparar con el satelite. El satelite tiene
        # medidas solo para las 9 de la mañana de cada dia, al menos para el MUR.
         
         # 3. self.temp es la temperature del modelo para la localizacion de la boya. Es una
         # serie temporal, no un mapa
         
         # 4. self.temp2d es la temperatura del modelo para todo el mapa (SW Irlanda)
         # Luego, para que tenga las mismas dimensiones que el satelite, y se puedan comparar,
         # se interpola mas abajo a la malla del satelite. Asi que self.temp2d ya no hay que usarlo.
        self.time, self.time2d, self.temp, self.temp2d = read_nws(self, 'T')
        
        # Salinity
        _, _, self.salt, _ = read_nws(self, 'S')  
                    
        
        ''' Read SST climatology '''
        
        # Aqui se lee del NetCDF de la climatologia: la longitud, la latitud, el tiempo 
        # (que son los dias del año del 1 al 365), el valor promedio (self.seas), y el percentil
        # 90 (self.pc90)
        
        
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
    
    dbo = main(lon, lat)
    

    
