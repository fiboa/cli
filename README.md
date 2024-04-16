# fiboa CLI

In order to make working with fiboa easier we have developed command-line interface (CLI) tools such as validation and file format conversion. To get started with the fiboa CLI please follow the instructions below:

## Installation

You will need **Python 3.9+** installed. 
Run `pip install fiboa-cli` to install the validator.

To install additional dependencies for specific [converters](#converter-for-existing-datasets),
you can for example run: `pip install fiboa-cli[xyz]` with xyz being the converter name.

## fiboa versions

- fiboa CLI >= 0.3.0 works with fiboa version > 0.2.0
- fiboa CLI < 0.3.0 works with fiboa version = 0.1.0

## Validation

To validate a fiboa GeoParquet or GeoJSON file, you can for example run:

- GeoJSON: `fiboa validate example.json --collection collection.json`
- GeoParquet: `fiboa validate example.parquet --data`

Check `fiboa validate --help` for more details.

The validator also supports remote files.

- `http://` or `https://`: no further configuration is needed.
- `s3://`: `s3fs` needs to be installed (run `pip install .[s3]`) and you may need to set environment variables.
  Refer [here](https://s3fs.readthedocs.io/en/latest/#credentials) for how to define credentials.
- `gs://`: `gcsfs` needs to be installed (run `pip install .[gcs]`).
  By default, `gcsfs` will attempt to use your default gcloud credentials or, attempt to get credentials from the google metadata service, or fall back to anonymous access.

## Create fiboa GeoParquet from GeoJSON

To create a fiboa-compliant GeoParquet for a fiboa-compliant set of GeoJSON files containing Features or FeatureCollections,
you can for example run:

- `fiboa create-geoparquet geojson/example.json -o example.parquet -c geojson/collection.json`

Check `fiboa create-geoparquet --help` for more details.

## Create fiboa GeoJSON from GeoParquet

To create one or multiple fiboa-compliant GeoJSON file(s) for a fiboa-compliant GeoParquet file,
you can for example run:

- GeoJSON FeatureCollection:
  `fiboa create-geojson example.parquet -o dest-folder`
- GeoJSON Features (with indentation and max. 100 features):
  `fiboa create-geojson example.parquet -o dest-folder -n 100 -i 2 -f`

Check `fiboa create-geoparquet --help` for more details.

## Inspect fiboa GeoParquet file

To look into a fiboa GeoParquet file to get a rough understanding of the content, the following can be executed:

- `fiboa describe example.parquet`

Check `fiboa describe --help` for more details.

## Create JSON Schema from fiboa Schema

To create a JSON Schema for a fiboa Schema YAML file, you can for example run:

- `fiboa jsonschema example.json --id=https://fiboa.github.io/specification/v0.1.0/geojson/schema.json -o schema.json`

Check `fiboa jsonschema --help` for more details.

## Validate a fiboa Schema

To validate a fiboa Schema YAML file, you can for example run:

- `fiboa validate-schema schema/schema.yaml`

Check `fiboa validate-schema --help` for more details.

## Update an extension template with new names

Once you've created and git cloned a new extension, you can use the CLI
to update all template placeholders with proper names.

For example, if your extension is meant to have
- the title "Timestamps Extension", 
- the prefix `ts` (e.g. field `ts:created` or `ts:updated`),
- is hosted at `https://github.io/fiboa/timestamps-extension`
  (organization: `fiboa`, repository `timestamps-extension`),
- and you run fiboa in the folder of the extension.

Then the following command could be used:
- `fiboa rename-extension . -t Timestamps -p ts -s timestamps-extension -o fiboa`

Check `fiboa rename-extension --help` for more details.

## Converter for existing datasets

To convert an existing dataset to fiboa using the pre-defined converters:

- `fiboa convert de_nrw`

Available converters:
- `at` (Austria)
- `de_bb` (Berlin/Brandenburh, Germany)
- `de_nds` (Lowe Saxony, Germany)
- `de_nrw` (North Rhine-Westphalia, Germany)
- `de_sh` (Schleswig-Holstein, Germany)

### Implement a converter

1. Create a new file in `fiboa_cli/datasets` based on the `template.py`
2. Implement the `convert()` function
3. Add missing dependencies into a separate dependency group in `setup.py`
4. Add the converter to the list above
5. Create a PR to submit your converter for review

## Development

To install in development mode run `pip install -e .` in this folder.

For the tests first run `pip install -r requirements-dev.txt` to install pytest.
Then you can run `pytest` to execute the tests.
