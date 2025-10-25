from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class PTConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    id = "pt"
    title = "Field boundaries for Portugal"
    short_name = "Portugal"
    description = "Open field boundaries (identificação de parcelas) from Portugal"
    # see https://www.ifap.pt/isip/ows/
    BASE = "https://www.ifap.pt/isip/ows/resources/"
    variants = {
        "2023": BASE + "2023/Continente.gpkg",
        "2022": BASE + "2022/2022.zip",
        "2021": BASE + "2021/2021.zip",
        "2020": BASE + "2017-2020/2020.zip",
        "2019": BASE + "2017-2020/2019.zip",
        "2018": BASE + "2017-2020/2018.zip",
        "2017": BASE + "2017-2020/2017.zip",
        "2016": BASE + "2011_2016/2016.zip",
        "2015": BASE + "2011_2016/2015.zip",
        # ...
    }

    def layer_filter(self, layer, uri):
        return layer.startswith("Culturas_")

    provider = (
        "IPAP - Instituto de Financiamento da Agricultura e Pescas <https://www.ifap.pt/isip/ows/>"
    )
    license = "No conditions apply <https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply>"
    columns = {
        "geometry": "geometry",
        "OSA_ID": "id",
        "CUL_ID": "block_id",
        "CUL_CODIGO": "crop:code",
        "CT_português": "crop:name",
        "Shape_Area": "metrics:area",
        "Shape_Length": "metrics:perimeter",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    ec_mapping_csv = "pt_2021.csv"
    column_additions = {
        "determination:datetime": "2023-01-01T00:00:00Z",
    }
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "block_id": {"type": "int64"},
        }
    }
