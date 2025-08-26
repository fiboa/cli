from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = {"https://data.geobasis-bb.de/geofachdaten/Landwirtschaft/dfbk.zip": ["DFBK_FB.shp"]}
    id = "de_bb"
    admin_subdivision_code = "BB"  # TODO Berlin is also in here, check each row
    short_name = "Germany, Berlin/Brandenburg"
    title = "Field boundaries for Berlin / Brandenburg, Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    license = "dl-de/by-2-0"
    providers = [
        {
            "name": "Land Brandenburg",
            "url": "https://geobroker.geobasis-bb.de/gbss.php?MODE=GetProductInformation&PRODUCTID=9e95f21f-4ecf-4682-9a44-e5f7609f6fa0",
            "roles": ["producer", "licensor"],
        }
    ]
    extensions = {"https://fiboa.github.io/flik-extension/v0.2.0/schema.yaml"}

    columns = {
        "geometry": "geometry",
        "FB_ID": ["flik", "id"],
        "FGUE_JAHR": "fgue_jahr",
        "FL_BRUTTO_": "metrics:area",
        "FL_NETTO_H": "net_area",
        "GUELTVON_F": "determination:datetime",
        "GUELTBIS_F": "expiry_datetime",
        "KREIS_NR": "kreis_nr",
        "TK10_BLATT": "tk10",
        "HBN_KAT": "hbn",
        "SHAPE_LEN": "metrics:perimeter",
    }
    missing_schemas = {
        "properties": {
            "hbn": {"type": "string"},
            "fgue_jahr": {"type": "string"},
            "net_area": {"type": "float", "exclusiveMinimum": 0},
            "expiry_datetime": {"type": "date-time"},
            "kreis_nr": {"type": "uint16"},
            "tk10": {"type": "string"},
        }
    }

    def layer_filter(self, layer: str, uri: str) -> bool:
        return layer == "DFBK_FB"
