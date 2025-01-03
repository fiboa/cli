from .es import ESBaseConverter


class ESCLConverter(ESBaseConverter):
    sources = {
        "https://idem.comunidad.madrid/recursos_cat_geo/Catalogo/recursos/UsoDelSuelo/spacm_sigpac.cm.zip": ["2024_SIGPAC_shape_toda_la_com/RECINTO.shp"]
    }
    id = "es_md"
    short_name = "Spain Comunidad de Madrid"
    title = "Spain Madrid Crop fields"
    description = """
    SIGPAC is the Agricultural Parcel Identification System implemented throughout the European Union for the application of CAP (Common Agricultural Policy) aid to farmers and ranchers.
    """
    providers = [
        {
            "name": "Comunidad de Madrid",
            "url": "https://www.comunidad.madrid/",
            "roles": ["producer", "licensor"]
        }
    ]
    license = "CC-0"  # No-limits

    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "determination_datetime": "determination_datetime",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "DN_SURFACE": "area",
    }
    use_code_attribute = "USO_SIGPAC"
    column_additions = ESBaseConverter.column_additions | {
        "determination_datetime": "2024-01-01T00:00:00Z"
    }
    column_migrations = {
        'DN_SURFACE': lambda column: column / 10000
    }
