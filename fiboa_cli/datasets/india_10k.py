from vecorel_cli.conversion.admin import AdminConverterMixin

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

RECORD = "https://zenodo.org/api/records/7315090/files"


class IndiaConverter(AdminConverterMixin, FiboaBaseConverter):
    area_is_in_ha = False
    # The record's files one by one: its files-archive also bundles the 256 MB model weights
    sources = {
        f"{RECORD}/india_10k_fields.{ext}/content": f"india_10k_fields.{ext}"
        for ext in ("shp", "shx", "dbf", "prj", "cpg")
    }
    id = "in_10k"
    short_name = "India 10k"
    title = "10,000 Crop Field Boundaries across India"
    description = """
Release of dataset and neural network weights accompanying the paper
"Unlocking large-scale crop field delineation in smallholder farming systems with transfer learning and weak supervision"
(forthcoming in Remote Sensing). Ten thousand crop fields in India were delineated manually through inspection
of high-resolution satellite imagery (Airbus SPOT). We also provide the weights of the highest performing
neural network (FracTAL ResUNet architecture) pre-trained in France and fine-tuned on Airbus SPOT images in India.
The model was trained in MXNet 1.6.0 and can be loaded with the "model.load_parameters()" function.
    """
    provider = "Zenodo <https://zenodo.org>"
    attribution = "https://doi.org/10.5281/zenodo.7315090"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "area": "metrics:area",
    }
    # "India in October 2020": the month of the Airbus SPOT images the fields were drawn on
    # (Wang, Waldner & Lobell 2022, https://doi.org/10.3390/rs14225738); 2022-11-12 is the
    # date of the Zenodo release
    column_additions = {"determination:datetime": "2020-10-01T00:00:00Z"}
