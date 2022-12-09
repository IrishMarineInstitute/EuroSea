# See https://opendrift.github.io for usage

FROM condaforge/mambaforge

ENV DEBIAN_FRONTEND noninteractive

RUN mkdir /code
WORKDIR /code

# Install opendrift environment into base conda environment
COPY environment.yml .
RUN mamba env update -n base -f environment.yml

# Install opendrift
ADD . /code
RUN pip install -e .

# Test installation
RUN /bin/bash -c "echo -e \"import opendrift\" | python"

RUN apt-get update && apt-get -y install cron vim

# Directory to store logging files
RUN mkdir /log

# Build data directory tree
RUN mkdir /data
RUN mkdir /data/pkl
RUN mkdir /netcdf

WORKDIR /root

# Set cron
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab

# Copy required files 
COPY [ "*.py" , "/root/" ]
COPY config .

RUN echo $PYTHONPATH

CMD ["cron", "-f"]
