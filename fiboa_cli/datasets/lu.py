from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = {
    "https://data.public.lu/fr/datasets/r/b4ae6690-7e4c-4454-8b60-9fa33ba6a61b": "lu.zip"
}

ID = "lu"
SHORT_NAME = "Luxembourg"
TITLE = "Luxembourg FLIK Parcels"
DESCRIPTION = """
The Land Parcel Identification System (LPIS) is a reference database of the agriculture parcels used as a basis for area related payments to farmers in relation to the Common Agricultural Policy (CAP). These payments are (co)financed by the European Agricultural Guarantee Fund (‘EAGF’) and the European Agricultural Fund for Rural Development (‘EAFRD’).
To ensure that payments are regular, the CAP relies on the Integrated Administration and Control System (IACS), a set of comprehensive administrative and on the spot checks on subsidy applications, which is managed by the Member States. The Land Parcel Identification System (LPIS) is a key component of the IACS. It is an IT system based on ortho imagery (aerial or satellite photographs) which records all agricultural parcels in the Member States. It serves two main purposes: to clearly locate all eligible agricultural land contained within reference parcels and to calculate their maximum eligible area (MEA). The LPIS is used for cross checking during the administrative control procedures and as a basis for on the spot checks by the paying agency.
"""

PROVIDERS = [
    {
        "name": "Luxembourg ministry of Agriculture",
        "url": "https://agriculture.public.lu/",
        "roles": ["licensor", "producer"]
    }
]
ATTRIBUTION = "Luxembourg ministry of Agriculture"
LICENSE = "CC-BY-4.0"

COLUMNS = {
    "geometry": "geometry",
    'FLIK': 'id',
    "determination_datetime": "determination_datetime",
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "LU")


def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        providers=PROVIDERS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        **kwargs
    )
