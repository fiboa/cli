# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Declare the beautifulsoup4 dependency the ES-PV and ES-VC converters import
- ES-CL: the ITACyL server is https-only, the 2025 shapefiles sit in province subfolders, and C_REFREC is the identifier
- A test refuses a fixture above 5 MB, committed or merely lying in the fixture folder, because a failing convert test downloads the real source there
- ES-MD: find RECINTO.shp wherever the archive puts it
- DK: support editions 2008-2026; older editions use row numbering for IDs, and 2008/2009 publish without crop and HCAT because the source has no crop columns
- PT: the 2025 edition, whose layers, crop column and area units all changed, and CUL_ID as the identifier
- US CSB: editions 2017-2024 from the single archive, and numbered fields because the dissolve leaves no source identifier
- ES-AR: per-municipality SIGPAC files listed from IDEAragon
- LT: read Europe-LAND v1.3, which carries 2025 beside 2024
- ES-GA: editions 2014-2026 with per-campaign column names, determination date from the variant, and pasto arbustivo excluded before the 2023 campaign
- EC-SI: stop requiring columns the source leaves empty, and require only what every parcel carries
- EC-LV: stop requiring columns the source leaves empty
- ES-AN: CD_USO is the land-use column, with the determination date from the variant year
- HR: editions 2011-2024; the archives leave their CRS undefined and carry ARKOD's own parcel id, which the row index used to overwrite
- NL: the full BRP series 2009-2026 — the 2009-2019 zips hold a FileGDB with differently prefixed columns, 2020 is a GeoPackage, and the download moved to a new PDOK location
- SI: editions back to 2019 — the archives differ per campaign in their folder layout, CRS declaration, column names and crop-code padding
- BE-WAL: match the crop by name where EuroCrops' table leaves the code empty, which covered 6.79% of the collection
- CZ: find the shapefile in nested archive folders (2026)
- CZ: read the 2019-2022 editions (GPZ_DP: renamed crop and area columns, no application date, ENTITA_ID is the land block), recover the crop codes the 2020 edition leaves empty, map the 167 crop codes EuroCrops does not carry, and publish a declaration that straddles two land blocks once
- BE-VLG: editions 2018-2026; REF_ID is published as block_id and the row index identifies the field, the QGIS styles table in the 2026 GeoPackage is skipped, and the 2020 archive is read as cp1252 with its CRS declared
- FI: one variant per year (2020-2025) instead of a hard-coded 2023, with the year in the cache name
- AT: extract the archive instead of reading the GeoPackage through /vsizip, which never finished for 2018
- SK: KODKD is the LPIS block code (non-unique, sometimes empty), so it is kept as block_id and the row index identifies the field
- EC-LT: repair the Lithuanian crop names, which the release ships read through the wrong code page, and map them through a corrected table — Šlapynės (wetlands) was published as spinach
- EC-LT: nothing in the release identifies a parcel, so the row index does
- ES-CM: read the year-named SIGPAC service, whose id field is OBJECTID_1, with the determination date from the variant
- ES-CN: the seven island files each kept their own row index, and the region was declared as Cantabria
- EC-EE: name the shapefile inside the archive, migrate the year column the release actually has, and require only what every parcel carries
- ES-CAT: the 2024 download is a shapefile package, and 34 crop names new in that edition are mapped
- DE-NDS: give the collection an id (the row index), which it was published without
- DE-BB: ref_ident holds the FLIK (field block reference), not a farmer, and the shapefile is cp1252
- JP: editions 2021-2024, each with the determination date of the parcel rather than a constant
- PerFileBaseConverter: convert a multi-file source one file at a time and merge the parts, so a dataset larger than memory can be converted; used by the Spain-wide converter
- FiboaDuckDBBaseConverter: convert a source that is already Parquet with SQL, without loading it into memory
- Update vecorel-cli to v0.2.17:
  - GeoJSON is read as UTF-8 as the format mandates, instead of the platform locale (cp1252 on Windows mangled umlauts)
  - GeoJSON files with a byte order mark no longer fail to read
  - Drop the per-converter UTF-8 workarounds in de_bw and de_he, now redundant
- Converter for Spain (whole), based on the FEGA 2025+ data
- Add Italy Tuscany (IT-1) basd on EuroCrops v2
- Suuport multiple years for CZ
- Multiple years for DE_sh
- Multiple year support for HR
- Introduce FiboaBaseConverter.use_variant_as_determination for setting proper determination_date
- Update fr-converter to support 2021/2022 files
- Converter for Baden-Württemberg, Germany (GISELa LPIS reference parcels, 2018-2022)
- Converter for Lithuania KŽS reference parcels (lt_kzs), reading the geoportal.lt ArcGIS REST service
- Support Esri JSON and server-side filters in EsriRESTConverterMixin (rest_format, rest_params["where"])
- Converter for Bavaria, Germany LPIS field blocks (de_by_block)
- Converter for Hesse, Germany LPIS reference parcels
- Converter for Saxony-Anhalt, Germany LPIS field blocks (de_st)
- Converter for Saarland, Germany LPIS field blocks (de_sl_block)
- Fix parcel sizes written in scientific notation being read 10,000x too large (de_sl_block parser)
- Repair the Saarland, Germany converter (de_sl), which could no longer read its source at all.
  It now pages through the whole dataset, where the previous six hardcoded bounding boxes reached
  only 20,300 of 54,038 parcels, so earlier output was incomplete. `metrics:area` is derived from
  the geometry, because the service stopped publishing the declared size.
- Converter for South Tyrol, Italy (it_bz), reading the province's LAFIS utilised agricultural area
- Repair the Saxony, Germany converter (de_sax): only the current year's archive is served, so the
  2024 edition it read is gone. It now reads 2026, and a test fixture covers the dataset.
- Update vecorel-cli to v0.2.16:
  - Converter output is sorted by Hilbert distance
  - Commands exit with a non-zero exit code when they report a failure
  - Collection-only properties are kept when merging collections
  - Default GeoParquet compression is now zstd (level 15), configurable via `--compression_level`
- DE-SH: make the 2023, 2025 and 2026 editions convert — glob the GeoPackage inside the archive (2023 was written with user_version = 0, so the archive alone matches no driver), parse fachguelti as DD.MM.YYYY, and map the 2023 and upper-case 2025/2026 column spellings that silently dropped determination:datetime and metrics:area (their area is text with a decimal comma)
### Added
- Added `FiboaDuckDBBaseConverter` for SQL-based conversion of large Parquet sources.
- Added `PerFileBaseConverter` to process multi-file sources incrementally.
- Added support for supplementary HCAT/crop mappings via `ec_mapping_supplements`.
- Added support for Esri JSON output and server-side filters in REST converters.
- Added a test guard that rejects fixture files larger than 5 MB.
- AT: Added support for 2018 by extracting archives before reading.
- DE-BW: Added Baden-Württemberg reference parcels converter.
- DE-BY-BLOCK: Added Bavaria field-block converter.
- DE-HE: Added Hesse reference parcels converter.
- DE-SL-BLOCK: Added Saarland field-block converter.
- DE-ST: Added Saxony-Anhalt field-block converter.
- ES: Added Spain-wide converter based on FEGA 2025+.
- IT-1: Added Tuscany converter based on EuroCrops v2.
- IT-BZ: Added South Tyrol converter.
- LT-KZS: Added Lithuania KŽS reference parcels converter.
- PL:
  - Added `pl` with campaigns 2025 and 2026 from ARiMR's declared-crop dataset.
  - Added `pl_block` with Poland LPIS maximum eligible area parcels from ARiMR.

### Changed
- `fiboa publish` no longer uploads to S3 or generates README/LICENSE files. It now creates GeoParquet, PMTiles and a STAC Collection with relative links, checksums and web-map-links.
- Updated `aiohttp` to support Zenodo responses that include both returned `Content-Type` headers.
- Improved geometry axis handling so generated tiles and bounding boxes keep x/y order consistent in output.
- Updated vecorel-cli to 0.2.16, 0.2.17, 0.2.18 and 0.2.20, including improved validation defaults and latest-variant selection when `--variant` is not provided.
- BE-VLG: Extended editions to 2018-2026 and aligned determination dates with the selected campaign year.
- CZ: Extended year coverage, including GPZ_DP editions (2019-2022), and added 2026 nested-archive support.
- DE-SH: Extended support to editions 2023, 2025 and 2026.
- DK: Added 2025 and 2026 editions.
- ES:
  - ES regions based on SIGPAC now publish `hcat:code` from land-use mapping.
  - ES-AR now reads municipality SIGPAC sources listed by IDEAragon.
  - ES-GA now supports editions 2014-2026.
- FI: Editions are now available by year (2020-2025).
- FR: Updated converter support for 2021 and 2022 files.
- HR: Editions now cover 2011-2024.
- LV:
  - Editions now cover 2015-2025 from yearly data.gov.lv releases.
  - `block_id` is published from the field-block identifier and `crop:name` comes from the official code list.
  - The merged code list at https://fiboa.org/code/lv/lv.csv now includes the 34 post-2021 added codes.
  - URL discovery now requires all nine regional GeoPackages to avoid partial campaign publication.
- NL: Extended BRP coverage to 2009-2026 and moved to the newer PDOK source.
- PT: Updated for the 2025 edition and its schema/unit changes.
- SE: Editions now cover 2015-2025 from the yearly WFS filter.
- SI: Extended editions back to 2019.
- US-CSB: Editions now cover 2017-2024.

### Fixed
- Added HCAT spelling fixes via `csv_supplements` for DE-BB, DE-NDS and EC-SI.
- Declared the `beautifulsoup4` dependency used by ES-PV and ES-VC.
- Dropped cached error pages for REST converters.
- Fixed `use_variant_as_determination` so determination dates are retained.
- Multipart geometries now get recomputed area/perimeter for split parts.
- Rows missing `crop:code` are now dropped with a warning (and an error threshold), instead of failing whole conversions.
- CH:
  - CH now uses geodienste.ch STAC canton downloads.
  - `lnf_code` is now published as `crop:code`.
  - IDs are now derived from stable source identifiers instead of row order.
- DE-BB:
  - Excluded NBF ineligible patches with empty crop code.
  - Fixed source encoding and FLIK handling.
- DE-NDS: Added stable collection IDs where missing.
- DE-SAX: Updated to current available archive campaign.
- DE-SL:
  - Fixed parser issues with scientific notation in area values.
  - Restored full paging coverage and area derivation for complete output.
- EC-EE: Fixed shapefile naming and year-column migration.
- EC-FR: Added the missing 2018 RPG campaign from EuroCrops.
- EC-LT: Fixed Lithuanian crop-name decoding and parcel identifier handling.
- EC-LV: Relaxed requirements to match fields present in source data.
- EC-SI: Relaxed requirements to match fields present in source data.
- EE: Published valid crop code, land-use class and stable parcel identifier; cache files are now campaign-specific.
- ES:
  - ES-AN now uses the correct land-use column and campaign-based determination date.
  - ES-CAT and ES-CN now map crop codes to HCAT with the extended mapping table.
  - ES-CB now derives determination date from the campaign.
  - ES-CL now reads the HTTPS source and 2025 province subfolders.
  - ES-CM now uses the campaign-specific SIGPAC service and schema.
  - ES-CN now keeps distinct island records and correct region metadata.
  - ES-EX and ES-NC now read FEGA national recinto releases (2025, 2026) because the regional portals are unavailable.
  - ES-MD now finds `RECINTO.shp` regardless of archive folder layout.
- Europe-LAND: Empty source crop codes now fall back to crop names (for example LT 2024).
- IE: Uses stable feature IDs and publishes computed `metrics:area` when missing from source.
- JP: Uses campaign-specific determination dates and DuckDB conversion path.
- LT: Updated to Europe-LAND v1.3 with 2025 coverage.
- SK: Fixed edition selection, crop-name matching and block/id handling across campaigns.

## [v0.21.0] - 2026-02-16

- Update vecorel-cli
- Make the library better usable as a Python library
- Add support for Python 3.14, remove support for Python 3.10
- Support HCAT mapping CSV files without crop_code
- Split Germany BB and NDS in block dataset and crop fields
- Fix the column additions of the determination fields in the AI4SF converter
- Add HCAT to datasets where possible
- Updated years & variants for at_crop, be_vlg, es_an, es_cl, es_pv, ie, pt, se
- Extend create_stac, include include fiboa data
- Publish command; skip hidden files, generate better texts
- Fix to vecorel: converter.license and provider should be string
- Added a Dockerfile to simplify working with fiboa
- Command `fiboa publish` to automate source coop publication process
  - Run the converter to get the parquet file
  - Validate parquet file
  - Check for README.md, if missing generates one based on data-survey (if available) and converter
  - Check for LICENSE.txt, if missing generate one based on the converter file
  - Generate pmtiles file
  - Check AWS-environment vars
  - Synchronize parquet + pmtiles + README/LICENSE to source coop repo
- Check for license validity, either SPDX string or custom with url
- Seperate concerns for HCAT utility classes:
  - AddHCATMixin assures hcat-extension validity and csv-based data-conversion if required
  - EuroCropsConverterMixin is a BaseClass for EuroCrops-provided datasets
  - EuroLandBaseConverter is a BaseClass for Euroland-provided datasets
- Avoid base property schema override
- Add Converter for Bulgaria
- Remove unintended CommonMark formatting (indentation) from descriptions in converters
- Fibo improve command:
  - Upgrades from fiboa-0.2 if required
  - Adds HCAT if specified
- Various minor bug fixes

## [v0.20.3] - 2025-09-13

- Update vecorel-cli to solve issues with resolving schemas

## [v0.20.2] - 2025-08-29

- Reimplementation tests and CI
- Update extensions namespace to fiboa.org, use vecorel schemas
- Calibrate ha and m2 calculation in converters
- Adapt `create-stac-collection` to fiboa

## [v0.20.1] - 2025-08-27

- Reimplementation some modules (e.g. converters)
- Upgrade vecorel-cli dependency

## [v0.20.0] - 2025-08-25

- Reimplementation based on vecorel-cli
- Upgrade to support fiboa >= 0.3
- Removed support for fiboa < 0.3

## [v0.11.0] - 2025-08-25

### Added

- Converter for JECAM datasets
- Converter for Romania, based on LandCover dataset
- Converter for Brasil CONAB fields collection
- Converter for India 10k dataset

### Changed

- Improve Converter template.py usability
- Check proper 2-letter country-id for admin-extension
- Replace BaseConverter.source_variants by years

### Removed

- Remove functionality for function based converters

## [v0.10.0] - 2025-03-11

### Added

- Converter for Austrian crop fields
- Converters for Spain: Aragon, Andalusia, Balearic Islands, Basque Country, Catalonia, Cantabria, Castilla y León, Castilla-La Mancha, Canary Islands, Extremadura, Galicia, Madrid, Navarra, Valencia
- Use ruff format + linting for a uniform code style

### Changed

- Refactored converters to use a class-based approach
- Start to use `https://fiboa.org/code/` prefixed codes for our own code lists
- Use only unix line-endings in source files
- Use set instead of list for Converter.extensions
- Converted datasets are hilbert-curve sorted

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

[Unreleased]: <https://github.com/fiboa/cli/compare/v0.21.0...main>
[v0.21.0]: <https://github.com/fiboa/cli/compare/v0.20.3...v0.21.0>
[v0.20.3]: <https://github.com/fiboa/cli/compare/v0.20.2...v0.20.3>
[v0.20.2]: <https://github.com/fiboa/cli/compare/v0.20.1...v0.20.2>
[v0.20.1]: <https://github.com/fiboa/cli/compare/v0.20.0...v0.20.1>
[v0.20.0]: <https://github.com/fiboa/cli/compare/v0.11.0...v0.20.0>
[v0.11.0]: <https://github.com/fiboa/cli/compare/v0.10.0...v0.11.0>
[v0.10.0]: <https://github.com/fiboa/cli/compare/v0.9.0...v0.10.0>
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
