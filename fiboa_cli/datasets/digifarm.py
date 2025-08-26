# Digifarm converter for fiboa
# First draft just takes in a file saved from the API.
# It'd be ideal if there was a CLI that took a Digifarm token and BBOX and would save the file locally and
# convert it. Not sure if we want to keep loading functionality into the converter, if we have a new
# CLI tool that could query field boundary API's - I'd see DigiFarm and Onesoil as options, where you could
# do like 'fiboa api-request digifarm --bbox 4,12,5,13 --token blah | fiboa convert digifarm -i -'.

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(FiboaBaseConverter):
    sources = None
    data_access = """
    Data must be obtained from the Digifarm API, see https://api-docs.digifarm.io/.
    Use the `-i` CLI parameter to provide the data source.
    Provide a URL to an API request (e.g. `https://api.digifarm.io/v1/delineated-fields?token=...&bbox=11.13,60.72,11.21,60.76`)
    or download the API response to a local GeoJSON file (use `.json` as file extension).
    """
    id = "digifarm"
    short_name = "DigiFarm"
    title = "Field boundaries created by DigiFarm Automatic Field Delineation Model"
    description = """These field boundaries are created by DigiFarm using a state-of-the-art deep neural network model for Field Delineation
    from super-resolved satellite imagery. The results are available through an API, covering over 200 million hectares across 30+ countries.
    The data is provided through the DigiFarm API at https://api-docs.digifarm.io/, as GeoJSON. For more information see https://digifarm.io/products/field-boundaries
    """
    providers = [
        {"name": "DigiFarm", "url": "https://digifarm.io", "roles": ["producer", "licensor"]}
    ]
    attribution = "© 2024 digifarm.io"
    license = {
        "title": "DigiFarm Terms and Conditions",
        "href": "https://digifarm.io/legal/tc",
        "type": "text/html",
        "rel": "license",
    }
    columns = {"id": "id", "geometry": "geometry", "area": "metrics:area"}
    column_migrations = {"area": lambda column: column / 10000}
    column_additions = {"determination_method": "auto-imagery"}
