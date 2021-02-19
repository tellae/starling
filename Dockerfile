FROM ubuntu:20.04

# Install packages
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update --fix-missing
RUN apt-get install -yy -q software-properties-common
RUN apt-get install -yy -q libcurl4-gnutls-dev \
    libssl-dev libproj-dev libgdal-dev gdal-bin python3-gdal \
    libgdal-dev libudunits2-dev pkg-config libnlopt-dev libxml2-dev \
    libcairo2-dev gdal-bin libudunits2-dev \
    libgdal-dev libgeos-dev libproj-dev python3-pip python3-dev \
    build-essential libspatialindex-dev python3-rtree
RUN apt-get install -yy -q wget unzip

# Python packages
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

# create a non-root user
# give them the password "user" put them in the sudo group
RUN useradd -d /home/starling_user -m -s /bin/bash starling_user \
    && echo "starling_user:starling_user" | chpasswd && adduser starling_user sudo

# Directory
RUN mkdir starling_dir
WORKDIR /starling_dir

# Make the files owned by user
RUN chown -R starling_user:starling_user /starling_dir

# Install sudo
RUN apt-get -y install sudo

# Switch to your new user in the docker image
USER starling_user
