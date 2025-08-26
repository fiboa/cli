import pandas as pd

from .es import ESBaseConverter


class ARConverter(ESBaseConverter):
    # https://idearagon.aragon.es/descargas
    # These files can be annoying to download (web server failure, no http-range support for continuation)
    # Alternative is to download the files by municipality, check the atom.xml
    sources = {
        "https://icearagon.aragon.es/datosdescarga/descarga.php?file=/CartoTema/sigpac/rec22_sigpac.shp.zip&blocksize=0": "rec22_sigpac.shp.zip",
        "https://icearagon.aragon.es/datosdescarga/descarga.php?file=/CartoTema/sigpac/rec44_sigpac.shp.zip&blocksize=0": "rec44_sigpac.shp.zip",
        "https://icearagon.aragon.es/datosdescarga/descarga.php?file=/CartoTema/sigpac/rec50_sigpac.shp.zip&blocksize=0": "rec50_sigpac.shp.zip",
    }

    id = "es_ar"
    short_name = "Spain Aragon"
    title = "Spain Aragon Crop fields"
    description = """
    SIGPAC - Sistema de Información Geográfica de la Política Agrícola común (ejercicio actual)

    Crop Fields of Spain province Aragon
    """
    providers = [
        {
            "name": "Gobierno de Aragon",
            "url": "https://www.aragon.es/",
            "roles": ["producer", "licensor"],
        }
    ]

    # License: https://idearagon.aragon.es/portal/politica-privacidad.jsp
    license = "CC-BY-4.0"
    attribution = "(c) Gobierno de Aragon"
    columns = {
        "geometry": "geometry",
        "dn_oid": "id",
        "provincia": "admin_province_code",
        "municipio": "admin_municipality_code",
        "uso_sigpac": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "ejercicio": "determination:datetime",
    }

    column_migrations = {
        "ejercicio": lambda col: pd.to_datetime(col, format="%Y"),
    }

    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
