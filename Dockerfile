FROM ubuntu:18.04

# Install packages
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -yy -q software-properties-common
RUN add-apt-repository -y ppa:ubuntugis/ppa
RUN apt-get update
RUN apt-get install -yy -q libcurl4-gnutls-dev \
    libssl-dev libproj-dev libgdal-dev gdal-bin python-gdal python3-gdal \
    libgdal-dev libudunits2-dev pkg-config libnlopt-dev libxml2-dev \
    libcairo2-dev gdal-bin python-gdal python3-gdal libudunits2-dev \
    libgdal-dev libgeos-dev libproj-dev python3-pip python3-dev \
    build-essential libspatialindex-dev python3-rtree

# Directory
RUN mkdir starling
WORKDIR /starling

# Python packages
COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN python3 -m pip install --upgrade pip
RUN pip3 install numba==0.51.2
