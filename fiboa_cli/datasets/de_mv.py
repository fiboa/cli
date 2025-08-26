from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = {
        "https://www.geodaten-mv.de/dienste/gdimv_feldblock_wfs?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=mv:feldbloecke&OUTPUTFORMAT=shape-zip": "gdimv_feldblock_wfs.zip"
    }
    id = "de_mv"
    admin_subdivision_code = "MV"
    short_name = "Germany, Mecklenburg-Western Pomerania"
    title = "Field boundaries for Mecklenburg-Western Pomerania, Germany"
    description = "Field block register of the Ministry of Agriculture and Environment M-V"

    providers = [
        {
            "name": "Ministerium für Landwirtschaft und Umwelt M-V",
            "url": "https://www.geodaten-mv.de/dienste/feldblock_atom?type=dataset&id=f18122c4-2585-4c22-9c48-9e960e8dhd34",
            "roles": ["producer", "licensor"],
        }
    ]
    license = {
        "title": "No restrictions apply",
        "href": "https://www.geodaten-mv.de/dienste/feldblock_atom?type=dataset&id=f18122c4-2585-4c22-9c48-9e960e8dhd34",
        "type": "text/html",
        "rel": "license",
    }
    extensions = {"https://fiboa.github.io/flik-extension/v0.2.0/schema.yaml"}

    columns = {
        "geometry": "geometry",
        "fbid": ["id", "flik"],  # make flik id a dedicated column to align with NRW etc.
        "dgl_jahr": "dgl_jahr",
        # TODO implement crop:code extension
        "bodennutzu": "bodennutzu",  # Bodennutzungsart
        "bez_kreis": "bez_kreis",  # Kreisbezeichnung
        "groesse_p": "metrics:area",  # Produktive Fläche des FB in Hektar (Nettofläche)
        "perimeter": "metrics:perimeter",  # Polygonumfang
        "erwind": "erwind",  # Gefährdungsklasse des Feldblockes gegenüber Winderosion nach DIN 19708
        "erwater": "erwater",  # Gefährdungsklasse des Feldblockes gegenüber Wassererosion nach DIN 19708
        "erwind_l": "erwind_l",
        "erwater_l": "erwater_l",
    }
    iso_schema = {
        "type": "string",
        "enum": [
            "Enat0",  # keine bis sehr geringe Erosionsgefährdung
            "Enat0-EE",
            "Enat1",  # sehr geringe Erosionsgefährdung
            "Enat1-EE",
            "Enat2",  # geringe Erosionsgefährdung
            "Enat2-EE",
            "Enat3",  # mittlere Erosionsgefährdung
            "Enat3-EE",
            "Enat4",  # hohe Erosionsgefährdung
            "Enat4-EE",
            "Enat5",  # sehr hohe Erosionsgefährdung
            "Enat5-EE",
            "-",  # Keine Angabe
        ],
    }
    missing_schemas = {
        "properties": {
            "dgl_jahr": {"type": "int16"},
            "bodennutzu": {
                "type": "string",
                "enum": [
                    "AAF",  # Aufforstung auf Ackerfläche
                    "AF",  # Ackerfläche
                    "AGL",  # Aufforstung auf Grünland
                    "AÖD",  # Aufforstung auf Ödland
                    "DK",  # Dauerkultur
                    "FO",  # Forst
                    "GL",  # Grünland
                ],
            },
            "bez_kreis": {"type": "string"},
            "erwind": {
                "type": "string",
                "enum": [
                    "CC0",  # nicht relevant für Cross Compliance
                    "CC1",  # Erosionsgefährdung nach Direktzahlungen-Verpflichtungenverordnung
                    "-",  # keine Angabe
                ],
            },
            "erwater": {
                "type": "string",
                "enum": [
                    "CC0",  # nicht relevant für Cross Compliance
                    "CC1",  # Erosionsgefährdung nach Direktzahlungen-Verpflichtungenverordnung (15-27,5 t/ha/a Bodenabtrag durch Wasser)
                    "CC2",  # hohe Erosionsgefährdung nach Direktzahlungen-Verpflichtungenverordnung (>27,5 t/ha/a Bodenabtrag durch Wasser)
                    "-",  # keine Angabe
                ],
            },
            "erwind_l": iso_schema,
            "erwater_l": iso_schema,
        }
    }
