# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Rewrite to class-based converters
- Converters for Spain: Aragon, Andalusia, Balearic Islands, Basque Country, Catalonia, Cantabria, Castilla y León, Castilla-La Mancha, Canary Islands, Extremadura, Galicia, Madrid, Navarra, Valencia
- Start to use `https://fiboa.org/code/` prefixed codes for our own code lists
- Use only unix line-endings in source files
- Use set instead of list for Converter.extensions

## [v0.9.0] - 2025-01-07

### Added

- Command `fiboa improve` with helpers to
  - change the CRS
  - change the GeoParquet version and compression
  - fill missing perimeter/area values
  - fix invalid geometries
  - rename columns
- Converter for Lithuania (EuroCrops)
- Converter for Slovenia
- Converter for Slovakia
- Converter for Switzerland
- Converter for Czech
- Converter for US Department of Agriculture Crop Sequence Boundaries
- Converter for California (US) Statewide Crop Mapping
- Converter for Latvia (from original source)
- Converter for Japan, currently based on supplied (non-fiboa) parquet files
- Many converters implement the admin extension
- `fiboa convert`: New parameter `--original-geometries` / `-og` to keep the original geometries

### Changed

- `fiboa convert`:
  - Writes custom schemas to collection metadata
  - Geometries are made valid using GeoPanda's `make_valid` method by default
  - MultiPolygons are converted to Polygons by default
- `fiboa validate` uses custom schemas for validation
- `fiboa merge` keeps custom schemas when needed
- Extended converter for Croatia; with crop_code and crop_name
- Many converters implement the admin extension

### Removed

- `fiboa convert`: Removed the explicit parameter `explode_multipolygon` from the converter

### Fixed

- Fix converter for Estland to use the id `ec_ee` instead of `ec_es`
- Assure tests don't download external sources

## [v0.8.0] - 2024-11-12

### Added

- Merge command: `fiboa merge`
- Converter for Croatia
- Converter for Germany, Mecklenburg-Western Pomerania
- Converter for Germany, Saarland
- Converter for Germany, Saxony
- Converter for Estonia (EuroCrops)
- Converter for Sweden
- Converter for Luxembourg
- Converter for Ireland
- Converter for Lacuna Labels (A region-wide, multi-year set of crop field boundary labels for Africa)
- Require changelogs for Pull Requests

### Changed

- `fiboa convert`: Default compression changed from `zstd` to `brotli`
- The default row group size of exported parquet files was changed from ~1.000.000 to 25.000

### Fixed

- Datatype conversion from pandas to pyarrow fixed

## [v0.7.0] - 2024-08-24

### Added

- Converter for Luís Eduardo Magalhães (LEM) and other municipalities in the west of Bahia state, Brazil (`br_ba_lem`)
- Converter for Denmark (`dk`)
- Additional converters for EuroCrops datasets: `ec_be_vlg`, `ec_nl_crop`
- New parameter `--geoparquet1` to generate GeoParquet 1.0 without bbox column instead of GeoParquet 1.1 with bbox column

### Changed

- CLI creates GeoParquet 1.1 with bbox column by default
- The function signature in the `convert` function of the converters has changed to a simpler more future-proof variant.
- The EuroCrops converters extend the original converters

### Fixed

- `fiboa convert`: Create output folder if it doesn't exist
- Strip whitespaces/newlines from created STAC collections
- `fiboa create-geojson`: Don't write FeatureCollections to folder if a filename is given

## [v0.6.0] - 2024-07-25

### Added

- Added a `SHORT_NAME` variable to the converter template
- Added a `FILE_MIGRATION` variable to the converter template for per-file migrations
- Added a `LAYER_FILTER` variable to the converter template for loading specific layers from a file
- Added `-i` parameter to specify input files for converters
- `fiboa converters` output can be customized with options `-p`, `-s` and `-v`.
- `fiboa convert` reads JSON file with custom logic, which allows to access nested objects through dot notation
- Converter for Slovenia via EuroCrops (`ec_lv`)
- Converter for Planet's Automated Field Boundary (`planet_afb`)
- Converter for Portugal (`pt`)
- Converter for Varda FieldID (`varda`)
- Converter for DigiFarm (`digifarm`)
- Converter for AI4SmallFarms in Cambodia and Vietnam (`ai4sf`)
- Further tests

### Changed

- The `BBOX` is optional in the converter template as it will be computed automatically from the data.
- The `PROVIDER_NAME` and `PROVIDER_URL` variables in the converter template were replaced by `PROVIDERS`
- `fiboa converters` is more readable by default
- Upgraded to geopandas 1.0.0, which migrates from fiona to pyogrio for data loading
- The EuroCrops converters (prefix: `ec_`) use the HCAT fiboa extension

### Fixed

- Fixed schema issue for the `tk10` column in `de_bb` converter
- jsonschema library doesn't warn against external references any longer

## [v0.5.0] - 2024-06-17

### Added

- Basic support for `patternProperties` in GeoParquet creation
- The converter template accepts multiple input URLs
- Added parameter to explode multipolygons to polygons (`explode_multipolygon`, default: `False`)
- Converter for Belgium, Flanders (`be_vlg`)
- Converter for Belgium, Wallonia (`be_wa`)
- Converter for Finland (`fi`)
- Converter for France (`fr`)
- Converter for The Netherlands (`nl` and `nl_crops`)
- Converter for Slovenia via EuroCrops (`ec_si`)

### Changed

- The `--cache` option for the `convert` command asks for a folder instead of a file
- The `cache_file` parameter in converters has been renamed to `cache` (requires changes in the converter templates)
- The converter template allows for more detailed source information
- The `URI` constant in the template was renamed to `SOURCES` (requires changes in the converter templates)

### Fixed

- Extensions were not correctly displayed in `describe` and `validate` command
- Fixed regular expressions for email and uuid in data validation

## [v0.4.0] - 2024-05-10

### Added

- Converter for France via EuroCrops (`ec_fr`)
- `fiboa create-geojson`: Show conversion progress
- `fiboa jsonschema` and `fiboa validate`: Support `geometryTypes` for `geometry` data type in GeoJSON
- `fiboa validate`:
  - Basic validation for objects, geometries and bounding boxes in GeoParquet files

### Fixed

- `fiboa validate-schema`: The `-m` option is applied correctly if `$schema` is present in schema
- `fiboa validate` and `fiboa validate-schema`: Don't stop validation after the first file.
- `fiboa validate`:
  - Is more robust against invalid collections and doesn't abort if not needed
  - Check NULL values correctly in case of arrays
  - Throw an error if no files were provided
- `fiboa create-geojson`:
  - Handles GeoParquet bbox correctly
  - Converts numpy arrays
  - Doesn't export empty collections
- Fix recursive import

## [v0.3.10] - 2024-05-06

### Added

- `fiboa convert`:
  - Added step that allows to set constant values (`ADD_COLUMNS`)
  - Support for reading GeoParquet files
  - Help lists all available converters
- `fiboa converters`: More detailed list of available converters/datasets

### Changed

- `fiboa convert`:
  - `determination_datetime` is not required any longer
  - Default compression changed from `brotli` to `zstd`

## [v0.3.9] - 2024-05-01

### Fixed

- JSON Schema and GeoJSON validation also errors when the data doesn't comply to the given formats

## [v0.3.8] - 2024-04-27

### Added

- Converter for Thuringia, Germany (`de_th`)

### Fixed

- Fixed GeoJSON to GeoParquet conversion of the `date` data type

## [v0.3.7] - 2024-04-25

### Fixed

- Small fixes in CLI output and docs

## [v0.3.6] - 2024-04-24

### Added

- `fiboa describe`: New parameters `--column` and `--num`

### Changed

- `fiboa create-geoparquet`: Allow collection creation based on parameters and define clear priority of collection inputs

### Fixed

- `fiboa describe`: Show all columns / don't hide data with `...`
- `fiboa validate`: Warn more clearly if no schema is defined for a column

## [v0.3.5] - 2024-04-22

### Added

- Converters: Allow to filter rows with pandas Series operations easily

### Fixed

- Support converting to array data type

## [v0.3.4] - 2024-04-19

### Added

- Validate GeoParquet metadata

### Changed

- Load schemas for GeoParquet and STAC based on given version numbers

### Fixed

- Fix missing license issue for AT converter

## [v0.3.3] - 2024-04-12

### Changed

- Update converters for Germany to use the flik extension

### Fixed

- Provide more details in data validation messages
- Fix issue with `get_pyarrow_type_for_geopandas`
- Fix missing schemas issue for AT converter

## [v0.3.2] - 2024-04-12

### Added

- `fiboa rename-extension` to quickly replace template placeholders in new extensions

## [v0.3.1] - 2024-04-11

### Added

- Support for enums and GeoParquet structs
- `fiboa convert`: Allow data of the GeoDataFrame or individual columns to be changed via custom functions

### Fixed

- `fiboa create-geoparquet`: Handle column conversion more gracefully
- `fiboa validate`: Don't fail collection test if something unexpected happened
- `fiboa create-geojson`: Option `-f` doesn't need a value any longer
- `fiboa convert`: Fixed invalid method call

## [v0.3.0] - 2024-04-10

### Added

- Command to validate the fiboa schemas (`fiboa validate-schema`)
- Command to create GeoJSON from GeoParquet (`fiboa create-geojson`)
- Converter for Austria (`at`)
- Converter for Berlin/Brandenburg, Germany (`de_bb`)
- Converter for Schleswig Holstein, Germany (`de_sh`)
- Converter for Lower Saxony, Germany (`de_nds`)

### Changed

- Renamed `fiboa create` to `fiboa create-geoparquet`
- The `--collection` parameter is not needed anylonger if the collection can be
  read directly from the GeoJSON files
  (`fiboa` property or link with relation type `collection`)

### Fixed

- Several minor improvements for the conversion process

## [v0.2.1] - 2024-04-02

### Fixed

- Fixed the field boundary generation for de-nrw, which was pointing at the wrong dataset.

## [v0.2.0] - 2024-04-02

### Added

- Converter framework (`fiboa convert`)
- Converter for North Rhine-Westphalia, Germany (`de_nrw`)

### Fixed

- Validator for GeoParquet recognizes missing fields
- `--json` option for describe command doesn't throw error

## [v0.1.1] - 2024-03-27

- Add experimental data validation support for GroParquet files

## [v0.1.0] - 2024-03-27

- Add `describe` command to inspect fiboa GeoParquet files
- Add `jsonschema` command to create JSON Schema from fiboa schema
- Add validateion for GeoJSON

## [v0.0.9] - 2024-02-28

- Support string enums

## [v0.0.8] - 2024-02-28

- Fixed reading GeoJSON FeatureCollections

## [v0.0.7] - 2024-02-23

- Allow folders to be specified as input files [#3](https://github.com/fiboa/cli/issues/3)

## [v0.0.6] - 2024-02-23

- Add `-e` option for create command to support extension schema mapping to local files

## [v0.0.5] - 2024-02-23

- Add `-e` option for validate command to support extension schema mapping to local files

## [v0.0.4] - 2024-02-23

- Adds missing dependencies

## [v0.0.3] - 2024-02-23

- Use extension schemas for conversion
- Correctly write the Parquet schema and columns - workaround for <https://github.com/geopandas/geopandas/issues/3182>

## [v0.0.2] - 2024-02-16

- Basic validation for collection
- Minimal validation for data
- Fixed creation of GeoParquet files

## [v0.0.1] - 2024-02-16

- First release

[Unreleased]: <https://github.com/fiboa/cli/compare/v0.9.0...main>
[v0.9.0]: <https://github.com/fiboa/cli/compare/v0.8.0...v0.9.0>
[v0.8.0]: <https://github.com/fiboa/cli/compare/v0.7.0...v0.8.0>
[v0.7.0]: <https://github.com/fiboa/cli/compare/v0.6.0...v0.7.0>
[v0.6.0]: <https://github.com/fiboa/cli/compare/v0.5.0...v0.6.0>
[v0.5.0]: <https://github.com/fiboa/cli/compare/v0.4.0...v0.5.0>
[v0.4.0]: <https://github.com/fiboa/cli/compare/v0.3.10...v0.4.0>
[v0.3.10]: <https://github.com/fiboa/cli/compare/v0.3.9...v0.3.10>
[v0.3.9]: <https://github.com/fiboa/cli/compare/v0.3.8...v0.3.9>
[v0.3.8]: <https://github.com/fiboa/cli/compare/v0.3.7...v0.3.8>
[v0.3.7]: <https://github.com/fiboa/cli/compare/v0.3.6...v0.3.7>
[v0.3.6]: <https://github.com/fiboa/cli/compare/v0.3.5...v0.3.6>
[v0.3.5]: <https://github.com/fiboa/cli/compare/v0.3.4...v0.3.5>
[v0.3.4]: <https://github.com/fiboa/cli/compare/v0.3.3...v0.3.4>
[v0.3.3]: <https://github.com/fiboa/cli/compare/v0.3.2...v0.3.3>
[v0.3.2]: <https://github.com/fiboa/cli/compare/v0.3.1...v0.3.2>
[v0.3.1]: <https://github.com/fiboa/cli/compare/v0.3.0...v0.3.1>
[v0.3.0]: <https://github.com/fiboa/cli/compare/v0.2.1...v0.3.0>
[v0.2.1]: <https://github.com/fiboa/cli/compare/v0.2.0...v0.2.1>
[v0.2.0]: <https://github.com/fiboa/cli/compare/v0.1.1...v0.2.0>
[v0.1.1]: <https://github.com/fiboa/cli/compare/v0.1.0...v0.1.1>
[v0.1.0]: <https://github.com/fiboa/cli/compare/v0.0.9...v0.1.0>
[v0.0.9]: <https://github.com/fiboa/cli/compare/v0.0.8...v0.0.9>
[v0.0.8]: <https://github.com/fiboa/cli/compare/v0.0.7...v0.0.8>
[v0.0.7]: <https://github.com/fiboa/cli/compare/v0.0.6...v0.0.7>
[v0.0.6]: <https://github.com/fiboa/cli/compare/v0.0.5...v0.0.6>
[v0.0.5]: <https://github.com/fiboa/cli/compare/v0.0.4...v0.0.5>
[v0.0.4]: <https://github.com/fiboa/cli/compare/v0.0.3...v0.0.4>
[v0.0.3]: <https://github.com/fiboa/cli/compare/v0.0.2...v0.0.3>
[v0.0.2]: <https://github.com/fiboa/cli/compare/v0.0.1...v0.0.2>
[v0.0.1]: <https://github.com/fiboa/cli/tree/v0.0.1>
