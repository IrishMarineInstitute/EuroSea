# EuroSea Data Portal

Welcome to the GitHub Repository of the EuroSea Data Portal. The EuroSea Data Portal is a project that aims at providing real-time oceanographic data and forecasts at the Deenish Island and El Campello monitoring sites. The website can be accessed at https://eurosea.marine.ie. 

This is a EuroSea partnership between the Marine Institute, the Spanish National Research Council (CSIC), Mowi Ireland (formerly Marine Harvest) and Xylem / Aanderaa Data Instruments. This part of the Marine Observatory work is being developed within the WP6 Ocean Health Demonstrator of the EuroSea project “Improving and integrating the European Ocean Observing and Forecasting System”. This project is funded by the EU Horizon 2020 research and innovation programme under grant agreement No 862626.

# Installation

These instructions have been tested on Ubuntu 18.04.6 LTS (Bionic Beaver). First, download the code with: 

```
git clone https://github.com/IrishMarineInstitute/EuroSea.git
```

The code is structured in multiple Docker containers that communicate with each other through a shared volume. Create a Docker volume to communicate the containers:

```
docker volume create shared-data
```

The next step is to initialize each container. ``` crontab ``` is used to schedule tasks and ensure that the website updates on a regular basis. The containers work independently, so there is no need to initialize them in a specific order.

## Deenish Island - SITE container

This container is set to run every ten minutes to download _in-situ_ data from the EuroSea monitoring station at Deenish Island. In addition, it subsets the latest data
for the number of days specified in the configuration file. All this data is wrapped in a BUOY.pkl file that is updated every ten minutes, and later accessed by the WEBAPP container through the shared volume. Historical data starting from the time the buoy started data transmission is compiled to address any request from the Historical Data Portal.
   
Navigate to the Deenish Island - SITE container
```
cd EuroSea/containers/Deenish-Island/site
```

Build image
```
docker build -t deenish-site:latest .
```

Start container with data sharing to communicate with other containers.
```
docker run -d -v shared-data:/data --name deenish-site deenish-site:latest
```
 
The task will run every ten minutes. Once it is finished, _in-situ_ observations are exported to a pickle file ```/data/pkl/BUOY.pkl```. The website will read the _in-situ_ data from this file.

## Deenish Island - MODEL container

This container is set to run hourly to download the model forecasts from Copernicus Marine. This data is wrapped in a MODEL.pkl file that is updated every hour and later accessed by the WEBAPP container through the shared volume.
   
Navigate to the Deenish Island - MODEL container
```
cd EuroSea/containers/Deenish-Island/model
```

Build image
```
docker build -t deenish-model:latest .
```

Start container with data sharing to communicate with other containers.
```
docker run -d -v shared-data:/data --name deenish-model deenish-model:latest
```
 
The task will run hourly at the time specified in the ```crontab``` file. Once it is finished, model forecasts are exported to a pickle file ```/data/pkl/MODEL.pkl```. The website will read the model forecasts from this file. 

## Deenish Island - CHL container

This container is set to run hourly to download the latest seawater chlorophyll-a concentration observations in Irish waters. The chlorophyll-a 
concentration is provided by the Atlantic Ocean Colour Bio-Geo-Chemical L4 Satellite Observations (https://doi.org/10.48670/moi-00288).
   
In addition, chlorophyll-a anomaly is determined as the difference between the actual chlorophyll-a concentration and a 60-day running median, ending two weeks before the current image (Tomlinson et al., 2004).

This application is set to run hourly to make sure that the website updates as soon as a new daily layer is released by the Copernicus Marine Service. This application also creates the figures that are later accessed by the WEBAPP container through the shared volume.

Navigate to the Deenish Island - CHL container
```
cd EuroSea/containers/Deenish-Island/chl
```

Build image
```
docker build -t chlorophyll:latest .
```

Start container with data sharing to communicate with other containers.
```
docker run -d -v shared-data:/data --name chlorophyll chlorophyll:latest
```

The task will run hourly at the time specified in the ```crontab``` file. Once it is finished, chlorophyll-a NetCDF files are downloaded to the ```/data/CHL``` folder, and CHL figures are exported as Plotly JSON strings to a pickle file  ```/data/pkl/CHL.pkl```. The website will read the CHL figures from this file. 

## Deenish Island - Red Band container

The Red Band Difference (RBD) algorithm is used as a proxy of relative chlorophyll-a fluorescence and is calculated as the difference between two red bands. As described by Amin et al. (2009) and tested in Irish waters by Jordan et al. (2021), the RBD algorithm is less sensitive to coloured dissolved organic matter, suspended particulate matter and atmospheric corrections, which makes it useful in both open and coastal waters. Daily figures are downloaded from NOAA and weekly composites are created every Monday. 

Navigate to the Deenish Island - RBN container
```
cd EuroSea/containers/Deenish-Island/rbn
```

Build image
```
docker build -t redband:latest .
```

Start container with data sharing to communicate with other containers.
```
docker run -d -v shared-data:/data --name redband redband:latest
```

The task will run daily at the time specified in the ```crontab``` file. Once it is finished, new daly Red Band images are downloaded to be published on the website.

## El Campello containers

The _in-situ_ and model forecast containers for El Campello are the same as those for Deenish Island and work identically. For El Campello, there is an additional wave forecasting product covering the Balearic Sea (see below). 

## El Campello - WAVES container

This container is set to run hourly to download the latest wave height forecasts from Copernicus Marine for the Balearic Sea. This application is set to run hourly to make sure that the website updates as soon as new forecasts are released by the Copernicus Marine Service. This application also creates a Plotly JSON figure that is later accessed by the WEBAPP container through the shared volume.

Navigate to the El Campello - WAVES container
```
cd EuroSea/containers/El-Campello/waves
```

Build image
```
docker build -t waves:latest .
```

Start container with data sharing to communicate with other containers.
```
docker run -d -v shared-data:/data --name waves waves:latest
```
 
The task will run hourly at the time specified in the ```crontab``` file. Once it is finished, wave forecasts are exported to a pickle file ```/data/pkl/CAMPELLO-WAVES.pkl```. The website will take the wave forecast figure (exported as a Plotly JSON string) from this file. 

## WEBAPP container

This container runs the website as a uwsgi-nginx-flask deployment. It loads the data files generated by the backend containers and provides the visualization on the website. It also provides access to the Historical Data requests for Deenish Island and El Campello. 

Navigate to the WEBAPP container
```
cd EuroSea/containers/webapp
```

Build image
```
docker build -t eurosea-webapp:latest .
```

Launch website
```
docker run -d --restart=on-failure --name=eurosea-webapp -p 80:80 -v /opt/cloudadm/multidocker/webapp:/app -v shared-data:/data eurosea.webapp:latest
```
