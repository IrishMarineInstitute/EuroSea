# EuroSea Data Portal

Welcome to the GitHub Repository of the EuroSea Data Portal. The EuroSea Data Portal is a project that aims at providing real-time oceanographic data and forecasts at the Deenish Island and El Campello monitoring sites. The website can be accessed at https://eurosea.marine.ie. 

This is a EuroSea partnership between the Marine Institute, the Spanish National Research Council (CSIC), Mowi Ireland (formerly Marine Harvest) and Xylem / Aanderaa Data Instruments. This part of the Marine Observatory work is being developed within the WP6 Ocean Health Demonstrator of the EuroSea project “Improving and integrating the European Ocean Observing and Forecasting System”. This project is funded by the EU Horizon 2020 research and innovation programme under grant agreement No 862626.

# Installation

These instructions have been tested on Ubuntu 18.04.6 LTS (Bionic Beaver). First, download the code with: 

```
git clone https://github.com/IrishMarineInstitute/EuroSea.git
```

The code is structured in multiple Docker containers that communicate with each other through a shared volume. The next step is to initialize each container. ``` crontab ``` is used to schedule tasks and ensure that the website updates on a regular basis. The containers work independently, so there is no need to initialize them in a specific order.

## Deenish Island - SST container

This container is set to run hourly to download the latest sea surface temperature observations for the Irish EEZ. The sea surface temperature is provided by the 
Operational Sea Surface Temperature and Ice Analysis (OSTIA) system run by the UK's Met Office and delivered by IFREMER.

In addition, sea surface temperature anomalies are calculated using a 40-year baseline reference climatology. The occurrence of marine heat waves is determined using the Hobday et al. (2016) definition.

This application is set to run hourly to make sure that the website updates as soon as a new daily layer is released by the Copernicus Marine Service. This application also creates the figures that are later accessed by the WEBAPP container through the shared volume.

Navigate to the Deenish Island - SST container
```
cd EuroSea/containers/Deenish-Island/sst
```

Build image
```
sudo docker build -t eurosea-sst:latest .
```

Start container with data sharing to communicate with other containers.
```
sudo docker run -d -v shared-data:/data --name eurosea-sst eurosea-sst:latest
```

The task will run hourly at the time specified in the ```crontab``` file. Once it is finished, sea surface temperature NetCDF files are downloaded to the ```/data/SST``` folder, and a pickle file  ```/data/pkl/SST.pkl``` should exist. The website will read the SST figures from this file.


