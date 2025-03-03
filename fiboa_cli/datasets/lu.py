from .commons.admin import AdminConverterMixin
from ..convert_utils import BaseConverter


class Converter(AdminConverterMixin, BaseConverter):
    sources = {
        "https://data.public.lu/fr/datasets/r/b4ae6690-7e4c-4454-8b60-9fa33ba6a61b": "lu.zip"
    }
    id = "lu"
    short_name = "Luxembourg"
    title = "Luxembourg FLIK Parcels"
    description = """
    The Land Parcel Identification System (LPIS) is a reference database of the agriculture parcels used as a basis for area-related payments to farmers in relation to the Common Agricultural Policy (CAP). These payments are (co)financed by the European Agricultural Guarantee Fund (‘EAGF’) and the European Agricultural Fund for Rural Development (‘EAFRD’).

    To ensure that payments are regular, the CAP relies on the Integrated Administration and Control System (IACS), a set of comprehensive administrative and on-the-spot checks on subsidy applications, which is managed by the Member States. The Land Parcel Identification System (LPIS) is a key component of the IACS. It is an IT system based on ortho imagery (aerial or satellite photographs) which records all agricultural parcels in the Member States.
    """
    providers = [
        {
            "name": "Luxembourg ministry of Agriculture",
            "url": "https://agriculture.public.lu/",
            "roles": ["licensor", "producer"]
        }
    ]
    attribution = "Luxembourg ministry of Agriculture"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        'FLIK': 'id',
        "determination_datetime": "determination_datetime",
    }
