# fiboa CLI

A command-line interface (CLI) for working with fiboa files.

- [Getting Started](#getting-started)
- [Documentation / Commands](#commands)
- [Development](#development)

## Getting Started

In order to make working with fiboa easier we have developed command-line interface (CLI) tools such as
inspection, validation and file format conversions.

### Installation

#### Using Pixi (Recommended)

This project uses [Pixi](https://pixi.sh/) for dependency management. Install Pixi first, then:

```bash
# Clone the repository and navigate to it
git clone https://github.com/vecorel/cli.git
cd cli

# Install all dependencies
pixi install

# Run the CLI
pixi run fiboa
```

#### Using pip

Alternatively, you can install from PyPI with **Python 3.10** or any later version:

```bash
pip install fiboa-cli
```

### Execute a command

After the installation you should be able to run the following command: `fiboa` (or `pixi run fiboa` if using Pixi)

You should see usage instructions and [available commands](#commands) for the CLI.

fiboa CLI supports various commands to work with the files:

- [fiboa CLI](#fiboa-cli)
  - [Getting Started](#getting-started)
    - [Installation](#installation)
      - [Using Pixi (Recommended)](#using-pixi-recommended)
      - [Using pip](#using-pip)
    - [Execute a command](#execute-a-command)
  - [Commands](#commands)
    - [Validation](#validation)
    - [Create fiboa GeoParquet from GeoJSON](#create-fiboa-geoparquet-from-geojson)
    - [Create fiboa GeoJSON from GeoParquet](#create-fiboa-geojson-from-geoparquet)
    - [Inspect fiboa GeoParquet file](#inspect-fiboa-geoparquet-file)
    - [Merge fiboa GeoParquet files](#merge-fiboa-geoparquet-files)
    - [Create JSON Schema from fiboa Schema](#create-json-schema-from-fiboa-schema)
    - [Validate a Vecorel Schema](#validate-a-vecorel-schema)
    - [Improve a fiboa Parquet file](#improve-a-fiboa-parquet-file)
    - [Update an extension template with new names](#update-an-extension-template-with-new-names)
    - [Converter for existing datasets](#converter-for-existing-datasets)
  - [Development](#development)
    - [Implement a converter](#implement-a-converter)

## Commands

### Validation

To validate a Vecorel GeoParquet or GeoJSON file, you can for example run:

- GeoJSON: `fiboa validate example.json --collection collection.json`
- GeoParquet: `fiboa validate example.parquet --data`

Check `fiboa validate --help` for more details.

The validator also supports remote files.

- `http://` or `https://`: no further configuration is needed.
- `s3://`: With Pixi, run `pixi install -e s3` or with pip, run `pip install fiboa-cli[s3]` and you may need to set environment variables.
  Refer to the [s3fs credentials documentation](https://s3fs.readthedocs.io/en/latest/#credentials) for how to define credentials.
- `gs://`: With Pixi, run `pixi install -e gcs` or with pip, run `pip install fiboa-cli[gcs]`.
  By default, `gcsfs` will attempt to use your default gcloud credentials or, attempt to get credentials from the google metadata service, or fall back to anonymous access.

### Create fiboa GeoParquet from GeoJSON

To create a fiboa-compliant GeoParquet for a fiboa-compliant set of GeoJSON files containing Features or FeatureCollections,
you can for example run:

- `fiboa create-geoparquet geojson/example.json -o example.parquet -c geojson/collection.json`

Check `fiboa create-geoparquet --help` for more details.

### Create fiboa GeoJSON from GeoParquet

To create one or multiple fiboa-compliant GeoJSON file(s) for a fiboa-compliant GeoParquet file,
you can for example run:

- GeoJSON FeatureCollection:
  `fiboa create-geojson example.parquet -o dest-folder`
- GeoJSON Features (with indentation and max. 100 features):
  `fiboa create-geojson example.parquet -o dest-folder -n 100 -i 2 -f`

  `fiboa create-geojson example.parquet -o dest-folder -n 100 -i 2 -f`

Check `fiboa create-geojson --help` for more details.

### Inspect fiboa GeoParquet file

To look into a fiboa GeoParquet file to get a rough understanding of the content, the following can be executed:

- `fiboa describe example.parquet`

Check `fiboa describe --help` for more details.

### Merge fiboa GeoParquet files

Merges multiple fiboa datasets to a combined fiboa dataset:

- `fiboa merge ec_ee.parquet ec_lv.parquet -o merged.parquet -e https://fiboa.org/hcat-extension/v0.1.0/schema.yaml -i ec:hcat_name -i ec:hcat_code -i ec:translated_name`

Check `fiboa merge --help` for more details.

### Create JSON Schema from fiboa Schema

To create a JSON Schema for a fiboa Schema YAML file, you can for example run:

- `fiboa jsonschema example.json --id=https://vecorel.org/specification/v0.3.0/geojson/schema.json -o schema.json`

Check `fiboa jsonschema --help` for more details.

### Validate a Vecorel Schema

To validate a Vecorel Schema YAML file, you can for example run:

- `fiboa validate-schema schema/schema.yaml`

Check `fiboa validate-schema --help` for more details.

### Improve a fiboa Parquet file

Various "improvements" can be applied to a fiboa GeoParquet file.
The commands allows to

- change the CRS (`--crs`)
- change the GeoParquet version (`-gp1`) and compression (`-pc`)
- add/fill missing perimeter/area values (`-sz`)
- fix invalid geometries (`-g`)
- rename columns (`-r`)

Example:

- `fiboa improve file.parquet -o file2.parquet -g -sz -r old=new -pc zstd`

Check `fiboa improve --help` for more details.

### Update an extension template with new names

Once you've created and git cloned a new extension, you can use the CLI
to update all template placeholders with proper names.

For example, if your extension is meant to have

- the title "Administrative Division Extension",
- the prefix `admin` (e.g. field `admin:country_code` or `admin:subdivision_code`),
- is hosted at `https://github.io/vecorel/administrative-division-extension`
  (organization: `vecorel`, repository `/administrative-division-extension`),
- and you run Vecorel in the folder of the extension.

Then the following command could be used:

- `fiboa rename-extension . -t "Administrative Division" -p admin -s administrative-division-extension -o vecorel`

Check `fiboa rename-extension --help` for more details.

### Converter for existing datasets

The CLI ships various converters for existing datasets.

To get a list of available converters/datasets with title, license, etc. run:

- `fiboa converters`

Use any of the IDs from the list to convert an existing dataset to fiboa:

- `fiboa convert de_nrw`

See [Implement a converter](#implement-a-converter) for details about how to

## Development

This project uses [Pixi](https://pixi.sh/) for dependency management and development workflows.

```bash
# Install all dependencies including development tools
pixi install -e dev

# Install the package in editable mode
pixi run install-dev

# Run tests
pixi run test

# Format and lint code
pixi run format
pixi run lint

# Run all checks (lint, format, test)
pixi run check

# Install and run pre-commit
pixi run pre-commit-install
pixi run pre-commit-run
```

### Implement a converter

The following high-level description gives an idea how to implement a converter in fiboa CLI:

1. Create a new file in `fiboa_cli/datasets` based on the `template.py`
2. Fill in the required variables / test it / run it
3. Add missing dependencies into the appropriate feature group in `pixi.toml` (or `setup.py` for pip users)
4. Add the converter to the list above
5. Create a PR to submit your converter for review
