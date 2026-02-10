# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [1.3.0](https://github.com/tellae/starling/compare/v1.2.3...v1.3.0) (2026-02-10)


### Features

* new operator method closest_stop_points ([#141](https://github.com/tellae/starling/issues/141)) ([5245f5d](https://github.com/tellae/starling/commit/5245f5dccb7a14126391f34297f8a8a8d50bb1fe))

## [1.2.3](https://github.com/tellae/starling/compare/v1.2.2...v1.2.3) (2025-10-23)


### Bug Fixes

* error in read of topology info ([#138](https://github.com/tellae/starling/issues/138)) ([aae3fb1](https://github.com/tellae/starling/commit/aae3fb1b244ad41514b6165a4a6e0db3f460281c))


### Documentation

* remove mention of Starling being unusable as a package ([26c8179](https://github.com/tellae/starling/commit/26c81792e3d10ff19f8587ef504b2ee8aba3743b))

## [1.2.2](https://github.com/tellae/starling/compare/v1.2.1...v1.2.2) (2025-10-23)


### Bug Fixes

* remove starling import in setup.py ([50fde8e](https://github.com/tellae/starling/commit/50fde8e0e385cdf377a873e2fe08370783489605))

## [1.2.1](https://github.com/tellae/starling/compare/v1.2.0...v1.2.1) (2025-10-22)


### Bug Fixes

* add deprecation message to run.py ([23c8f96](https://github.com/tellae/starling/commit/23c8f96211a3017a3bbf9f32295021dbc50cfd97))

## [1.2.0](https://github.com/tellae/starling/compare/v1.1.0...v1.2.0) (2025-10-22)


### Features

* add a command line interface to Starling ([#128](https://github.com/tellae/starling/issues/128)) ([3e7dc3a](https://github.com/tellae/starling/commit/3e7dc3afe11aaf3be8353a6553b9d206f0c9bcbe))
* add zipping commands ([#132](https://github.com/tellae/starling/issues/132)) ([75b5df9](https://github.com/tellae/starling/commit/75b5df9f8493ff95cba8fb71434870d972ed73d4))
* allow calling a preprocessing function before running a simulation ([#133](https://github.com/tellae/starling/issues/133)) ([8b5921e](https://github.com/tellae/starling/commit/8b5921e4efc75e08ab761a4b948f77545665fd91))


### Bug Fixes

* add missing requirement for the loguru library ([#129](https://github.com/tellae/starling/issues/129)) ([ba07c68](https://github.com/tellae/starling/commit/ba07c683d8576a49b5899737df1c0b5640c2acfb))
* fixed evaluation of active gtfs stops ([#125](https://github.com/tellae/starling/issues/125)) ([254ec8b](https://github.com/tellae/starling/commit/254ec8bc266c1e747e95822afe44734f2513d585))
* fixed PT path evaluation when using line shapes file ([#126](https://github.com/tellae/starling/issues/126)) ([dd73868](https://github.com/tellae/starling/commit/dd73868a75b2a1172e563d29bcf76ae772c6b596))

## [1.1.0](https://github.com/tellae/starling/compare/v1.0.1...v1.1.0) (2025-04-28)


### Features

* edge speeds improvements ([#120](https://github.com/tellae/starling/issues/120)) ([cd2fc88](https://github.com/tellae/starling/commit/cd2fc88211f8bcaeb262677689db7b581ed64bc5))


### Bug Fixes

* add stop position to StopEvent attributes ([#117](https://github.com/tellae/starling/issues/117)) ([9b7d249](https://github.com/tellae/starling/commit/9b7d2498fdc4c1501537dfdce896e3fbfb8f15f8))
* error from path store initialisation ([#121](https://github.com/tellae/starling/issues/121)) ([8e41963](https://github.com/tellae/starling/commit/8e41963e7a5eb3a66355f7185cf7f85d74597601))

## [1.0.1](https://github.com/tellae/starling/compare/v1.0.0...v1.0.1) (2025-03-19)


### Bug Fixes

* error in test_simulation_events ([#114](https://github.com/tellae/starling/issues/114)) ([3d588f6](https://github.com/tellae/starling/commit/3d588f6e723bb6db097902f0206810974050db2e))
* SimulationEvents now reads compressed events file ([#116](https://github.com/tellae/starling/issues/116)) ([c709914](https://github.com/tellae/starling/commit/c709914affa960fc1af2402ea8b9ef8b81e652f6))

## [1.0.0](https://github.com/tellae/starling/compare/v0.11.7...v1.0.0) (2025-03-19)


### ⚠ BREAKING CHANGES

* for the need of this feature, the Event sub classes have been modified, and the "trace" file generation has been impacted. Parsing of the "traces" file will probably break.

### Features

* new event file output ([#112](https://github.com/tellae/starling/issues/112)) ([c044000](https://github.com/tellae/starling/commit/c044000699e2383581e13a96d755dc2d1e526d18))

## [0.11.7](https://github.com/tellae/starling/compare/v0.11.6...v0.11.7) (2025-01-20)


### Bug Fixes

* fixed an error occuring when trips had different stop sequence minimums ([#110](https://github.com/tellae/starling/issues/110)) ([15322cd](https://github.com/tellae/starling/commit/15322cd804e28b3ff3a5c77f79b524bd738190cd))
* revert change of demand "icon" into "icon_type" ([#108](https://github.com/tellae/starling/issues/108)) ([177dfaf](https://github.com/tellae/starling/commit/177dfaf088fec944a91b4e19f04c88e59bae7ad7))

## [0.11.6](https://github.com/tellae/starling/compare/v0.11.5...v0.11.6) (2024-12-09)


### Bug Fixes

* remove unused files ([#103](https://github.com/tellae/starling/issues/103)) ([e4e19f2](https://github.com/tellae/starling/commit/e4e19f28aeeee04f3971c914153d140bf752f0a9))

### 0.11.5 (2024-12-09)

### 0.11.4 (2024-11-28)

### 0.11.3 (2024-10-21)


### Bug Fixes

* change default value of "stop_sequence_separator" config to ";" ([#94](https://github.com/tellae/starling/issues/94)) ([c0cd1c5](https://github.com/tellae/starling/commit/c0cd1c5a76cf73802880de52295fe770a6781c16))

### 0.11.2 (2024-05-27)


### Features

* time profiled KPIs ([#92](https://github.com/tellae/starling/issues/92)) ([7ef4b24](https://github.com/tellae/starling/commit/7ef4b24e8747175bbf2eec27a40ca2c27c59942a))

### 0.11.1 (2024-01-08)


### Bug Fixes

* position_in_zone is now correctly returns self without zone ([#91](https://github.com/tellae/starling/issues/91)) ([1d66c5e](https://github.com/tellae/starling/commit/1d66c5e0bd49fd7848e863390f2665f99d217883))

## 0.11.0 (2023-12-14)


### ⚠ BREAKING CHANGES

* improve stop points initialization (#90)

### Features

* improve stop points initialization ([#90](https://github.com/tellae/starling/issues/90)) ([b62d07f](https://github.com/tellae/starling/commit/b62d07fcb345c6b39d6e74afd4aaac72f2a108ef))

### 0.10.20 (2023-11-29)


### Bug Fixes

* error in Python3 only classifier ([0746c23](https://github.com/tellae/starling/commit/0746c2340bc4318695e2749bda86d655973fe775))

### 0.10.19 (2023-11-27)

### 0.10.18 (2023-11-20)

### 0.10.17 (2023-11-16)


### Features

* **io:** agent can now be duplicated using 'duplicates' attribute ([#87](https://github.com/tellae/starling/issues/87)) ([c13481a](https://github.com/tellae/starling/commit/c13481ae8c487b33a4a302ce15845ca4d07f935e))

### 0.10.16 (2023-10-24)

### 0.10.15 (2023-10-19)


### Bug Fixes

* missing SB_VS_R adaptations with previous changes in depot use ([#84](https://github.com/tellae/starling/issues/84)) ([2fd15ee](https://github.com/tellae/starling/commit/2fd15eeb4b65be5c77a6ac76c765b587213b46d1))

### 0.10.14 (2023-10-19)


### Bug Fixes

* service vehicle depot was fetch at wrong place during input generation ([#83](https://github.com/tellae/starling/issues/83)) ([1062197](https://github.com/tellae/starling/commit/10621977db0d96bbdc9dc12301ffa5b7ee6b348e))

### 0.10.13 (2023-08-10)

### 0.10.12 (2023-03-13)

### 0.10.11 (2023-03-09)


### Bug Fixes

* rename reference files after naming change in previous commit ([#77](https://github.com/tellae/starling/issues/77)) ([31e09bc](https://github.com/tellae/starling/commit/31e09bc8f0c3aab705ca89cdfe319284b70f7f54))

### 0.10.10 (2023-01-25)

### 0.10.9 (2023-01-13)


### Bug Fixes

* fixed a bug in SB_VS when user patience was None ([bd2f5a0](https://github.com/tellae/starling/commit/bd2f5a02f92cb770994e2c72d53093484a78f57b))

### 0.10.8 (2022-11-25)


### Features

* improvements on service vehicle methods ([#75](https://github.com/tellae/starling/issues/75)) ([62c48b4](https://github.com/tellae/starling/commit/62c48b417b8e314c8ca958589b9efc08f5cdeeb0))

### 0.10.7 (2022-11-07)


### Bug Fixes

* update sphinx version ([e626e8b](https://github.com/tellae/starling/commit/e626e8b53b418af6b2e849e2823ff9fcba8a233b))

### 0.10.6 (2022-11-07)


### Features

* public transport model ([#73](https://github.com/tellae/starling/issues/73)) ([4f007be](https://github.com/tellae/starling/commit/4f007beff4484ca3dc5a6fe18163da8a0e9ad627))

### 0.10.5 (2022-10-20)


### Bug Fixes

* remove wrong imports ([#72](https://github.com/tellae/starling/issues/72)) ([7ece11d](https://github.com/tellae/starling/commit/7ece11d547e5cdc93176ba7a092733df621e0f1a))

### 0.10.4 (2022-10-19)


### Features

* journey refactor ([#71](https://github.com/tellae/starling/issues/71)) ([3f1d0f0](https://github.com/tellae/starling/commit/3f1d0f0c6b49560d17ba2957a3111cee84a6ac47))

### 0.10.3 (2022-10-13)

### 0.10.2 (2022-09-15)


### Features

* add possibility of generating an empty graph ([#69](https://github.com/tellae/starling/issues/69)) ([d08b0f2](https://github.com/tellae/starling/commit/d08b0f209c0a8df8d353095d07f16d39e890dd26))

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
