import re

from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin


def parse_flik(x):
    match = re.search(r"flik:\s*([A-Z]{6}\d{10})", x, re.I)
    return match.group(1) if match else None


def parse_size(x):
    match = re.search(r"Size in ha: (\d+(\.\d+)?)+", x, re.I)
    return float(match.group(1)) if match else None


url = "https://geoportal.saarland.de/gdi-sl/inspirewfs_Existierende_Bodennutzung_Antragsschlaege?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&typeNames=elu:ExistingLandUseObject&outputFormat=application/gml%2Bxml;%20version=3.2&EPSG=4258&BBOX={bbox}"
bboxes = [
    [49.1, 6.5423790007724, 49.332379000772, 6.7747580015449],
    [49.1, 6.7747580015449, 49.332379000772, 7.0071370023173],
    [49.1, 7.0071370023173, 49.216189500386, 7.2395160030898],
    [49.216189500386, 7.0071370023173, 49.332379000772, 7.2395160030898],
    [49.1, 7.2395160030898, 49.332379000772, 7.4718950038622],
    [49.332379000772, 6.31, 49.564758001545, 6.5423790007724],
    # Add more bboxes if needed
]


class Converter(AdminConverterMixin, BaseConverter):
    sources = {
        url.format(bbox=",".join(map(str, bbox))): f"{i}.gml"
        for i, bbox in enumerate(bboxes, start=1)
    }

    id = "de_sl"
    admin_subdivision_code = "SL"
    short_name = "Germany, Saarland"
    title = "Field boundaries for Saarland, Germany"
    description = """This dataset contains data transformed into the INSPIRE data model “Land Use” of the IACS areas applied for within the framework of agricultural land promotion (GIS application) from the Saarland."""
    providers = [
        {
            "name": "Ministerium für Umwelt, Klima, Mobilität, Agrar und Verbraucherschutz",
            "url": "https://geoportal.saarland.de",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "©GDI-SL 2024"
    license = "cc-by-4.0"
    extensions = {"https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"}
    columns = {
        "geometry": "geometry",
        "identifier": "id",
        "flik": "flik",
        "area": "area",
        "name": "name",
    }
    missing_schemas = {"properties": {"name": {"type": "string"}}}

    def migrate(self, gdf):
        gdf["flik"] = gdf["description"].apply(parse_flik)
        gdf["area"] = gdf["description"].apply(parse_size)
        return gdf
