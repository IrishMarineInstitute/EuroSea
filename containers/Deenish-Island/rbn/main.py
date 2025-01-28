from composite import get_median
from datetime import date, timedelta
from PIL import Image
import subprocess
import glob
import os

from log import set_logger, now
logger = set_logger()

def run(command):
    ''' Execute a CLI command and return output and error messages '''
    try:
        process = subprocess.Popen(command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        return output.decode('utf-8'), error.decode('utf-8')

    except Exception as e:
        return None, str(e)

def configuration():
    ''' Read configuration file '''
    config = {}
    with open('config', 'r') as f:
        for line in f:
            if line[0] == '!': continue
            key, val = line.split()[0:2]
            # Save to dictionary
            config[key] = val
    return config

def main():
    ''' Download NOAA Red Band daily files '''

    # WGET instruction to download TIFF files
    swget = 'wget --no-proxy --no-check-certificate -t 200 --waitretry=100 --retry-connrefused -c'
    config = configuration()

    http = config.get('http')

    # Prepare output directory
    rw = config.get('rw')
    if not os.path.isdir(rw):
        os.makedirs(rw)

    link = config.get('link')   

    # CLI instruction to call WGET to download HTML file
    strwget = 'wget -O list.txt "' + link + '"'
    # Download via WGET to get a "list.txt" local file
    output, error = run(strwget)
    if error:
        logger.error(error)

    str1, str2 = 'sentinel', 'rbd_rhos.tif'
    # Get names of TIFF files to download
    with open('list.txt', 'r') as f:
        for line in f:
            if (str1 in line) and (str2 in line):
                i0, i1 = line.find(str1), line.find(str2)
                image = line[i0 : i1+12]

                #  Don't download filenames
                # longer than 73 characters 
                if len(image) > 73: continue 

                # Check if file exists. Download otherwise
                filename = rw + '/' + image
                if not os.path.isfile(filename):
                    logger.info(f'Downloading {image}')
                    run(swget + ' -P ' + rw + ' ' + http + image)

    mv = config.get('mv')
    if not os.path.isdir(mv):
        os.makedirs(mv)

    # Get year, month and day from each file name
    files = sorted(glob.glob(rw + '/*.tif'))
    for i in files:
        s = os.path.basename(i).split('.')
        # Get year, month and day from file name
        y, m, d = s[1][0:4], s[2][0:2], s[2][2:4]

        # Open TIFF file
        img = Image.open(i)
        # Convert to PNG. Name of PNG file
        pngname = mv + '/sentinel-' + y + m + d + '.png'
        # Save image as PNG 
        img.save(pngname)

    os.remove('list.txt')

    logger.info(' ')
    # Produce weekly composites
    weekly_composites(mv, config.get('wk'))

def weekly_composites(pathin, pathout):
    ''' Produce weekly composites for every week with available data '''

    today = date.today().weekday()
    # Get date of last Sunday
    Sunday = date.today() - timedelta(days=today+1)
    # Get date of Monday
    Monday = Sunday - timedelta(days=6)

    while 1:
        idate, edate = Monday.strftime('%Y-%b-%d'), Sunday.strftime('%Y-%b-%d')

        logger.info(f'Creating composite from {idate} to {edate}')

        R = get_median(pathin, pathout, Monday, Sunday)

        if not R:
            logger.info('No files found for this week. Exiting...'); break

        Monday -= timedelta(days=7); Sunday -= timedelta(days=7)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(str(e))
