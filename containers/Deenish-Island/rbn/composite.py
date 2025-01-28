from datetime import timedelta
from PIL import Image
import numpy as np
import os

from log import set_logger, now
logger = set_logger()

def color_scale():
    ''' Get colormap used in red band images '''
    
    C, R, G, B = [], [], [], []
    with open('viridis_red_v2.txt', 'r') as f:       
        for line in f:
            if line[0] == '!': continue
            out = line.split()
            C.append(int(out[0]))
            R.append(int(out[2]))
            G.append(int(out[3]))
            B.append(int(out[4]))
            
    return np.array(C), np.array(R), np.array(G), np.array(B) 

def get_median(pathin, pathout, idate, edate):
    ''' Get median of images from IDATE to EDATE '''

    istr, estr = idate.strftime('%Y-%b-%d'), edate.strftime('%Y-%b-%d')
    logger.info(f'   Creating weekly composite from {istr} to {estr}...')

    if not os.path.isdir(pathout):
        os.makedirs(pathout)
    
    newfile = pathout + '/sentinel-' + idate.strftime('%Y%m%d') + \
            '-' + edate.strftime('%Y%m%d') + '.png'
    if os.path.isfile(newfile):
        logger.info('   File already exists. Return.'); return 1

    files = [] # Get list of Sentinel TIF files from IDATE to EDATE
    while idate < edate + timedelta(days=1):
        filename = pathin + '/sentinel-' + idate.strftime('%Y%m%d') + '.png'
        if os.path.isfile(filename):
            logger.info(f'      Using {filename}')
            files.append(filename)
        idate += timedelta(days=1)
    
    if not files: # No files for these dates
        logger.info('   No files found for these dates. Return.'); return 0
        
    M, L = Image.open(files[0]).size
    
    O = np.zeros((len(files), L, M))
    for i, f in enumerate(files):
        O[i, :, :] = Image.open(f)
        
    ''' Mask invalid values that should be ignored when computing the median '''
    # Mask cloud, invalid or not covered values
    O = np.ma.masked_where(O > 252, O)  
    # Mask values above range
    O = np.ma.masked_where(O == 250, O)
    O = np.ma.masked_where(O == 251, O)
    # Mask no detections 
    O = np.ma.masked_where(O == 0, O)
   
    # Calculate median
    P50 = np.round(np.ma.median(O, axis=0)).filled(0)
   
    C, R, G, B = color_scale()
    
    # Initialize output RGB image
    RGB = np.zeros((L, M, 3), dtype=np.uint8)
    for i in range(L):        
        for j in range(M):            
            w = np.argmin(abs(C - P50[i, j]))
            RGB[i, j, :] = np.array([R[w], G[w], B[w]])
    
    Im = Image.fromarray(RGB, mode='RGB')
    # Save image to disk
    Im.save(newfile)
    
    return 1
