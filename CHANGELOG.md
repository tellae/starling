# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### 0.10.1 (2022-09-08)


### Features

* improve version and commit trace ([#68](https://github.com/tellae/starling/issues/68)) ([a679c68](https://github.com/tellae/starling/commit/a679c688150305a2268cac2792f0a2511a0dd28e))

## 0.10.0 (2022-08-18)


### ⚠ BREAKING CHANGES

* multiple scenarios run (#64)

### Features

* multiple scenarios run ([#64](https://github.com/tellae/starling/issues/64)) ([c98d2f6](https://github.com/tellae/starling/commit/c98d2f62ded4f134dc0e8e35e80dc7f075b36f43))

### 0.9.1 (2022-08-09)


### Features

* multiple scenarios ([#63](https://github.com/tellae/starling/issues/63)) ([4f29856](https://github.com/tellae/starling/commit/4f29856314b9beffdd4f35c6c24747a629ad3a6d))

## 0.9.0 (2022-08-02)


### ⚠ BREAKING CHANGES

* model classes are not specified in the following attributes of the SimulationModel subclasses: environment_class, population_class, input_class, output_class

* moved model elements initialisation in the parent SimulationModel class ([#62](https://github.com/tellae/starling/issues/62)) ([0f2e49e](https://github.com/tellae/starling/commit/0f2e49ef80a4ec25288c5382f07c7b53f3570a67))

## 0.8.0 (2022-07-28)


### ⚠ BREAKING CHANGES

* now provide path to the scenario folder instead of path to the simulation parameters to run a simulation

### Features

* scenario path management ([#61](https://github.com/tellae/starling/issues/61)) ([ccc6bb2](https://github.com/tellae/starling/commit/ccc6bb2fec95e5fb9c80230e4a044643baebc964))

### 0.7.12 (2022-06-23)


### Bug Fixes

* move file information generation to utils ([#58](https://github.com/tellae/starling/issues/58)) ([984babd](https://github.com/tellae/starling/commit/984babd7bbf462e8483104203f2010202a8a6d5a))

### 0.7.11 (2022-06-22)


### Features

* improve run summary ([#57](https://github.com/tellae/starling/issues/57)) ([d048a21](https://github.com/tellae/starling/commit/d048a2117761073d971b389bae34ad7a83538725))

### 0.7.10 (2022-05-09)


### Features

* agent number parameter ([#54](https://github.com/tellae/starling/issues/54)) ([fef3fd7](https://github.com/tellae/starling/commit/fef3fd7433dd824eadbe1aeef9e928307db5a449))

### 0.7.9 (2022-04-12)


### Bug Fixes

* missing date parameter crash ([#48](https://github.com/tellae/starling/issues/48)) ([10d5b03](https://github.com/tellae/starling/commit/10d5b03e28e9f761ca438c39079ddd2466f51b42))

### 0.7.8 (2022-04-08)


### Bug Fixes

* handle case when GTFS is not provided ([#47](https://github.com/tellae/starling/issues/47)) ([cd35969](https://github.com/tellae/starling/commit/cd35969451b36ac6628795f46e9086889ba8298e))

### 0.7.7 (2022-03-23)


### Features

* added a PlanningChange exception to interrupt service vehicle loops ([#46](https://github.com/tellae/starling/issues/46)) ([436039e](https://github.com/tellae/starling/commit/436039e2b2ca13a87456aab2aa06af099d20c7fc))

### 0.7.6 (2022-03-22)


### Bug Fixes

* long description content type ([#45](https://github.com/tellae/starling/issues/45)) ([ce0de89](https://github.com/tellae/starling/commit/ce0de89d90b0b4457aada7ca4523e65536e39f3c))

### 0.7.5 (2022-03-21)

### 0.7.4 (2022-03-17)


### Features

* input filepath ([#42](https://github.com/tellae/starling/issues/42)) ([e899bca](https://github.com/tellae/starling/commit/e899bca16b60b604bdefcd8affef385d21a9ba68))

### 0.7.3 (2022-03-14)


### Features

* unify parameters filename ([#41](https://github.com/tellae/starling/issues/41)) ([93fdd22](https://github.com/tellae/starling/commit/93fdd2250e70065bc49cd6329ced5d62456e7c56))

### 0.7.2 (2022-02-25)


### Features

* added a new config parameter 'stop_sequence_separator' ([6207cc5](https://github.com/tellae/starling/commit/6207cc5eb9fc3fd2004e88150d0ebea2bce6518a))

### 0.7.1 (2022-01-26)


### Bug Fixes

* isochrones ([#40](https://github.com/tellae/starling/issues/40)) ([b7aa65a](https://github.com/tellae/starling/commit/b7aa65a962aea409b290b83e75834085f71d16da))

## 0.7.0 (2021-12-13)


### ⚠ BREAKING CHANGES

* major changes in the inputs specifications, described with json schemas
Simulation parameters:
**gtfs_timetables** can no longer be null (None in Python)
**line_shapes** can no longer be null 
**routes** can no longer be null
**early_dynamic_input** can no longer be null
renamed **geojson_output** into **visualisation_output**
**routes** removed, now fetched in operation parameters (of relevant models)
**line_shapes_file** removed, now fetched in operation parameters
renamed **PT_parameters** into **user_routing_parameters**

PT_parameters (in simulation parameters, now renamed 'user_routing_parameters')

**journey_time_range** removed (now specified as a dispatcher option in operation parameters)
**max_nb_trips** removed (now specified as a dispatcher option in operation parameters)
**additional_transfers** removed (now specified as a dispatcher option in operation parameters)
**no_journey_timeout** removed (now using the **fail_timeout** param of Person class)
**nb_journey_trials** removed (now using the **max_tries** param of Person class)
**nb_seats** moved to PublicTransportOperator operation parameters
**service_vehicle_prefix** moved to PublicTransportOperator operation parameters
**use_shortest_path** moved to PublicTransportOperator operation parameters
**multi_source** moved to PublicTransportOperator operation parameters

### Features

* models schemas ([#32](https://github.com/tellae/starling/issues/32)) ([c2fe3b2](https://github.com/tellae/starling/commit/c2fe3b24af7193e9bcf28d2e49b0da73b3cdfa8f))

### 0.5.1 (2021-11-10)

## 0.5.0 (2021-11-10)

## 0.4.0 (2021-06-29)

### Added

- Shortest paths storing
- Possibility to provide a list of init input files
- PT delay information factory
- Added an environment variable OUTPUT_FOLDER to specify the output folder

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
