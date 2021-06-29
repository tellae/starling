# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

## 0.4.0 (2021-06-29)

### Added

- Shortest paths storing
- Possibility to provide a list of init input files
- PT delay information factory

### Changed
- Deprecated use of origin/destination_lat/lon, now fetching coordinates from geometry
- Now exporting KPI files to .gz compressed format

## 0.3.0 (2021-03-16)

### Added
- CHANGELOG file
- Online documentation, hosted by ReadtheDocs
- --which-result option for generate_osm_graph place import
- Common inputs scenarios for inputs shared between scenarios
- gzip compression/decompression
- Changed default visualisation file extension to .geojson.gz
- Added a 'request' column to the journeys DataFrame
- Added a confirm_journey_ method to Operator that replaces Traveler's make_journey_request_

### Changed
- Moved to osmnx 1.0.1
- Replaced the bz2_compress option by an automatic detection of .bz2 extension
- Moved the test demand in a common inputs folder
- The trips dict now also contain the agent serving it
- Switched to autoapi for the automatic documentation of the code

## 0.2.0 (2021-02-19)

### Added
- Test framework and scenarios for the models
- New parameter origin/destination_station/stop_point for some models' inputs
- Memory of failed stations in SB_VS users
- Simulation exceptions
- Simulation leave event and KPI
- New import methods generate_osm_graph script
- Run module that contains the launch functions
- Simulation agent traces file
- Mode resolution for each model
- Coordinates positions pre-processing using nearest_nodes
- New function for importing
- New functions for importing stop points

### Changed
- Graph extension is now an operator attribute
- Graph extension is done when nearest node is over a certain distance from coordinates.
- Example imports is now done by copying test scenarios

### Removed
- Zone attribute of OSMNetwork

## 0.1.1 (2021-01-05)

### Added
- Minor fixes (?)

## 0.1.0 (2020-12-11)

### Added
- First pre-release
